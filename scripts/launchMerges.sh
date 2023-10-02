#!/bin/bash
DATASETS="adult.dat chessBig.dat connect.dat letrecog.dat pendigits.dat"
METHODS="k_means"
SIZES="4 8 16"
for i in $DATASETS; do
	for method in $METHODS; do  
		for clusters in $SIZES; do 
			echo processing $i - $method - $clusters 
			echo $i $method $clusters 0 $1 $2
			./mergeMethodsComparison.sh $i $method $clusters 0 $1 $2
			rm tmp_split_*.dat
		done
	done
done
