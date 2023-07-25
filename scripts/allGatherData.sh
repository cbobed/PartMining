#!/bin/bash 
DATASET_DIR=../../../datasets
for i in `ls -d batch*`; do 
	cp gatherData.sh $i
	cd $i
	for j in `ls "$DATASET_DIR"/*.dat`; do 
		FILENAME=`basename $j`
		./gatherData.sh $FILENAME
	done
	cd ..
done
