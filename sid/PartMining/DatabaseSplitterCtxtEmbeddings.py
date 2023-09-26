###############################################################################
# File: DatabaseSplitterCtxtEmbeddings.py
# Author: Carlos Bobed
# Date: Sept 2023
# Comments: Program to split a database according to the CLS vector of each
# transaction instead of having to calculate the centroids or to do the vertical
# partitioning
##############################################################################

from gensim.models import Word2Vec
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

## I was going to use scikit directly, but I saw this post
## kudos for him https://towardsdatascience.com/k-means-8x-faster-27x-lower-error-than-scikit-learns-in-25-lines-eaedc7a3a0c8
import faiss

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

## finally, we build the clusters accordingly from the transaction vectors
def trans_labelling_from_trans_vects(database, trans_vects, trans_clusters, dim, clustering_method):
    cluster = {}
    base_label_trans_item = 'trans_clust_'
    if clustering_method == 'k_means':
        for t, vect in enumerate(trans_vects):
            trans_D, trans_I = trans_clusters.index.search(vect.reshape(1, dim), 1)
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

    my_parser.add_argument('-normalize', action='store_true', required=False,
                           help="normalize the vectors, default: False", default=False)
    my_parser.add_argument('-num_clusters', action='store', required=False, type=int,
                           help='number of clusters for the clustering algorithms, default: 4', default=4)

    args=my_parser.parse_args()

    start_time = time.time()
    vects = np.load(args.model_file)
    print(f'Vectors loaded in {time.time() - start_time} s.')

    start_time = time.time()
    database_transactions = tdb.read_database_dat(args.database_file)
    print(f'Database loaded in {time.time() - start_time} s.')

    print(f'checking :: vects {vects.shape} :: database {len(database_transactions)}')

    vector_dimension=vects.shape[1]
    print(vector_dimension)
    # Note that we might want to normalize the item vectors and we are not pre-calculating
    # them, that's why I've kept the option
    if args.clustering == 'k_means' or args.clustering == 'hdbscan':
        clustering = cluster_data(args.clustering, vects, args.num_clusters, args.normalize)
        trans_cluster = trans_labelling_from_trans_vects(database_transactions, vects, clustering, vector_dimension, args.clustering)
        split_database_transactions(args.database_file[:-4]+'_transaction_'+args.clustering+'_'+str(vector_dimension)+'d_k'+str(args.num_clusters)+'_'+str(args.normalize)+'Norm',
                                                    trans_cluster)
