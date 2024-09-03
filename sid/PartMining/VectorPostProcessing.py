###############################################################################
# File: VectorPostProcessing.py
# Author: Carlos Bobed
# Date: Ago 2024
# Comments: Program to apply the postprocessing proposed in All-but-top paper
#           (ICLR 2018) to improve the isotropy of the vectors in the embedding
# Notes:
##############################################################################

import argparse
import time

from gensim.models import KeyedVectors
from gensim.models import Word2Vec

from AllButTop import all_but_the_top

## I was going to use scikit directly, but I saw this post
## kudos for him https://towardsdatascience.com/k-means-8x-faster-27x-lower-error-than-scikit-learns-in-25-lines-eaedc7a3a0c8

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

    output_vectors = all_but_the_top(model.wv.vectors, num_dimensions)
    model.wv.vectors = output_vectors
    model.save(args.model_file+"-postProc-"+str(num_dimensions)+".vect")
