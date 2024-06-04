
import TransactionDatabase as tdb

import argparse
import sys
import numpy as np

import matplotlib
import matplotlib.pyplot as plt

import math


# we must:
#  - load and display the base db
#  - load, translate and display the partitions

def build_global_cooc_matrix(transaction_db, vocab_size):
    cooc_matrix = np.zeros((vocab_size, vocab_size))
    for label in transaction_db:
        int_items = [int(item) for item in transaction_db[label]]
        ## items in range [0..vocab_size-1]
        for i in int_items[:-1]:
            for j in int_items[i+1:]:
                cooc_matrix[i][j] +=1
                cooc_matrix[j][i] +=1
    return cooc_matrix

def build_cooc_matrix_translating (transaction_dat, vocab_size, analysis_table):
    cooc_matrix = np.zeros((vocab_size, vocab_size))
    for label in transaction_dat:
        translated_items = [analysis_table[1][int(item)] for item in transaction_dat[label]]
        for i in translated_items[:-1]:
            for j in translated_items[i+1:]:
                cooc_matrix[i][j] +=1
                cooc_matrix[j][i] +=1
    return cooc_matrix


if __name__ == '__main__':
    # params:   -db_base file
    #           -partition_basename
    #           -k
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-db_base', action='store', required=True,
                           help="file with the complete transaction database .. must be a db")
    my_parser.add_argument('-partition_basename', action='store', required=True,
                           help="basename of the partition files")
    my_parser.add_argument('-k', action='store', required=True,
                           help="number of partitions")
    args = my_parser.parse_args()

    if (args.db_base.endswith('.db')):
        original_db = tdb.read_database_db(args.db_base)
        analysis_table = tdb.read_analysis_table_bidir(args.db_base+'.analysis.txt')
    else:
        print('not valid DB file extension')
        sys.exit(-1)

    original_matrix = build_global_cooc_matrix(original_db, len(analysis_table[0]))

    plt.figure()
    ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(original_matrix)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("", rotation=-90, va="bottom")
    plt.show(block=False)

    plt.figure()
    k = int(args.k)
    aux = math.ceil(math.sqrt(k))
    if (aux * aux == args.k):
        figure, axis = plt.subtplots(aux, aux)
    else:
        figure, axis = plt.subplots (aux, aux+1)

    for i in range(k):
        print(f'processing {i} partition ... ')
        partition_dat = tdb.read_database_dat(args.partition_basename+str(i)+'_k'+str(k)+'.dat')
        current_matrix = build_cooc_matrix_translating(partition_dat, len(analysis_table[0]), analysis_table)

        im = axis[i//aux][i%aux].imshow(current_matrix)
        current_cbar = axis[i//aux][i%aux].figure.colorbar(im, ax=axis[i//aux][i%aux])
        current_cbar.ax.set_ylabel("", rotation=-90, va="bottom")
    plt.show()



