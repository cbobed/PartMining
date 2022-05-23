#!/bin/bash 
DATA_STORAGE=datStorage
for i in `ls "$1"/*.dat`; do 
	BASENAME_DATABASE=`basename $i`
	ORIGINAL_DATABASE=${BASENAME_DATABASE%%_*}
	echo processing "$i" -- "$ORIGINAL_DATABASE".dat
	./calculateAdjustedEntropy.sh $i "$DATA_STORAGE"/"$ORIGINAL_DATABASE".dat 
done
