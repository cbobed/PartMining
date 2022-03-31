#!/bin/bash 

OUTPUT_DIR=batch_results
RESULTS_DATABASES_DIR=output_databases

mkdir $OUTPUT_DIR
rm "$RESULTS_DATABASES_DIR"/*
for BATCH_ID in `seq 1 1 1`; do 
	./launchTests.sh 
	mkdir "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv "$RESULTS_DATABASES_DIR"/* "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *.vect-times "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *.out "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *.err "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *.time "$OUTPUT_DIR"/batch-"$BATCH_ID"
	mv *-vocabSize "$OUTPUT_DIR"/batch-"$BATCH_ID"
	rm *.vect*
done
