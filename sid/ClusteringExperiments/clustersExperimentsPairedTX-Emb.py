"""
Author: Jordi Bernad
Date: Feb 2022
Comments: Clustering experiments for CBDs and SBDs.
 Intructions to use the script:
   1. Clone the github repository https://github.com/riccotti/TX-Means.
      You download a folder called TX-Means.
   2. Modify the bellow variable 'Folder_Cloned_In' with the path to the TX-Means folder
   3. Previously to run this script, it is necessary to run the python script 
         clustersExperimentsTxmeans.py
      to obtain the results for tx-means algorithm. This script writes the results 
      in a folder. Let us suppose that the latter results folder for CBDs datasets
	  is called 
	     'clusteringResults_Real_TX'
	  and the results folder for SBDs datasets 
	  is called 
	     'clusteringResults_Syn_TX'
     		 
   4. For CBDs experiments, use the following values for the bellow variables
 	    PATH_DIR = "CBDs/"
		PATH_RESULTS_TX = "clusteringResults_Real_TX/results_TX_D00_SN_K00.txt"
	
     For SBDs experiments, use the following values for the bellow variables
	    PATH_DIR = "SBDs/"
		PATH_RESULTS_TX = "clusteringResults_Syn_TX/results_TX_D00_SN_K00.txt"

     where PATH_DIR contains the datasets in https://github.com/cbobed/PartMining

This script produce output files with the results for all datasets in a folder named
with the value of the variable OUTPUT_DIR
"""

import os, sys, importlib
from os.path import expanduser
from pathlib import Path
from sklearn.metrics import normalized_mutual_info_score # Measure of Validation
import pandas as pd
import numpy as np
import datetime
import tqdm
import gensim
import re
from gensim.models import Word2Vec
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
PATH_MODELS = "embeddingsClassic/"
TOTAL_RUNS = 30

now=datetime.datetime.now()
now = now.strftime("%Y-%m-%d_%H-%M-%S")
print(now)

PATH_RESULTS_TX = "clusteringResults_Real_TX/results_TX_D00_SN_K00.txt"
resultsTx = pd.read_csv(PATH_RESULTS_TX)

OUTPUT_DIR = "clusteringResults_Paired_TX-EMb_Real/"
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
    
OUTPUT_FILE = OUTPUT_DIR + "results_TX_D-1_SN_K00.txt"
output_p = open(OUTPUT_FILE, 'w')
head = ",".join(list(resultsTx.columns))
output_p.write(head)
output_p.write("\n")

for index, row in resultsTx.iterrows():
    nclusters = row[64:].tolist()
    file_name = row[0]
    n_clusters_p = row[64:].tolist()
    print("Processing paired embeddings for file " + file_name)
    
    for TYPE_EMB in ["w2v", "Glove"]:
        if TYPE_EMB == "Glove":
            EPOCHS = 20
        else:
            EPOCHS = 10

        for EMB_DIM in [50, 100, 200]:
            
            path_dataset = PATH_DIR + file_name + "/" + file_name
            file_model = "model_{:s}_D{:03d}_W05_E{:02d}_sn.npy".format(TYPE_EMB, EMB_DIM, EPOCHS)
            path_file_model = PATH_MODELS + file_name + "/" + file_model

            print("  " + TYPE_EMB + " " + str(EMB_DIM))
            print("   Loading transaction embeddings for file " + path_dataset + "...")
            #get transacction embeddings model and real labels
            trans_embs, real_labels = getTransactionsEmbeddingsRealLabels(path_dataset, 
                                                                          path_file_model)

            #paired clusters tests
            print("  Calculating paired number clusters tests...")
            nmi_emb_p = []
            rt_emb_p = []
            for num_clusters in tqdm.tqdm(n_clusters_p):
                start_time = datetime.datetime.now()
                kmeans = KMeans(n_clusters=num_clusters, n_init=1).fit(trans_embs)
                #kmeans = faiss.Kmeans(d=EMB_DIM, k=num_clusters).train(trans_embs)
                end_time = datetime.datetime.now()

                pred_emb = kmeans.labels_.tolist()
                nmi_emb_p.append(normalized_mutual_info_score(real_labels, pred_emb))
                rt_emb_p.append((end_time - start_time).total_seconds())
            # write file name, and the TOTAL_RUNS measure and runtime values
            output_p.write("{:s},{:s},{:d},{:d}".format(file_name, TYPE_EMB, EMB_DIM, -1))
            for val in nmi_emb_p:
                output_p.write("," + str(val))
            for val in rt_emb_p:
                output_p.write("," + str(val))
            for val in n_clusters_p:
                output_p.write("," + str(val))
            output_p.write("\n")

output_p.close()
