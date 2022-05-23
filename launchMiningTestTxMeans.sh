#!/bin/bash
METHODS="txmeans"
for i in *.dat; do 
	for method in $METHODS; do 
			echo processing $i - $method 
			./miningAndCompression.sh $i $method 
	done
done
