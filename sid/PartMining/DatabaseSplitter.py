###############################################################################
# File: DatabaseSplitter.py
# Author: Carlos Bobed
# Date: JUl 2021
# Comments: Program to split a database based on different clusterings
#       built from their embeddings
# Modifications:
# Notes:
# * Dec 2020: using the overall probability of each item as weight to calculate the centroid
#   lead to decisions which partition the codes further (in the histograms I've observed that
#   the freq of lengths of the codes gets higher in the shorter regions)
#   maybe going for a soft clustering technique (considering fuzzy k-means - hdbscan was too expensive for
#   our purposes)
# * Jul 2021: some problems with fuzzy k-means implementations and hdbscan restrict
#       such options to the notebook
# * Dec 2021: added doc2vec method to cluster the transactions
##############################################################################

from gensim.models import Word2Vec
from gensim.models import Doc2Vec
import numpy as np
from sklearn import preprocessing
import TransactionDatabase as tdb
import math
import os
import time
import faiss
import hdbscan
import argparse
import random
import ntpath
import logging

## I was going to use scikit directly, but I saw this post
## kudos for him https://towardsdatascience.com/k-means-8x-faster-27x-lower-error-than-scikit-learns-in-25-lines-eaedc7a3a0c8
import faiss

## Vector manipulation
def calculate_centroids (model, labelled_transactions):
#     initial code
#     centroids = []
#     for transaction in transaction_list:
#         words = [model.wv[it] for it in transaction]
#         centroids.append(np.mean(words, axis=0))
#     return centroids
    # more pythonic way
    return { label: np.mean([model.wv[it] for it in  labelled_transactions[label]], axis=0) for label in labelled_transactions}

def calculate_transaction_representations (model, labelled_transactions):
    ## the id used in the doc2vec tagged documents is the same one as the one used when loading the transaactions
    ## in labelled transactions -> ordered line by line (( a small check is added if debug is true though just in case with the inference ))
    logging.debug(f'first vector in the model {model.dv[0]}')
    logging.debug(f'first inferred vector from the model {model.infer_vector(labelled_transactions[0])}')
    logging.debug(np.allclose(model.dv[0], model.infer_vector(labelled_transactions[0])))
    return {label: model.dv[label] for label in labelled_transactions}

def calculate_normalized_centroids(model, labelled_transactions):
    dim = model.wv[labelled_transactions[0][0]].shape[0]
    return { label: preprocessing.normalize(np.mean([model.wv[it] for it in labelled_transactions[label]], axis=0).reshape(1,dim), norm='l2').reshape(dim,)
                                            for label in labelled_transactions}

def calculate_weighted_centroids(model, labelled_transactions):
    # model.wv.vocab['1'].count
    # I was going to get the softmax derived weights but it would add some dependency that we don't want
    # to explore right now
    # for the time being, let's focus on the global probability of each item being part of a transaction

    #     total_sum = sum([model.wv.vocab[it].count for it in model.wv.vocab])
    #     e_values = {it: math.pow(math.e, model.wv.vocab[it].count / total_sum) for it in model.wv.vocab}
    #     total_e_values = sum([evalues[it] for it in e_values])
    #     weights = {it:e_values[it] / total_e_values for it in e_values}

    result = {}
    # old gensim 3.x code
    # weights = {it: model.wv.vocab[it].count / len(labelled_transactions) for it in model.wv.vocab}
    weights = {it: model.wv.get_vecattr(it, "count") / len(labelled_transactions) for it in model.wv.key_to_index}
    for label in labelled_transactions:
        item_vect = []
        weight_vect = []
        for it in labelled_transactions[label]:
            item_vect.append(model.wv.get_vector(it))
            weight_vect.append(weights[it])
        result[label] = np.average(item_vect, weights=np.array(weight_vect, dtype='float32'), axis=0)
    return result

## Clustering methods

def cluster_data(method, vectors, num_clusters, normalize):
    dim = vectors[0].shape[0]
    if normalize:
        actual_vectors = np.array([preprocessing.normalize(x.reshape(1,dim)).reshape(dim,) for x in vectors])
    else:
        actual_vectors = np.array([x for x in vectors])

    if method =='k_means':
        clusters = faiss.Kmeans(d=actual_vectors.shape[1], k=num_clusters, niter=2000, nredo=10)
        clusters.train(actual_vectors)
    elif method == 'hdbscan':
        clusters = hdbscan.HDBSCAN(min_cluster_size=10, prediction_data=True)
        clusters.fit(actual_vectors)

    return clusters

## Labelling methods - once we have the clusters, we have to label each transaction to the cluster it belongs
## we can have then 3 different partitions of the database:
## clustered according to the items k-means
## clustered according to the items obtained from the "flattened" transaction k-means
## clustered directly from the transaction k-means

## we build the clusters accordingly from the calculated k-means of their vectors
## done in this way for readability purposes, we can speed up this process by
## sharing orders
def item_labelling_from_item_vects(item_vects, item_clusters, dim, clustering_method):
    # labelled_vects = {int(x): model.wv[x] for x in model.wv.vocab}
    cluster = {}
    base_label_item = 'item_clust_'
    if clustering_method == 'k_means':
        for i in range(len(item_vects)):
            print(f'item_vects[i]: {item_vects[i].shape}')
            item_D, item_I = item_clusters.index.search(item_vects[i].reshape(1, dim), 1)
            current_label = base_label_item + str(item_I[0, 0])
            if current_label not in cluster:
                cluster[current_label] = set()
            cluster[current_label].add(i)
    elif clustering_method == 'hdbscan':
        # hdbscan object has a label_ field with directly the label of each of the elements
        # in item_vects :: it's the same order
        for i in range(len(item_vects)):
            current_label = base_label_item + str(item_clusters.labels_[i])
            if current_label not in cluster:
                cluster[current_label] = set()
            cluster[current_label].add(item_vects[i])
    return cluster

## we build the clusters accordingly from the items in the transactions belonging to a
## cluster
def item_labelling_from_trans_vects(database, trans_vects, trans_clusters, dim, clustering_method):
    # from read_database_*
    #     transactions[label] = list(words)
    #     label+=1

    cluster = {}
    base_label_trans_item = 'trans_item_clust_'
    if clustering_method == 'k_means':
        for t in trans_vects:
            trans_D, trans_I = trans_clusters.index.search(trans_vects[t].reshape(1, dim), 1)
            current_label = base_label_trans_item + str(trans_I[0, 0])
            if current_label not in cluster:
                cluster[current_label] = set()
            ## centroids/trans_vects share the same ids as database
            for item in database[t]:
                cluster[current_label].add(int(item))
    elif clustering_method == 'hdbscan':
        idx = 0
        for t in sorted(trans_vects):
            ## we force to iterate in the same order than trans_clusters.labels_
            ## and we asign the appropiate idx position label
            current_label = base_label_trans_item + str(trans_clusters.labels_[idx])
            if current_label not in cluster:
                cluster[current_label] = set()
                ## centroids/trans_vects share the same ids as database
            for item in database[t]:
                cluster[current_label].add(int(item))
            idx += 1
    return cluster

## finally, we build the clusters accordingly from the transaction vectors
def trans_labelling_from_trans_vects(database, trans_vects, trans_clusters, dim, clustering_method):
    cluster = {}
    base_label_trans_item = 'trans_clust_'
    if clustering_method == 'k_means':
        for t in trans_vects:
            trans_D, trans_I = trans_clusters.index.search(trans_vects[t].reshape(1, dim), 1)
            current_label = base_label_trans_item + str(trans_I[0, 0])
            if current_label not in cluster:
                cluster[current_label] = []
            ## centroids/trans_vects share the same ids as database
            cluster[current_label].append(database[t])
    elif clustering_method == 'hdbscan':
        idx = 0
        # we force the iteration to be in the same order as the trans_clusters.labels_
        for t in sorted(trans_vects):
            current_label = base_label_trans_item + str(trans_clusters.labels_[idx])
            if current_label not in cluster:
                cluster[current_label] = []
            ## centroids/trans_vects share the same ids as database
            cluster[current_label].append(database[t])
            idx += 1
    return cluster


# def trans_labelling_from_trans_vects_normalizing(database, trans_vects, trans_kmeans, dim):
#     cluster = {}
#     base_label_trans_item = 'trans_clust_'
#     for t in trans_vects:
#         trans_D, trans_I = trans_kmeans.index.search(preprocessing.normalize(trans_vects[t].reshape(1, dim)), 1)
#         current_label = base_label_trans_item + str(trans_I[0, 0])
#         if current_label not in cluster:
#             cluster[current_label] = []
#         ## centroids/trans_vects share the same ids as database
#         cluster[current_label].append(database[t])
#     return cluster

## We randomly split transaction database
def trans_labelling_random(database, k):
    cluster = {}
    ## beware: database is a dict, not a list
    idx_list = [i for i in range(len(database))]
    size = int(math.ceil(len(idx_list) / k))
    print(f'size of shuffle: {len(idx_list)}')
    print(f'Partitioning DB of {len(idx_list)} in {k} sets of {size} elements')
    base_label = 'rand_clust_'
    random.shuffle(idx_list)
    shuffled = [idx_list[i::k] for i in range(k)]
    print(f'size of shuffle: {len(shuffled)}')
    for (i, vect) in enumerate([idx_list[i::k] for i in range(k)]):
        current_label = base_label + str(i)
        if current_label not in cluster:
            cluster[current_label] = []
        for j in vect:
            cluster[current_label].append(database[j])
    for cl in enumerate(cluster):
        print(f'{cl[0]} - {cl[1]} -- len {len(cluster[cl[1]])}')
    return cluster

## Database manipulation
## convert a transaction in Vreken to the original item name
def convert_transaction_db_to_dat (transaction, table):
    return sorted([table[int(item)] for item in transaction])

def convert_database_db_to_dat(database, table, output_filename):
    with open(output_filename, mode='wt', encoding='UTF-8') as file:
        for i in database:
            for item in convert_transaction_db_to_dat(database[i], table):
                file.write(f'{item} ')
            file.write('\n')

## split a database regarding a cluster of items that has been calculated
## either at item embedding or at transaction embedding level
## for the time being everything is done in memory
## TODO: process each line at a time
def split_database_items(database, database_name, clusters, itemTrans):
    ## we create an in-memory database for each cluster
    ## the items currently are stored in the DB as strings as they are tokens for the
    ## word embedding
    ## the clusters of items can be just sets of integers for speed up reasons
    k = len(clusters)
    in_mem_splitting = {label: [] for label in clusters}
    for i in database:
        aux_set = set()
        [aux_set.add(int(item)) for item in database[i]]
        ## NOT THE MOST EFFICIENT WAY TO DO IT!!!!
        ## to speed up this: we should create an inverted index
        [in_mem_splitting[label].append(database[i]) for label in clusters if
         len(aux_set.intersection(clusters[label])) != 0]

    if not os.path.exists('output_databases'):
        os.mkdir('output_databases')
        print("Directory output_databases Created ")
    else:
        print("Directory output_databases already exists")

    for label in clusters:
        with open(os.path.join('output_databases', ntpath.basename(database_name) + '_' + str(label) + '_k' + str(k) + '.dat'), mode='wt',
                  encoding='UTF-8') as file:
            for trans in in_mem_splitting[label]:
                [file.write(f'{item} ') for item in trans]
                file.write('\n')

def split_database_transactions(database_name, clusters):
    if not os.path.exists('output_databases'):
        os.mkdir('output_databases')
        print("Directory output_databases Created ")
    else:
        print("Directory output_databases already exists")

    ## the splitting has been already done, and they just give clusters of transactions
    k = len(clusters)
    for label in clusters:
        with open(os.path.join('output_databases', ntpath.basename(database_name) + '_' + str(label) + '_k' + str(k) + '.dat'), mode='wt',
                  encoding='UTF-8') as file:
            for trans in clusters[label]:
                [file.write(f'{item} ') for item in trans]
                file.write('\n')

def split_database_transactions_translating(database_name, clusters, table):
    if not os.path.exists('output_databases'):
        os.mkdir('output_databases')
        print("Directory output_databases Created ")
    else:
        print("Directory output_databases already exists")
    ## the splitting has been already done, and they just give clusters of transactions
    k = len(clusters)
    for label in clusters:
        with open(os.path.join('output_databases', ntpath.basename(database_name) + '_' + str(label) + '_k' + str(k) + '.dat'), mode='wt',
                  encoding='UTF-8') as file:
            for trans in clusters[label]:
                [file.write(f'{table[int(item)]} ') for item in trans]
                file.write('\n')

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # params: -database filename of the extension
    #           -clustering k_means | fuzzy_k_means | hdbscan
    #           -granularity transaction | item
    #               clustering applied at item level or at transaction level (vertical or horizontal partitioning)
    #           -normalize to normalize the centroids and adopt a spherical clustering
    #                       (making euclidean_dist in that transformed space equivalent to cos_distance)
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="file of the database")
    my_parser.add_argument('-model_file', action='store', required=True,
                           help="file of the vectors")
    my_parser.add_argument('-clustering', action='store', required=True,
                           choices=['k_means', 'hdbscan', 'random'],
                           help="clustering algorithm, default: k_means", default='k_means')
    my_parser.add_argument('-vector_type', action='store', required=False,
                           choices=['w2v', 'd2v'],
                           help="embedding method, defines the embedding granularity, item/transaction, default: w2v",
                           default='w2v')
    my_parser.add_argument('-granularity', action='store', required=True,
                           choices=['transaction', 'item'],
                           help="clustering level, default: transaction", default='transaction')
    my_parser.add_argument('-itemTrans', action='store_true', required=False,
                           help="cluster the transactions by the items in the transaction clusters (just a test), default: False", default=False)
    my_parser.add_argument('-normalize', action='store_true', required=False,
                           help="normalize the vectors, default: False", default=False)
    my_parser.add_argument('-num_clusters', action='store', required=False, type=int,
                           help='number of clusters for the clustering algorithms, default: 4', default=4)

    args=my_parser.parse_args()

    start_time = time.time()
    if args.vector_type == 'w2v':
        model = Word2Vec.load(args.model_file)
        vector_dimension = model.wv.vector_size
        labelled_vects = {int(x): model.wv.get_vector(x) for x in model.wv.key_to_index}
    elif args.vector_type == 'd2v':
        model = Doc2Vec.load(args.model_file)
        vector_dimension = model.dv.vector_size
    print(f'Model loaded in {time.time() - start_time} s.')

    start_time = time.time()
    if (args.database_file.endswith('.db')):
        database_transactions = tdb.read_database_db(args.database_file)
    elif (args.database_file.endswith('.dat')):
        database_transactions = tdb.read_database_dat(args.database_file)
    print(f'Database loaded in {time.time() - start_time} s.')

    if args.vector_type == 'w2v':
        start_time = time.time()
        ## we need to calculate the representation of the transactions from their items' embeddings
        centroids = calculate_centroids(model, database_transactions)
        print(f'Centroids calculated in {time.time() - start_time} s.')

        start_time = time.time()
        weighted_centroids = calculate_weighted_centroids(model, database_transactions)
        print(f'weighted centroids calculated in {time.time() - start_time} s.')

        start_time = time.time()
        normalized_centroids = calculate_normalized_centroids(model, database_transactions)
        print(f'normalized centroids calculated in {time.time() - start_time} s.')
    elif args.vector_type == 'd2v':
        ## for retrocompatibility's sake, I use the same variable names for the transaction
        ## representation using doc2vec as well
        start_time = time.time()
        centroids = calculate_transaction_representations(model, database_transactions)
        print(f'Transaction representations calculated in {time.time() - start_time} s.')
        ## it makes no sense to have either weighted or normalized vectors in this case
        weighted_centroids = None
        normalized_centroids = None

    ## to avoid losing the linking information about the vector and its centroid,
    ## we force the array vects to be sorted regarding the labels of the dict
    ## There are clustering objects that do not allow to label new items regarding
    ## the clustering as faiss.kmeans does, so we need to keep track of it
    if args.granularity == 'item' and not args.clustering == 'random':
        vects = [labelled_vects[label] for label in sorted(labelled_vects)]
        print(vects[0].shape)
    else:
        if args.normalize:
            vects = [normalized_centroids[c] for c in sorted(normalized_centroids)]
        else:
            vects = [centroids[c] for c in sorted(centroids)]

    # Note that we might want to normalize the item vectors and we are not pre-calculating
    # them, that's why I've kept the option
    if args.clustering == 'k_means' or args.clustering == 'hdbscan':
        clustering = cluster_data(args.clustering, vects, args.num_clusters, args.normalize)

        if args.granularity == 'item':
            trans_cluster = item_labelling_from_item_vects(vects, clustering, vector_dimension, args.clustering)
        else:
            if args.itemTrans:
                # this is just a test: clustering the transactions by the items participating the transaction clusters
                # crisp partition
                trans_cluster = item_labelling_from_trans_vects(database_transactions, centroids, clustering, vector_dimension, args.clustering)
            else:
                trans_cluster = trans_labelling_from_trans_vects(database_transactions, centroids, clustering, vector_dimension, args.clustering)
    else:
        ## random
        trans_cluster = trans_labelling_random(database_transactions, args.num_clusters)

    if args.granularity == 'item' or args.itemTrans:
        if (args.database_file.endswith('.db')):
            aux_db_name = args.database_file[:-3]
        else:
            aux_db_name = args.database_file[:-4]
        split_database_items(database_transactions, aux_db_name+'_'+args.vect_type+'_'+args.granularity+'_'+str(args.itemTrans)+'_'
                             +args.clustering+'_'+str(vector_dimension)+'d_k'+str(args.num_clusters)+'_'+str(args.normalize)+'Norm',
                             trans_cluster, args.itemTrans)
    elif args.granularity == 'transaction':
        if args.database_file.endswith('.db'):
            ## we need to translate back the database if it's in Vreeken's format
            translation_table = tdb.read_analysis_table(args.database_file+'.analysis.txt')
            split_database_transactions_translating(args.database_file[:-3]+'_'+args.vect_type+'_'+args.granularity+'_'+args.clustering+'_'+str(vector_dimension)+'d_k'+str(args.num_clusters)+'_'+str(args.normalize)+'Norm',
                                                    trans_cluster,
                                                    translation_table)
        else:
            split_database_transactions(args.database_file[:-4]+'_'+args.vect_type+'_'+args.granularity+'_'+args.clustering+'_'+str(vector_dimension)+'d_k'+str(args.num_clusters)+'_'+str(args.normalize)+'Norm',
                                                    trans_cluster)