#===============================================================
# File: mergeMethodsComparison.sh
# Author: Carlos Bobed
# Date: Sept 2021
# Comments: script for launching the different merge methods 
# 	over already existing mined codetables
#	$1 == database filename (with .dat extension)
#	$2 == clustering method (k_means) 
#	$3 == num clusters
# 	$4 == starting index
#	$5 == vector dimension 
#	$6 == directory where all the data is 
#===============================================================

CURRENT_PATH=`pwd`

PYTHON_PROJECT_PATH=/home/siduser/cbobed/git/PartMining
DATASETS_PATH=/home/siduser/cbobed/git/PartMining
OUTPUT_SPLITTED_PATH=$6

# configuration of the second script to split the database_name
# k_means , random
CLUSTERING=$2
GRANULARITY=transaction
NUM_CLUSTERS=$3
PRUNING_THRESHOLD=0
DIMENSION=$5

# configuration of the third script
# set ALL_RATIOS to -all_ratios to calculate the partial ratios
ALL_RATIOS=-all_ratios
MERGE_METHODS="naive naive_plus informed"

OUTPUT_FILE="$1"-"$2"-"$3"-output-merged.out
ERR_FILE="$1"-"$2"-"$3"-output-merged.err
TIME_FILE="$1"-"$2"-"$3"-output-merged.time

# clean the outputs 
echo "" > "$OUTPUT_FILE"
echo "" > "$ERR_FILE"
echo "" > "$TIME_FILE"

# %1 is the filename of the dataset
cd $PYTHON_PROJECT_PATH

#Transactions: we should have in output_databases => 
#  dbBasename_GRANULARITY_CLUSTERING_DIMENSIONd_kNUM_CLUSTERS_[True|False]Norm * 

ln -s "$DATASETS_PATH"/"$1" "$6"/"$1"

DB_BASENAME=${1/.dat/}

if [[ $NORMALIZE = "" ]]; then 
	NORM_NAME=False
else 
	NORM_NAME=True
fi

if [[ $CLUSTERING = "random" ]]; then  
	TRANS_NAME=rand_clust
else 
	if [[ $GRANULARITY = "transaction" ]]; then  
		TRANS_NAME=trans_clust
	else 
		TRANS_NAME=item_clust
	fi
fi

SPLITTED_BASENAME="$DB_BASENAME"_"$GRANULARITY"_"$CLUSTERING"_"$DIMENSION"d_k"$NUM_CLUSTERS"_"$NORM_NAME"Norm_"$TRANS_NAME"
# afterwards  '_' + str(label) + '_k' + str(k) + '.dat' is added 

for db in "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME"*.dat; do 
	(( ACTUAL_NUM_CLUSTER = ACTUAL_NUM_CLUSTER + 1 ))
done 

for i in $MERGE_METHODS; do 
	echo $i
done 

# $4 is going to be the initial index 
echo We have "$ACTUAL_NUM_CLUSTER" clusters
for crt in $MERGE_METHODS; do 
	echo "-- MERGING METHOD $crt" >> "$OUTPUT_FILE"
	echo "calculating merged ratio with $crt ..." >> "$TIME_FILE"
	{ time ./calculateMergedRatio.sh $1 "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME" "$ACTUAL_NUM_CLUSTER" $4 "$PRUNING_THRESHOLD" "$crt" "$ALL_RATIOS" -parallel -split_parallelization >> "$OUTPUT_FILE" 2>>"$ERR_FILE" ; } 2>>"$TIME_FILE"
done 
cd "$CURRENT_PATH"
