#!/bin/bash 
for f in `find ./ -name '*.out'`; do 
	grep 'merged table size without non-used codes:\|merged ratio:\|-- MERGING' $f > ${f%.*}.curated
	grep 'merge accepted' $f | wc -l >> ${f%.*}.curated
	grep 'merge rejected' $f | wc -l >> ${f%.*}.curated
done