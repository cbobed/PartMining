#!/bin/bash
#METHODS="k_means random"
METHODS="k_means"
#CLUSTERS="4 8 16"
CLUSTERS="8 16"
#DATASETS="dbpedia201610PCB.dat"
DATASETS="genomes.dat"
#for i in *.dat; do 
for i in $DATASETS; do 
	for method in $METHODS; do 
		#for clusters in `seq 8 8 16`; do 
		for clusters in $CLUSTERS; do 
			echo processing $i - $method - $clusters 
			./completePipelineWSLFromDat.sh $i $method $clusters 0
		done
	done
done
