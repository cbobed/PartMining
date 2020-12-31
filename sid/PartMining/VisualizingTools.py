###############################################################################
# File: VisualizingTools.py
# Author: Carlos Bobed
# Date: Dec 2020
# Comments: Some code to visualize what's happening with the item embeddings
#   and the transactions using tSNE - WARNING: ONLY FOR DB databases
# Modifications:
###############################################################################

from gensim.models import Word2Vec
import numpy as np
import argparse
import sys
#Plot helpers
import matplotlib
import matplotlib.pyplot as plt

#import sid.PartMining.TransactionDatabase as tdb
#import sid.PartMining.CodeTable as ct
import TransactionDatabase as tdb
import CodeTable as ct

## this import depends on whether you have support for tsnecuda
# (only available for linux + cuda enabled computers)
# Highly recommended due to the incresed performance
from sklearn.manifold import TSNE
#from tsnecuda import TSNE

# we must load:
#   a model: item vector representations
#   a database: transactions using such items
#   a codetable: optional

def calculate_centroids (model, labelled_transactions):
    # more pythonic way
    return { label: np.mean([model.wv[it] for it in  labelled_transactions[label]], axis=0) for label in labelled_transactions}


if __name__ == '__main__':
    # params: -model file
    #         -database file
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-model', action='store', required=True,
                           help="file with the item embeddings")
    my_parser.add_argument('-db', action='store', required=True,
                           help="file with the transaction database - Must be a .db file")
    my_parser.add_argument('-ct', action='store', required=False,
                           help="code table of the database if available")
    args = my_parser.parse_args()

    model = Word2Vec.load(args.model)
    # we keep track of the items by tagging them with their int representation
    labelled_vects = {int(x): model.wv[x] for x in model.wv.vocab}

    if (args.db.endswith('.db')):
        database_transactions = tdb.read_database_db(args.db)
    else:
        print('not valid DB file extension')
        sys.exit(-1)

    centroids = calculate_centroids(model, database_transactions)

    if args.ct:
        #False is to avoid loading the singleton part of the CT
        codes = ct.read_codetable(args.ct, False)
        centroids_codes = calculate_centroids(model, {label: codes[label]['code'] for label in codes})
    else:
        codes = None
        centroids_codes = None

    # there are a number of blogs and people that suggest reducing the dimensions of the space
    # before using t-SNE due to its cost
    # one way is to use PCA

    # taken from https://towardsdatascience.com/visualising-high-dimensional-datasets-using-pca-and-t-sne-in-python-8ef87e7915b

    # pca = PCA(n_components=3)
    # pca_result = pca.fit_transform(df[feat_cols].values)
    # df['pca-one'] = pca_result[:,0]
    # df['pca-two'] = pca_result[:,1]
    # df['pca-three'] = pca_result[:,2]
    # print('Explained variation per principal component: {}'.format(pca.explained_variance_ratio_))
    # Explained variation per principal component: [0.09746116 0.07155445 0.06149531]

    # besides
    # “Since t-SNE scales quadratically in the number of objects N, its applicability is limited to data
    # sets with only a few thousand input objects; beyond that, learning becomes too slow to be practical
    # (and the memory requirements become too large)”.

    # However, I have to say that I've tried it with some tens of thousands
    # (visualizing the item embeddings of DBpedia 2016 conversion) and it was somehow bearable (can't recall the exact time it took,
    # but it ended ... which is nice :P)

    # for 'connect database' 65K transactions (and a non-very optimized version of t-SNE - there are multithreaded ones)
    # it has taken about 5 minutes (MSI-laptop)

    # We limit the number of centroids to be displayed
    top_position = len(centroids)
    # 25000 if len(centroids)>5000 else len(centroids)
    # changed from the notebook to make the code reps optional:
    ## 0 .. len(labelled_vects)-1 => projected vectors of items
    ## len(labelled_vects) .. len(labelled_vects)+top_position-1 => projected transactions
    ## len(labelled_vects) len(labelled_vects)+top_position-1 .. end  => codes

    start_centroids = len(labelled_vects)
    start_centroids_codes = len(labelled_vects) + top_position


    #+ [centroids[i] for i in range(top_position)]
     #                            + ( [centroids_codes[i] for i in range(len(centroids_codes))] if codes is not None else [] )  )


    positions_to_draw = np.array([labelled_vects[x] for x in range(len(labelled_vects))]
                                 + [centroids[i] for i in range(top_position)]
                                 + ( [centroids_codes[i] for i in range(len(centroids_codes))] if codes is not None else [] )  )

    ## We have to transform all of the ones that are going to be displayed at once
    Z = TSNE(n_components=2).fit_transform(positions_to_draw)

    fig_size = 5
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.set_size_inches(fig_size * 2, fig_size, forward=True)
    ax1.plot(Z[:len(labelled_vects), 0], Z[:len(labelled_vects), 1], 'o')
    ax1.set_title(f'Items - {args.model} - {args.db}')
    ax1.set_yticklabels([])  # Hide ticks
    ax1.set_xticklabels([])  # Hide ticks
    # transactions
    ax2.plot(Z[start_centroids:start_centroids_codes, 0], \
             Z[start_centroids:start_centroids_codes, 1], 'x')
    if codes is not None:     # codes
        ax2.plot(Z[start_centroids_codes:, 0], Z[start_centroids_codes:, 1], 'o')

    ax2.set_title(f'Transactions -{args.model} - {args.db}')
    ax2.set_yticklabels([])  # Hide ticks
    ax2.set_xticklabels([])  # Hide ticks
    plt.show()