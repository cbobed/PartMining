python sid/PartMining/EntropyCalculator.py -database_file $1 -vocab_size `cat "$2"-vocabSize` -original_db_trans_size `cat "$2".transSize` -original_db_item_size `cat "$2".itemSize` > $1.entropy
