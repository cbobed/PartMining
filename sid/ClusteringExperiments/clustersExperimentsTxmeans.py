"""
Author: Jordi Bernad
Date: Feb 2022
Comments: Clustering experiments for CBDs and SBDs.
 Intructions to use the script:
   1. Clone the github repository https://github.com/riccotti/TX-Means.
      You download a folder called TX-Means.
   2. Modify the bellow variable 'Folder_Cloned_In' with the path to the TX-Means folder
   3. For CBDs experiments, use the following values for the bellow variables
 	    PATH_DIR = "CBDs/"
	
     For SBDs experiments, use the following values for the bellow variables
	    PATH_DIR = "SBDs/"

     where PATH_DIR contains the datasets in https://github.com/cbobed/PartMining

This script produce output files with the results for all datasets in a folder named
with the value of the variable OUTPUT_DIR
"""

import os, sys, importlib
from os.path import expanduser
from pathlib import Path

# TO DO: Better way to add to PythonPath the package.
home = str(Path.home())

## MODIFY HERE! ##
# This need to point on the folder where you clone the repo (respect to the home...)
Folder_Cloned_In = '/home/siduser/jbernad/clusteringExperiments/' # Change here..
##################

# Full dir name
path_to_lib =  Folder_Cloned_In

if os.path.isdir(path_to_lib + 'TX-Means'):
    print(f'My Home is: {home}')
    print(f'I cloned in: {path_to_lib}')
    # Add dirs to Python Path 
    sys.path.insert(0, path_to_lib + 'TX-Means/code')
    sys.path.insert(0, path_to_lib + 'TX-Means/code/algorithms')
else:
    print("Can't find Directory.")
    print('For example: you are in')
    print(str(os.getcwd()))

import algorithms.txmeans
from algorithms.txmeans import TXmeans # The class (like sklearn)
from algorithms.txmeans import remap_items, count_items, sample_size # Util functions
from algorithms.txmeans import basket_list_to_bitarray, basket_bitarray_to_list # Converting(Reverting) to(from) bitarray
from generators.datamanager import read_uci_data, read_synthetic_data # (Convert the data in nice basket format)
from validation.validation_measures import delta_k, purity, normalized_mutual_info_score # Measure of Validation
from algorithms.util import jaccard_bitarray

import pandas as pd
import numpy as np
import datetime
import re
import tqdm

def getTransactionsRealLabelsForTxmeans(filename):
    #read data
    baskets_real_labels = read_synthetic_data(filename)
    # Save baskets and the real labels 
    baskets_list = list()
    real_labels = list()
    count = 0
    for basket, label in baskets_real_labels:
        baskets_list.append(basket)
        real_labels.append(label)
        count += 1    
    # Speeding up the Jaccard distance: 
    baskets_list, map_newitem_item, map_item_newitem = remap_items(baskets_list)
    baskets_list = basket_list_to_bitarray(baskets_list, len(map_newitem_item))
    
    return baskets_list, real_labels

PATH_DIR = "CBDs/"
TOTAL_RUNS = 30
MODEL = "TX"
EMB_DIM = 0
K = 0

dirs = os.listdir(PATH_DIR)
dirs = sorted(dirs)

now=datetime.datetime.now()
now = now.strftime("%Y-%m-%d_%H-%M-%S")

OUTPUT_DIR = "clusteringResults_Real_TX/" 
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
OUTPUT_FILE_TX = OUTPUT_DIR + "/results_{:s}_D{:02d}_SN_K{:02d}.txt".format(MODEL,EMB_DIM,K)

HEAD_TX = "dataset,model,emb_dim,nclusters"
for i in range(TOTAL_RUNS):
    HEAD_TX = HEAD_TX + ",NMI_{:02d}".format(i+1)
for i in range(TOTAL_RUNS):
    HEAD_TX = HEAD_TX + ",RT_{:02d}".format(i+1)
for i in range(TOTAL_RUNS):
    HEAD_TX = HEAD_TX + ",K_{:02d}".format(i+1)

out_tx = open(OUTPUT_FILE_TX, 'w')
out_tx.write(HEAD_TX + "\n")

for dir in dirs:
    files=[file for file in os.listdir(PATH_DIR + dir) if re.match("^[^.].*", file)]
    files=sorted(files)
    FILE_NAME = files[0]
    PATH_DATASET = PATH_DIR + dir + "/" + FILE_NAME
    PATH_DATASET_TX = PATH_DIR + dir + "/" + files[1]
    print(PATH_DATASET)
    print("   Calculating transactions tx for file " + PATH_DATASET_TX + "...")
    #get transactions (baskets), and real labels
    baskets_list, real_labels = getTransactionsRealLabelsForTxmeans(PATH_DATASET_TX)
    
    # Get the number of baskets (equal to number of data) 
    nbaskets = len(baskets_list)
    # Get the number of different item
    nitems = count_items(baskets_list)
    
    nmi_tx = []
    rt_tx = []
    nclusters_tx = []
    for nprueba in tqdm.trange(TOTAL_RUNS):
        # Initialize the model
        txmeans_model = TXmeans()
        # Get subsamples of the dataset (in order to speed up)
        nsample = sample_size(nbaskets, 0.05, conf_level=0.99, prob=0.5)
        # Fit the model
        start_time = datetime.datetime.now()
        txmeans_model.fit(baskets_list, nbaskets, nitems, random_sample=nsample)
        end_time = datetime.datetime.now()
        
        # Get the label and the clusters 
        res = txmeans_model.clustering

        # Initialize empty predicted labels
        pred_labels = [0] * len(real_labels)

        # Initialize empty cluster list
        baskets_clusters = list()
        for label, cluster in enumerate(res):
            # Revert the bitarray transform.
            cluster_list = basket_bitarray_to_list(cluster['cluster']).values()
            for bid, bitarr in cluster['cluster'].items():
                # Labels of every data point
                pred_labels[bid] = label
                # Clusters
                baskets_clusters.append(cluster_list)
                
        num_clusters = len(set(pred_labels))
        nmi_tx.append(normalized_mutual_info_score(real_labels, pred_labels))
        nclusters_tx.append(num_clusters)
        rt_tx.append((end_time - start_time).total_seconds())
    
    #write results tests
    out_tx.write(FILE_NAME)
    out_tx.write("," + MODEL)
    out_tx.write("," + str(EMB_DIM))
    out_tx.write("," + str(K))
    for val in nmi_tx:
        out_tx.write("," + str(val))
    for val in rt_tx:
        out_tx.write("," + str(val))
    for val in nclusters_tx:
        out_tx.write("," + str(val))
    out_tx.write("\n")
    
out_tx.close()
