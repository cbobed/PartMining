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
	    N_CLUSTERS = [4,8,16]
	
     For SBDs experiments, use the following values for the bellow variables
	    PATH_DIR = "SBDs/"
	    N_CLUSTERS = [6]

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
from algorithms.tkmeans import TKMeans # The class (like sklearn)
from algorithms.txmeans import remap_items, count_items, sample_size # Util functions
from algorithms.txmeans import basket_list_to_bitarray, basket_bitarray_to_list # Converting(Reverting) to(from) bitarray
from generators.datamanager import read_uci_data, read_synthetic_data # (Convert the data in nice basket format)
from validation.validation_measures import delta_k, purity, normalized_mutual_info_score # Measure of Validation
from algorithms.util import jaccard_bitarray
from sklearn.metrics import normalized_mutual_info_score # Measure of Validation
import pandas as pd
import numpy as np
import datetime
import tqdm
import datetime
import re

def getTransactionsRealLabelsForTxmeans (filename):
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
N_CLUSTERS = [4,8,16]
MODEL = "TK"

now=datetime.datetime.now()
now = now.strftime("%Y-%m-%d_%H-%M-%S")

OUTPUT_DIR = "clusteringResults_Real_TK/"
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

for TYPE_EMB in ["tk"]:
        
    for EMB_DIM in [0]:
        dirs = os.listdir(PATH_DIR)
        dirs = sorted(dirs)

        output_files_emb_fixed_k = {}
        for k in N_CLUSTERS:
            output_files_emb_fixed_k[k] = OUTPUT_DIR + "/results_{:s}_D{:03d}_SN_K{:02d}.txt".format(TYPE_EMB,EMB_DIM,k)

        head_emb = "dataset,model,emb_dim,nclusters"
        for i in range(TOTAL_RUNS):
            head_emb = head_emb + ",NMI_{:02d}".format(i+1)
        for i in range(TOTAL_RUNS):
            head_emb = head_emb + ",RT_{:02d}".format(i+1)

        out_fix_k = {}
        for k, name in zip(output_files_emb_fixed_k.keys(),output_files_emb_fixed_k.values()):
            out_fix_k[k]=open(name,'w')
            out_fix_k[k].write(head_emb + "\n")

        for dir in dirs:
            files=[file for file in os.listdir(PATH_DIR + dir) if re.match("^[^.].*", file)]
            files=sorted(files)
            FILE_NAME = files[0]
            PATH_DATASET = PATH_DIR + dir + "/" + FILE_NAME
            PATH_DATASET_TX = PATH_DIR + dir + "/" + files[1]
            print(PATH_DATASET)
            print("   Calculating transactions tk for file " + PATH_DATASET_TX + "...")
            #get transactions (baskets), and real labels
            baskets_list, real_labels = getTransactionsRealLabelsForTxmeans(PATH_DATASET_TX)
    
            # Get the number of baskets (equal to number of data) 
            nbaskets = len(baskets_list)
            # Get the number of different item
            nitems = count_items(baskets_list)

            #fixed clusters tests
            print("  Calculating fixed number clusters tests...")
            for num_clusters in N_CLUSTERS:
                print("    Number clusters: " + str(num_clusters) + "...")
                nmi_tk_k = []
                rt_tk_k = []
                pbar = tqdm.trange(TOTAL_RUNS)
                for nprueba in pbar:
                    tkmeans_model = TKMeans()
                    
                    start_time = datetime.datetime.now()
                    tkmeans_model.fit(baskets_list, nbaskets, nitems, k=num_clusters, niter=1)
                    end_time = datetime.datetime.now()
                    # Get the label and the clusters 
                    res = tkmeans_model.clustering

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
                        
                    nmi_tk_k.append(normalized_mutual_info_score(real_labels, pred_labels))
                    rt_tk_k.append((end_time - start_time).total_seconds())
                                
                # write file name, and the TOTAL_RUNS measure and runtime values
                out_fix_k[num_clusters].write("{:s},{:s},{:d},{:d}".format(FILE_NAME, TYPE_EMB, EMB_DIM, num_clusters))
                for val in nmi_tk_k:
                    out_fix_k[num_clusters].write("," + str(val))
                for val in rt_tk_k:
                    out_fix_k[num_clusters].write("," + str(val))
                out_fix_k[num_clusters].write("\n")

        for out_k in out_fix_k.values():
            out_k.close()  

