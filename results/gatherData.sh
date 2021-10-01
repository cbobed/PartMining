NUM_CLUSTERS="4 8"
METHODS="k_means random"


new_line(){
	echo "" >> $1
}

output () {

	echo $1 - $2 - $3 
	echo $1 ";" $2 >> $3
}

CSV_FILE="$1"-info.csv
VOCAB_SIZE=`cat "$1"-vocabSize`
FILE_ENTROPY=`head -6 "$1".entropy | tail -1 |awk '{ print $5}'`
FILE_NORMAL_ENTROPY=`head -7 "$1".entropy | tail -1 |awk '{ print $6}'`

> $CSV_FILE

output "vocabSize" "$VOCAB_SIZE" "$CSV_FILE"
output "fileEntropy" "$FILE_ENTROPY" "$CSV_FILE"
output "fileNormalEntropy" "$FILE_NORMAL_ENTROPY" "$CSV_FILE"

for N in $NUM_CLUSTERS; do 
	for M in $METHODS; do 
		new_line "$CSV_FILE" 
		output "info $N clusters $M method" "NA" "$CSV_FILE"
		TIME_FILE="$1"-"$M"-"$N"-output.time
		OUTPUT_FILE="$1"-"$M"-"$N"-output.out 
		ratios=(`cat $OUTPUT_FILE | grep ratio | awk ' { if ($1 == "Partition") {print $4; } else {print $3; }} ' `)

		(( POS_MERGED = ${#ratios[@]} - 1 ))
		
		if [[ $M != "random" ]]; then 
			SPLIT_DATABASE_LINE=10			
			VECTOR_REAL_TIME=`head -5 "$TIME_FILE" | head -3 | tail -1 | awk '{print $2; }'`
			VECTOR_USER_TIME=`head -5 "$TIME_FILE" | head -4 | tail -1 | awk '{print $2; }'`
		else
			SPLIT_DATABASE_LINE=6
		fi
		
		SPLIT_DATABASE_REAL_TIME=`head -$SPLIT_DATABASE_LINE "$TIME_FILE" | tail -5 | head -3 | tail -1 | awk '{print $2; }'`
		SPLIT_DATABASE_USER_TIME=`head -$SPLIT_DATABASE_LINE "$TIME_FILE" | tail -5 | head -4 | tail -1 | awk '{print $2; }'`
		
		MINING_REAL_TIME=()
		MINING_USER_TIME=() 
		
		PART_VOCAB_SIZES=() 
		PART_ADJUSTED_VOCAB=()
		PART_ITEM_ENTROPY=()
		PART_NORM_ITEM_ENTROPY=() 
		
		for (( COUNT=0; COUNT < N; COUNT++ )) 
		do	
			(( HEAD_OFFSET_MINING = SPLIT_DATABASE_LINE + 5 * (COUNT + 1) )) 
			if [[ `head -$HEAD_OFFSET_MINING "$TIME_FILE" | tail -5 | head -1 | awk '{print $1;}'` = "mining" ]]; then 
				
				MINING_REAL_TIME+=( `head -$HEAD_OFFSET_MINING "$TIME_FILE" | tail -5 |  head -3 | tail -1 | awk '{print $2; }'` ) 
				MINING_USER_TIME+=( `head -$HEAD_OFFSET_MINING "$TIME_FILE" | tail -5 |  head -4 | tail -1 | awk '{print $2; }'` ) 
				
				## We have to gather the vocabSize and the entropy of each subpartition
				
				if [[ $M = "random" ]]; then 
					PART_FILENAME="${1/.dat/}"_transaction_"$M"_200d_k"$N"_FalseNorm_rand_clust_"$COUNT"_k"$N".dat.entropy
				else 
					PART_FILENAME="${1/.dat/}"_transaction_"$M"_200d_k"$N"_FalseNorm_trans_clust_"$COUNT"_k"$N".dat.entropy
				fi
				
				PART_VOCAB_SIZES+=( `head -2 "$PART_FILENAME" | tail -1 | awk '{ print $3; }'` ) 
				PART_ADJUSTED_VOCAB+=( `head -3 "$PART_FILENAME" | tail -1 | awk '{ print $4; }'` ) 
				PART_ITEM_ENTROPY+=( `head -6 "$PART_FILENAME" | tail -1 | awk '{ print $4; }'` )
				PART_NORM_ITEM_ENTROPY+=( `head -7 "$PART_FILENAME" | tail -1 | awk '{ print $6; }'` )
				
			else 
				## We are dealing prematurely with the merged Ratio 
				
				MERGED_RATIO_REAL_TIME=`head -$HEAD_OFFSET_MINING "$TIME_FILE" | tail -5 |  head -3 | tail -1 | awk '{print $2; }'`
				MERGED_RATIO_USER_TIME=`head -$HEAD_OFFSET_MINING "$TIME_FILE" | tail -5 |  head -4 | tail -1 | awk '{print $2; }'`
			fi
			echo finishing ... 
		done
		if [ -z ${MERGED_RATIO_REAL_TIME+x} ]; then
			(( HEAD_OFFSET_MERGE = SPLIT_DATABASE_LINE + 5 * M )) 
			MERGED_RATIO_REAL_TIME=`head -$HEAD_OFFSET_MINING "$TIME_FILE" | tail -5 |  head -3 | tail -1 | awk '{print $2; }'`
			MERGED_RATIO_USER_TIME=`head -$HEAD_OFFSET_MINING "$TIME_FILE" | tail -5 |  head -4 | tail -1 | awk '{print $2; }'`
		fi
		## We print the information in the associated csv file (No headers) 
		
		new_line "$CSV_FILE"
		output "Vector Times" "--" "$CSV_FILE" 
		
		if [[ $M != "random" ]]; then 
			output "vector real time" "$VECTOR_REAL_TIME" "$CSV_FILE"
			output "vector user time" "$VECTOR_USER_TIME" "$CSV_FILE"
		else 
			output "vector real time" "NA" "$CSV_FILE"
			output "vector user time" "NA" "$CSV_FILE"
		fi 
		
		new_line "$CSV_FILE"
		output "Split Times" "--" "$CSV_FILE" 
		output "split real time" "$SPLIT_DATABASE_REAL_TIME" "$CSV_FILE"
		output "split user time" "$SPLIT_DATABASE_USER_TIME" "$CSV_FILE"
		
		new_line "$CSV_FILE" 
		output "Merging Times script testing " "--" "$CSV_FILE" 
		output "merged real time" "$MERGED_RATIO_REAL_TIME" "$CSV_FILE" 
		output "merged user time" "$MERGED_RATIO_USER_TIME" "$CSV_FILE" 
		
		new_line "$CSV_FILE"
		output "Ratios" "--" "$CSV_FILE" 
		for (( COUNT=0; COUNT < (${#ratios[@]} - 1); COUNT++ )); 
		do 	
			echo ${ratios[$COUNT]}
			output "part $COUNT" ${ratios[$COUNT]} "$CSV_FILE"
		done 
		output "merged" ${ratios[$POS_MERGED]} "$CSV_FILE" 

		output "Mining Times" "--" "$CSV_FILE" 
		for (( COUNT=0; COUNT < ${#MINING_REAL_TIME[@]}; COUNT++)); 
		do 
			output "Partition $COUNT real time" ${MINING_REAL_TIME[$COUNT]} "$CSV_FILE"
		done 	
		new_line "$CSV_FILE" 
		for (( COUNT=0; COUNT < ${#MINING_USER_TIME[@]}; COUNT++)); 
		do 
			output "Partition $COUNT user time" ${MINING_USER_TIME[$COUNT]} "$CSV_FILE"
		done
		
		new_line "$CSV_FILE"
		output "Partition info" "--" "$CSV_FILE" 
		for (( COUNT=0; COUNT < ${#PART_VOCAB_SIZES[@]}; COUNT++)); 
		do 
			new_line "$CSV_FILE"
			output "partition $COUNT" "++" "$CSV_FILE" 
			output "vocabSize" ${PART_VOCAB_SIZES[$COUNT]} "$CSV_FILE"
			output "adjustedVocab" ${PART_ADJUSTED_VOCAB[$COUNT]} "$CSV_FILE"
			output "entropy" ${PART_ITEM_ENTROPY[$COUNT]} "$CSV_FILE"
			output "normEntropy" ${PART_NORM_ITEM_ENTROPY[$COUNT]} "$CSV_FILE"
		
		done 
				
	done 
done