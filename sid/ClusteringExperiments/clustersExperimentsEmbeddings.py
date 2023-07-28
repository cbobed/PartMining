"""
Author: Jordi Bernad
Date: Feb 2022
Comments: Clustering experiments for CBDs and SBDs
   For CBDs experiments, use the following values for the bellow variables
	PATH_DIR = "CBDs/"
	PATH_MODELS = "embeddingsCBDs/"
	N_CLUSTERS = [4,8,16]
	
   For SBDs experiments, use the following values for the bellow variables
	PATH_DIR = "SBDs/"
	PATH_MODELS = "embeddingsSBDs/"
	N_CLUSTERS = [6]

   where PATH_DIR contains the datasets in https://github.com/cbobed/PartMining
   and PATH_MODELS contains the pretrained transaction embedding that also 
   can be downloaded from the same github.

This script produce output files with the results for all datasets and type of embeddings  
in a folder named with the value of the variable OUTPUT_DIR
"""

import os, sys, importlib
from os.path import expanduser
from pathlib import Path

from sklearn.metrics import normalized_mutual_info_score # Measure of Validation
import pandas as pd
import numpy as np
import datetime
import tqdm

import re
from scipy.special import softmax
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans
from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt')

class IteratorDataFile:
    """
     An iterator that yields items from all lines in a file
    """

    def __init__(self, path, removecls=False):
        self.path = path
        self.removecls = removecls
        
    def __iter__(self):
        for line in open(self.path, encoding="utf8"):
            #remove classification: last number in line 
            if (self.removecls == True):
                line = re.sub("[0-9]+$","",line)
            yield word_tokenize(line)

def getTransactionsEmbeddingsRealLabels(path_file_data, path_file_transactions_emb):
   """
    Parameters:
      path_file_data: Path to a file containing the transaction database.
           The database is a text file containing in each line
  	   a sequence of integers representing the ids of the items
	   in a transaction. The last number in a line represents
           the classification label of the regarding transaction.

      path_file_transaction_emb: A numpy matrix with the normalized transaction 
           embedding to length 1 of the transactions in path_file_data.

    Returns:
       A numpy matrix with the transactions embeddings in path_file_transaction_emb and
       a list with the regarding classification labels.
      
   """
    
    trans_embs = np.load(path_file_transactions_emb)
    
    itemIteratorCls = IteratorDataFile(path_file_data, False)
    max_length = 0
    cls1=[]
    for l in itemIteratorCls:
        cls1.append(int(l[-1]))
        max_length = max(len(l), max_length)
    cls1=np.array(cls1)
    unique_labels=np.unique(cls1)
    NUM_LABELS = len(unique_labels)
    d = {}
    i = 0
    for l in unique_labels:
        d[unique_labels[i]]=i
        i = i + 1
    real_labels = [d[l] for l in cls1]
    
    return trans_embs, real_labels

PATH_DIR = "CBDs/"
PATH_MODELS = "embeddingsCBDs/"
TOTAL_RUNS = 30
N_CLUSTERS = [4,8,16]

now=datetime.datetime.now()
now = now.strftime("%Y-%m-%d_%H-%M-%S")

print(now)

OUTPUT_DIR = "clusteringResults_Real_Emb/"
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

for TYPE_EMB in ["w2v", "Glove"]:
    if TYPE_EMB == "Glove":
        EPOCHS = 20
    else:
        EPOCHS = 10
        
    for EMB_DIM in [50, 100, 200]:
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
            file_name = files[0]
            path_dataset = PATH_DIR + dir + "/" + file_name
            print(path_dataset)
            file_model = "model_{:s}_D{:03d}_W05_E{:02d}_sn.npy".format(TYPE_EMB, EMB_DIM, EPOCHS)
            path_file_model = PATH_MODELS + file_name + "/" + file_model
            
            print("  " + TYPE_EMB + " " + str(EMB_DIM))
            print("   Loading transaction embeddings for file " + path_dataset + "...")
            #get transacction embeddings model and real labels
            trans_embs, real_labels = getTransactionsEmbeddingsRealLabels(path_dataset, 
                                                                          path_file_model)

            #fixed clusters tests
            print("  Calculating fixed number clusters tests...")
            for num_clusters in N_CLUSTERS:
                print("    Number clusters: " + str(num_clusters) + "...")
                nmi_emb_k = []
                rt_emb_k = []
                pbar = tqdm.trange(TOTAL_RUNS)
                for nprueba in pbar:
                    start_time = datetime.datetime.now()
                    kmeans = KMeans(n_clusters=num_clusters, n_init=1).fit(trans_embs)
                    #kmeans = faiss.Kmeans(d=EMB_DIM, k=num_clusters).train(trans_embs)
                    end_time = datetime.datetime.now()

                    pred_emb = kmeans.labels_.tolist()
                    nmi_emb_k.append(normalized_mutual_info_score(real_labels, pred_emb))
                    rt_emb_k.append((end_time - start_time).total_seconds())
                # write file name, and the TOTAL_RUNS measure and runtime values
                out_fix_k[num_clusters].write("{:s},{:s},{:d},{:d}".format(file_name, TYPE_EMB, EMB_DIM, num_clusters))
                for val in nmi_emb_k:
                    out_fix_k[num_clusters].write("," + str(val))
                for val in rt_emb_k:
                    out_fix_k[num_clusters].write("," + str(val))
                out_fix_k[num_clusters].write("\n")

        for out_k in out_fix_k.values():
            out_k.close()  
