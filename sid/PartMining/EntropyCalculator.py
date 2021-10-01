###############################################################################
# File: EntropyCalculator.py
# Author: Carlos Bobed
# Date: Sept 2021
# Comments: Program to calculate the global entropy of the items in the database
#       Inspired by binwalk and the way it calculates the entropy of a file
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
    my_parser.add_argument('-vocab_size', action='store', required=False, type=int,
                           help="original vocab size")
    args=my_parser.parse_args()

    start_time = time.time()
    if (args.database_file.endswith('.db')):
        database_transactions = tdb.read_database_db(args.database_file)
    elif (args.database_file.endswith('.dat')):
        database_transactions = tdb.read_database_dat(args.database_file)
    print(f'Database loaded in {time.time() - start_time} s.')

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

    if args.vocab_size is not None:
        adjusted_vocab_size = args.vocab_size
    else:
        adjusted_vocab_size = len(item_count)
    for item in item_count:
        p_x = float(item_count[item]) / num_items
        item_entropy[item] = -p_x * math.log(p_x,2) ## in fact would be the code length
        global_item_entropy += item_entropy[item]

    # we have to normalize the value using the maixmum diversity index (in this case, log_2 (len(item_count))
    normalized_global_item_entropy = global_item_entropy / math.log(len(item_count), 2)
    adjusted_normalized_global_item_entropy = global_item_entropy / math.log(adjusted_vocab_size, 2)

    length_normalized_transaction_entropy = {}
    avg_length_normalized_transaction_entropy = 0
    for t in database_transactions:
        length_normalized_transaction_entropy[t] = 0
        for item in database_transactions[t]:
            length_normalized_transaction_entropy[t] += item_entropy[item]
        length_normalized_transaction_entropy[t] /= float(len(database_transactions[t]))
        avg_length_normalized_transaction_entropy += length_normalized_transaction_entropy[t]
    avg_length_normalized_transaction_entropy /= float(len(database_transactions))

    print(f'vocab size: {len(item_count)}')
    print(f'adjusted vocab size: {adjusted_vocab_size}')
    print('-----------------------')
    print(f'global item entropy: {global_item_entropy}')
    print(f'normalized global item entropy {normalized_global_item_entropy}')
    print(f'adjusted normalized global item entropy {adjusted_normalized_global_item_entropy}')
    print('***********************')
    print(f'average length normalized transaction entropy: {avg_length_normalized_transaction_entropy}')
    print('-----------------------')
