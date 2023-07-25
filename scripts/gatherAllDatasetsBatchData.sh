#!/bin/bash 

## This script must be in the root directory of the batch results and 
## relies on having gatherData.sh in the same directory

## $1 is the directory where the datasets .dat are 
## and where the .entropy files MUST be already 
## $2 is the number of batches to be processed
## $3 is the dimension of the vectors 

for CURRENT_BATCH in `seq 1 $2`; do 
	cp gatherData.sh batch-"$CURRENT_BATCH"
	cd batch-"$CURRENT_BATCH"
	for CURRENT_DATASET in `ls $1/*.dat`; do 
		ln -s "$CURRENT_DATASET".entropy . 
		./gatherData.sh `basename "$CURRENT_DATASET"` $3 
	done 
	cd .. 
done 

