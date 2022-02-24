#!/bin/bash
METHODS="k_means random"
for i in *.dat; do 
	for method in $METHODS; do 
		for clusters in `seq 4 4 8`; do 
			echo processing $i - $method - $clusters 
			./testFromGloveVectors.sh $i $method $clusters 0
		done
	done
done
