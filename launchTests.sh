#!/bin/bash
METHODS="k_means random"
for i in *.dat; do 
	for method in $METHODS; do 
		for clusters in `seq 8 8 16`; do 
			echo processing $i - $method - $clusters 
			./completePipelineWSLFromDat.sh $i $method $clusters 0
		done
	done
done
