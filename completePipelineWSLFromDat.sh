#===============================================================
# File: completePipelineWSLFromDat.sh
# Author: Carlos Bobed
# Date: Sept 2021
# Comments: script for bash command line to launch the 
# 		whole pipeline starting from a .dat file. It requires the scripts prepared for 
#  	Maillot et al. 2018, and Bobed et al. 2020 to obtain the codetables 
# 		This script must be launched within a conda environment 
# 		with the proper packages installed. 
# 	Usage: configure the execution variables,and the following 
#		parameters are accepted: 
# 			%1 the filename of the dataset
#			%2 clustering method: k_means, random or hdbscan
# 			%3 number of clusters
# 			%4 the initial idx of the tables (usually 0) 
#===============================================================

CURRENT_PATH=`pwd`

PYTHON_PROJECT_PATH=/home/siduser/cbobed/git/PartMining
SLIM_PROJECT_PATH=/home/siduser/cbobed/krimp/slim
DATASETS_PATH=/home/siduser/cbobed/git/PartMining
OUTPUT_SPLITTED_PATH="$PYTHON_PROJECT_PATH"/output_databases

#configuration of the first script to obtain the vectors 
DIMENSION=50
WIN_SIZE=5
EPOCHS=10
WORKERS=4


# configuration of the second script to split the database_name
# k_means , random
CLUSTERING=$2
GRANULARITY=transaction
NUM_CLUSTERS=$3
# set NORMALIZE to -normalize if we want to normalize the vectors
NORMALIZE=
PRUNING_THRESHOLD=0

# configuration of the third script
# set ALL_RATIOS to -all_ratios to calculate the partial ratios
ALL_RATIOS=-all_ratios
MERGE_METHOD=naive

OUTPUT_FILE="$1"-"$2"-"$3"-output.out
ERR_FILE="$1"-"$2"-"$3"-output.err
TIME_FILE="$1"-"$2"-"$3"-output.time

# clean the outputs 
echo "" > "$OUTPUT_FILE"
echo "" > "$ERR_FILE"
echo "" > "$TIME_FILE"

# %1 is the filename of the dataset
cd $PYTHON_PROJECT_PATH

./calculateVocabSize.sh $1
./calculateEntropy.sh $1


if [[ $CLUSTERING != "random" ]]; then 
	echo "calculate vectors ..." > "$TIME_FILE"
	{ time ./calculateVectors.sh $1 $WIN_SIZE $DIMENSION $EPOCHS $WORKERS >> "$OUTPUT_FILE" 2>>"$ERR_FILE" ; } 2>> "$TIME_FILE"
fi

# we should now have database_name+'_DIMENSION_WIN_EPOCHS_sg.vect' as name of the model
MODEL_FILE="$1"_"$DIMENSION"_"$WIN_SIZE"_"$EPOCHS"_sg.vect
echo $MODEL_FILE

echo "split database ... " >> "$TIME_FILE"
{ time ./splitDatabase.sh $1 $MODEL_FILE $CLUSTERING $GRANULARITY $NUM_CLUSTERS $NORMALIZE >> "$OUTPUT_FILE" 2>>"$ERR_FILE" ; } 2>>"$TIME_FILE"

# depending on the granularity we can have different names

#Transactions: we should have in output_databases => 
#  dbBasename_GRANULARITY_CLUSTERING_DIMENSIONd_kNUM_CLUSTERS_[True|False]Norm * 

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

cp "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME"* $SLIM_PROJECT_PATH
cd $SLIM_PROJECT_PATH

for db in "$SPLITTED_BASENAME"*.dat; do 
	LOCAL_BASENAME=${db/.dat/}
	
	echo "mining $LOCAL_BASENAME ... " >> "$PYTHON_PROJECT_PATH"/"$TIME_FILE"
	{ time ./obtainCT-SLIM2012.sh $LOCAL_BASENAME >> "$PYTHON_PROJECT_PATH"/"$OUTPUT_FILE" 2>>"$PYTHON_PROJECT_PATH"/"$ERR_FILE" ; } 2>>"$PYTHON_PROJECT_PATH"/"$TIME_FILE"
	# now, in LOCAL_BASENAME-output we have the codetable and the analysis file
	cp "$LOCAL_BASENAME"-output/ct-latest.ct "$OUTPUT_SPLITTED_PATH"/"$LOCAL_BASENAME".ct
	cp "$LOCAL_BASENAME"-output/"$LOCAL_BASENAME".db.analysis.txt "$OUTPUT_SPLITTED_PATH"
	tar -zcf "$OUTPUT_SPLITTED_PATH"/"$LOCAL_BASENAME"-results.tar.gz "$LOCAL_BASENAME"-output
	rm -fr "$LOCAL_BASENAME"-output
	rm "$LOCAL_BASENAME"*
done 

echo going back to $PYTHON_PROJECT_PATH
cd $PYTHON_PROJECT_PATH

for db in "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME"*.dat; do 
	./calculateVocabSize.sh $db
	./calculateAdjustedEntropy.sh $db $1
done

ACTUAL_NUM_CLUSTER=0
for db in "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME"*.dat; do 
	(( ACTUAL_NUM_CLUSTER = ACTUAL_NUM_CLUSTER + 1 ))
done 

# $4 is going to be the initial index 
echo We have "$ACTUAL_NUM_CLUSTER" clusters
echo "calculating merged ratio ..." >> "$TIME_FILE"
{ time ./calculateMergedRatio.sh $1 "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME" "$ACTUAL_NUM_CLUSTER" $4 "$PRUNING_THRESHOLD" "$MERGE_METHOD" "$ALL_RATIOS" >> "$OUTPUT_FILE" 2>>"$ERR_FILE" ; } 2>>"$TIME_FILE"

cd "$CURRENT_PATH"
