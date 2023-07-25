CURRENT_PATH=`pwd`

PYTHON_PROJECT_PATH=/home/siduser/cbobed/git/PartMining
TXMEANS_PROJECT_PATH=/home/siduser/cbobed/git/TX-Means
TXMEANS_PROJECT_OUTPUT_PATH=/home/siduser/cbobed/git/TX-Means/dataset
SLIM_PROJECT_PATH=/home/siduser/cbobed/krimp/slim
DATASETS_PATH=/home/siduser/cbobed/git/PartMining
OUTPUT_SPLITTED_PATH="$PYTHON_PROJECT_PATH"/tkmeansDat

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

cd $TXMEANS_PROJECT_PATH
{ time ./split.sh ${1/.dat/.csv} $2 >> "$PYTHON_PROJECT_PATH"/"$OUTPUT_FILE" 2>>"$PYTHON_PROJECT_PATH"/"$ERR_FILE" ; } 2>>"$PYTHON_PROJECT_PATH"/"$TIME_FILE"

SPLITTED_BASENAME="${1/.dat/}"_"$2"_
mv "$TXMEANS_PROJECT_OUTPUT_PATH"/"$SPLITTED_BASENAME"*.dat $OUTPUT_SPLITTED_PATH
cd $PYTHON_PROJECT_PATH

echo "processing $SPLITTED_BASENAME"
cp "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME"*.dat $SLIM_PROJECT_PATH
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
{ time ./calculateMergedRatio.sh $1 "$OUTPUT_SPLITTED_PATH"/"$SPLITTED_BASENAME" "$ACTUAL_NUM_CLUSTER" 0 0 "$MERGE_METHOD" "$ALL_RATIOS" >> "$OUTPUT_FILE" 2>>"$ERR_FILE" ; } 2>>"$TIME_FILE"

cd "$CURRENT_PATH"
