###############################################################################
# File: TableVocabularySizeComparator.py
# Author: Carlos Bobed
# Date: Sept 2021
# Comments: Script to calculate the vocabulary size of a codetable in .dat format
#       and check the missing elements in the associated database
# Modifications:
# Notes:
##############################################################################

import CodeTable as ct
import TransactionDatabase as tdb
import math
import os
import time
import ntpath
import argparse

if __name__ == "__main__":
    # params: -database filename of the database
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-codetable_file', action='store', required=True,
                           help="file of the codetable")
    my_parser.add_argument('-database_file', action='store', required=True,
                        help="file of the database")
    args=my_parser.parse_args()

    start_time = time.time()
    codetable = ct.read_codetable_dat_format(args.codetable_file)
    database_transactions = tdb.read_database_dat(args.database_file)
    print(f'{len(codetable)}')

    ## dict to get all the item counts
    item_count = {}
    num_items = 0
    global_item_entropy = 0
    for t in codetable:
        for item in codetable[t]['code']:
            if item not in item_count:
                item_count[item] = 0
            item_count[item] += 1
            num_items +=1

    print (f'items in codetable: {len(item_count)}')

    missing_items = set()
    db_item_count = {}
    for t in database_transactions:
        for item in database_transactions[t]:
            if item not in item_count:
                missing_items.add(item)
            if item not in db_item_count:
                db_item_count[item] = 0
            db_item_count[item] +=1

    print(f'items in db not in codetable: {len(missing_items)}')
    missing_db_items = set()
    for item in item_count:
        if item not in db_item_count:
            missing_db_items.add(item)
    print(f'items in codetable not in db: {len(missing_db_items)}')
