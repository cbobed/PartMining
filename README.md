# PartMining
Repository for all the code and resources associated with the paper *Language-Model Based Informed Partition of Databases to Speed Up Pattern Mining*, submitted to VLDB 2024 (pVLDB, vol. 17). 

## Content of the repository

Source code of the approach for partitioning a transactional database adopting static dense language models and its related experiments. The code to convert RDF data into a transactional database can be found in the [SWKrimpSim repository](https://github.com/MaillPierre/SWKrimpSim) associated with our [previous works on assessing the structural differences of RDF graphs](http://doi.org/10.3233/SW-200368). 

+ The [sid folder](https://github.com/cbobed/PartMining/tree/main/sid) contains the source code for managing all the data (loading the different formats of databases and code tables, calculating the item and transaction embeddings, partitioning the database, and calculating the different measures - e.g., compression ratio, entropy, etc.).

  We use a modified version SLIM (extended to handle more than 16bit item identifiers) to mine the interesting patterns of each partition which can be found [here](https://github.com/MaillPierre/SWKrimpSim/blob/master/SlimBinSource-20120607mod.tar.gz). We suggest using the scripts already available at [SWKrimpSim](https://github.com/MaillPierre/SWKrimpSim) as they simplify greatly using both KRIMP and SLIM implementations. 

+ The [scripts folder](https://github.com/cbobed/PartMining/tree/main/scripts) contains auxiliary scripts to launch the different steps of the approach (as we use SLIM externally to mine the patterns of each partition, we have split the different steps in different scripts).
  
+ The [datasets folder](https://github.com/cbobed/PartMining/tree/main/datasets) contains the .dat files of the synthetic and non-synthetic datasets used in the experiments (corresponding to SBDs and CBDs). LDBs datasets can be found here (GitHub did not allowed us to host >100MB files): [DBpedia36](http://sid.cps.unizar.es/projects/dataEvolution/dbpedia36PCB.tar.gz), [DBpedia2014](http://sid.cps.unizar.es/projects/dataEvolution/dbpedia2014PCB.tar.gz), [DBpedia2016-10](http://sid.cps.unizar.es/projects/dataEvolution/dbpedia201610PCB.tar.gz), and [Kosarak](http://sid.cps.unizar.es/projects/dataEvolution/kosarak.tar.gz) - Due to some server configuration problems, the https layer is not able to serve the files, that's why we have left them with just the http URL. The synthetic ones (SDBs) were built following [*Guidoti et al., Clustering Individual Transactional Data for Masses of Users (SIGKDD'17)*](http://doi.org/10.1145/3097983.3098034), using their code available at [tx-means repository](https://github.com/riccotti/TX-Means). Since SLIM and TX-Means use different file formats to represent transactions, we provide the SBDs and CBDs data files in both formats (TX-Means format is marked with a `_tx` in the filename).
  
+ The [experimentalResults folder](https://github.com/cbobed/PartMining/tree/main/experimentalResults) contains the raw results of the different experiments reported in the paper. 

+ The [notebook folder](https://github.com/cbobed/PartMining/tree/main/notebooks) contains the initial notebooks used in the early stages of the project, including visualization and vector length/item frequency correlation. However, the code to be used is included in the *sid* folder (see above).

+ For better reproducibility of the classification and clustering experiments, we also provide pre-trained transaction embeddings for CBDs and SBDs: [embeddings for CBDs](https://drive.google.com/uc?export=download&id=1AKmY40Ws0OV0L-cSCo60pPcjBxp1Haq5) and [embeddings for SBDs](https://drive.google.com/uc?export=download&id=1kzYyiTB7Q3VnqrAc-ilcsCYh3GFMUDZR). To reproduce the experiments:
    - Classification experiments: Follow the instructions in the notebook [`notebooks/ExperimentsClassificationTransactions.ipynb`](https://github.com/cbobed/PartMining/blob/main/notebooks/ExperimentsClassificationTransactions.ipynb)
    - Clustering experiments: Follow the instructions in the Python scripts [`sid/ClusteringExperiments/clustersExperimentsEmbeddings.py`](https://github.com/cbobed/PartMining/blob/main/sid/ClusteringExperiments/clustersExperimentsEmbeddings.py), [`sid/ClusteringExperiments/clustersExperimentsTkmeans.py`](https://github.com/cbobed/PartMining/blob/main/sid/ClusteringExperiments/clustersExperimentsTkmeans.py), [`sid/ClusteringExperiments/clustersExperimentsTxmeans.py`](https://github.com/cbobed/PartMining/blob/main/sid/ClusteringExperiments/clustersExperimentsTxmeans.py), [`sid/ClusteringExperiments/clustersExperimentsPairedTX-Emb.py`](https://github.com/cbobed/PartMining/blob/main/sid/ClusteringExperiments/clustersExperimentsPairedTX-Emb.py)
  

## Citation

Not yet published, submitted for pVLDB vol.17, 2024. 

