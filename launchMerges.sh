#!/bin/bash
METHODS="k_means"
for i in *.dat; do
	for method in $METHODS; do  
		for clusters in `seq 4 4 8`; do 
			echo processing $i - $method - $clusters 
			echo $i $method $clusters 0 $1 $2
			./mergeMethodsComparison.sh $i $method $clusters 0 $1 $2
			rm tmp_split_*.dat
		done
	done
done
