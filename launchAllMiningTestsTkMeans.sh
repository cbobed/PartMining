#!/bin/bash 

OUTPUT_DIR=tkmeans_batch_results
RESULTS_DATABASES_DIR=tkmeansDat

mkdir $OUTPUT_DIR
rm "$RESULTS_DATABASES_DIR"/*
for BATCH_ID in `seq 1 1 5`; do 
	./launchMiningTestTkMeans.sh 
	mkdir "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv "$RESULTS_DATABASES_DIR"/* "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *.out "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *.err "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *.time "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *-vocabSize "$OUTPUT_DIR"/batch-"$BATCH_ID"
done
