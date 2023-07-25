#!/bin/bash
#METHODS="k_means random"
METHODS="random"
#DATASETS="dbpedia201610PCB.dat  dbpedia36PCB.dat"
DATASETS="dbpedia201610PCB.dat"
for i in $DATASETS; do 
	for method in $METHODS; do 
		for clusters in `seq 8 8 16`; do 
			echo processing $i - $method - $clusters 
			./completePipelineWSLFromDatModifiedSLIM.sh $i $method $clusters 0
		done
	done
done
