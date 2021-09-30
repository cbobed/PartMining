###############################################################################
# File: VocabularySize.py
# Author: Carlos Bobed
# Date: Sept 2021
# Comments: Script to calculate the vocabulary size of a database
# Modifications:
# Notes:
##############################################################################

import TransactionDatabase as tdb
import math
import os
import time
import ntpath
import argparse

if __name__ == "__main__":
    # params: -database filename of the database
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="file of the database")
    args=my_parser.parse_args()

    start_time = time.time()
    if (args.database_file.endswith('.db')):
        database_transactions = tdb.read_database_db(args.database_file)
    elif (args.database_file.endswith('.dat')):
        database_transactions = tdb.read_database_dat(args.database_file)

    ## dict to get all the item counts
    item_count = {}
    item_entropy = {}
    num_items = 0
    global_item_entropy = 0
    for t in database_transactions:
        for item in database_transactions[t]:
            if item not in item_count:
                item_count[item] = 0
            item_count[item] += 1
            num_items +=1

    print (len(item_count))