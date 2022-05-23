#!/bin/bash 
shuf $1 > ${1/.dat/}-shuffled.dat
split ${1/.dat/}-shuffled.dat -n l/$2 -d --additional-suffix=_k"$2".dat output_databases/"$3"_

for i in output_databases/"$3"*.dat; do 
	mv $i ${i/_clust_0/_clust_}
done 
