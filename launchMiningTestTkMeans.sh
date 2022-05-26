#!/bin/bash
METHODS="tkmeans"
DATASETS="heart.dat" 
for i in *.dat; do 
#for i in $DATASETS; do
	for method in $METHODS; do 
			echo processing $i - $method 
			./miningAndCompressionTkmeans.sh $i $method 
	done
done
