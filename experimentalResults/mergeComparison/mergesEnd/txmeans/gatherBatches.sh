#!/bin/bash
DATASET="adult.dat chessBig.dat connect.dat letrecog.dat pendigits.dat"
METHOD=txmeans
CLUSTERS="4"
OUTPUT_FILENAME="txmeans.csv"

for d in $DATASET; do 
	echo $d >> $OUTPUT_FILENAME
	echo clusters';'naiveCodes';'naiveRatio';'naivePlusCodes';'naivePlusRatio';'informedCodes';'informedRatio';'informedAccepted';'informedRejected >> $OUTPUT_FILENAME
	for c in $CLUSTERS; do 
		for i in `seq 1 1 5`; do 
			FILENAME=batch-"$i"/"$d"-"$METHOD"-"$c"-output-merged.curated
			echo processing $FILENAME
			NAIVE_CODES=`head -2 $FILENAME | tail -1 | awk '{ print $7; }'`
			NAIVE_RATIO=`head -3 $FILENAME | tail -1 | awk '{ print $3; }'`
			NAIVE_PLUS_CODES=`head -5 $FILENAME | tail -1 | awk '{ print $7; }'`
			NAIVE_PLUS_RATIO=`head -6 $FILENAME | tail -1 | awk '{ print $3; }'`
			INFORMED_CODES=`head -8 $FILENAME | tail -1 | awk '{ print $7; }'`
			INFORMED_RATIO=`head -9 $FILENAME | tail -1 | awk '{ print $3; }'`
			INFORMED_ACCEPTED=`head -10 $FILENAME | tail -1`
			INFORMED_REJECTED=`tail -1 $FILENAME`
			echo "$c"';'"$NAIVE_CODES"';'"$NAIVE_RATIO"';'"$NAIVE_PLUS_CODES"';'"$NAIVE_PLUS_RATIO"';'"$INFORMED_CODES"';'"$INFORMED_RATIO"';'"$INFORMED_ACCEPTED"';'"$INFORMED_REJECTED" >> $OUTPUT_FILENAME
		done
	done
done