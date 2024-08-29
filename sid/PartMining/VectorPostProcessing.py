###############################################################################
# File: VectorPostProcessing.py
# Author: Carlos Bobed
# Date: Ago 2024
# Comments: Program to apply the postprocessing proposed in All-but-top paper
#           (ICLR 2018) to improve the isotropy of the vectors in the embedding
# Notes:
##############################################################################

from gensim.models import Word2Vec
from gensim.models import KeyedVectors
from sid.util.AllButTop import all_but_the_top
import numpy as np
from sklearn import preprocessing
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

if __name__ == "__main__":
    # params: -database filename of the extension
    #           -clustering k_means | fuzzy_k_means | hdbscan
    #           -granularity transaction | item
    #               clustering applied at item level or at transaction level (vertical or horizontal partitioning)
    #           -normalize to normalize the centroids and adopt a spherical clustering
    #                       (making euclidean_dist in that transformed space equivalent to cos_distance)
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-model_file', action='store', required=True,
                           help="file of the vectors")
    my_parser.add_argument('-num_dimensions', action='store', required=False, type=int,
                           help='number of dimensions to consider for PCA, default: vect_d/100')

    args=my_parser.parse_args()

    start_time = time.time()
    model = Word2Vec.load(args.model_file)
    vector_dimension = model.wv.vector_size

    if args.num_dimensions:
        num_dimensions = args.num_dimensions
    else:
        num_dimensions = vector_dimension // 100

    labelled_vects = {int(x): model.wv.get_vector(x) for x in model.wv.key_to_index}
    print(f'Model loaded in {time.time() - start_time} s.')

    output_vectors = all_but_the_top(model.wv.vectors, num_dimensions)
    kVectors = KeyedVectors(vector_dimension)
    for x in model.wv.key_to_index:
        kVectors.add_vector(x, output_vectors[model.wv.key_to_index[x]])
    kVectors.save(args.model_file+"-postProc-"+str(num_dimensions)+".vect")