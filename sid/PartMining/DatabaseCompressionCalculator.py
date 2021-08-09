###############################################################################
# Author: Carlos Bobed
# Date: Jul 2021
# Comments: Code to merge codetables, translate them and use them to
#            to compress to be able to compare the results
#       NOTE: after analyzing the mined codes, they are interesting for
#           compression and structural comparison, but they might be not very
#           informative for the user. Important: we must consider
#           other merging options (for example, adopting the information matrix
#           from speeding up embeddings @ CIKM'21).
# Modifications:
###############################################################################

import math
import TransactionDatabase as tdb
import CodeTable as ct
import argparse
import time



## Methods to calculate the covers, support, usage

def calculate_cover(transaction, code_table):
    item_set = set(transaction)
    codes = []
    current_code = 0
    while (len(item_set) != 0 and current_code < len(code_table) ):
        aux_code_set = set(code_table[current_code]['code'])
        if (aux_code_set.issubset(item_set)):
            codes.append(current_code)
            item_set.difference_update(aux_code_set)
        current_code+=1
    return codes

# Reminder:
# Standard cover order
# |X|↓ suppD(X) ↓ lexicographically ↑
# Standard candidate order
# suppD(X) ↓|X|↓ lexicographically ↑

def calculate_transaction_cover(transaction, codetable):
    item_set = set(transaction)
    codes = []
    current_code = 0
    while (len(item_set) != 0 and current_code < len(codetable)):
        aux_code_set = set(codetable[current_code]['code'])
        if (aux_code_set.issubset(item_set)):
            codes.append(current_code)
            item_set.difference_update(aux_code_set)
        current_code += 1
    return codes


def calculate_codetable_support(database, codetable):
    # to speed up the calculations, we augment the codetable with the set version of the code
    for label in codetable:
        codetable[label]['code_set'] = set([int(item) for item in codetable[label]['code']])

    for trans in database:
        item_set = set([int(item) for item in database[trans]])
        ## we have to check all the codes in the code table
        ## this might be expensive ... we could just get the sum of the supports in the different databases
        ## note that this is additive so in a better implementation it wouldn't be a problem
        for label in codetable:
            ## if the intersection of the code is complete with the transaction
            if len(codetable[label]['code_set'].intersection(item_set)) == len(codetable[label]['code_set']):
                codetable[label]['support'] += 1


## Note that I cannot do it until I have the codetable
def calculate_codetable_usage(database, codetable):
    for label in codetable:
        codetable[label]['code_set'] = set([int(item) for item in codetable[label]['code']])

    for trans in database:
        remaining_item_set = set([int(item) for item in database[trans]])
        current_code = 0
        while len(remaining_item_set) != 0 and current_code < len(codetable):
            if len(codetable[current_code]['code_set'].intersection(remaining_item_set)) == len(
                    codetable[current_code]['code_set']):
                codetable[current_code]['usage'] += 1
                remaining_item_set = remaining_item_set - codetable[current_code]['code_set']
            current_code += 1

        if len(remaining_item_set) != 0:
            print('This codetable is not covering properly the database ... is the SCT added?')


def codetable_in_standard_cover_order(codetable):
    # we have to be careful with singleton codes (strings) ... if they have more than one char, they were
    # getting innerly sorted
    return {idx: {
        'code': sorted(codetable[label]['code']) if not isinstance(codetable[label]['code'], str) else codetable[label][
            'code'],
        'support': codetable[label]['support'],
        'usage': codetable[label]['usage']}
            for idx, label in enumerate(sorted(codetable.keys(), reverse=True,
                                               key=lambda x: (
                                               len(codetable[x]['code']) if not isinstance(codetable[x]['code'],
                                                                                           str) else 1
                                               , codetable[x]['support'])),
                                        start=0)}

def calculate_size_database_from_codetable(codetable):
    sum_usage = 0
    size = 0.0
    for label in codetable:
        sum_usage += codetable[label]['usage']
    for label in codetable:
        if (codetable[label]['usage'] != 0):
            num_bits = -math.log(codetable[label]['usage'] / sum_usage)
            size += codetable[label]['usage'] * num_bits
    return size

def prune_by_usage_threshold(codetable, threshold):
    return {i:{'code':codetable[i]['code'],
           'support':0,
           'usage':0,
           'code_set':codetable[i]['code_set']} for i in codetable if codetable[i]['usage'] > threshold or len(codetable[i]['code']) == 1}

if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="file of the database (must be the .dat)")

    ## argparse does not fully support subgroups, you have to do it with
    ## subparsers ... overkilling, I leave all the parameters in the wild living free
    ## the mutual exclusion is achieved by code exploring in this case

    ## First group :: calculate ratios merging :: everything is marked as not Required
    ## due to the exclusion, but we know this is not trueeee ... otherwise, it explodes
    my_parser.add_argument('-merge_codetables', action='store_true', required=False,
                           help="flag to tell that we are merging tables", default=False)
    ## REQUIRED
    my_parser.add_argument('-codetable_basename', action='store', required=False,
                               help="basename of the files of the codetables to be merged")
    ## REQUIRED
    my_parser.add_argument('-num_tables', action='store', type=int, required=False,
                               help="number of tables to be merged")
    my_parser.add_argument('-table_idx', action='store', type=int, required=False,
                               help='idx to start counting tables - hbscan sometimes starts at 0', default=0)
    ## REQUIRED
    my_parser.add_argument('-all_ratios', action='store_true', required=False,
                               help="calculate all the partial ratios, default: False", default=False)
    my_parser.add_argument('-pruning_threshold', action='store', type=int, required=False,
                           help="establish a threshold to prune some codes according to their usage", default=0)

    ## Second group :: calculate single ratios
    ## REQUIRED
    my_parser.add_argument('-analysis_file', action='store', required=False,
                       help="file with the analysis of the database")
    ## REQUIRED
    my_parser.add_argument('-codetable_file', action='store', required=False,
                           help="file with the code table to analyse the compression")

    args=my_parser.parse_args()
    if not args.merge_codetables:
        db_dat_table, dat_db_table = tdb.read_analysis_table_bidir(args.analysis_file)
        # we calculate the compression regarding the original .dat database
        # codetables are in Vreekens "space"
        codetable = ct.read_codetable(args.codetable_file, True)
        converted_codetable = ct.convert_int_codetable(codetable, db_dat_table)
        #converted should be in .dat space
        dat_database = tdb.read_database_dat(args.database_file)

        #converted_codetable = ct.merge_codetables([converted_codetable])
        calculate_codetable_support(dat_database, converted_codetable)
        converted_codetable_sco = codetable_in_standard_cover_order(converted_codetable)

        calculate_codetable_usage(dat_database, converted_codetable_sco)

        # we create the singleton code table
        sct_codetable = ct.build_SCT(dat_database)
        sct_codetable_sco = codetable_in_standard_cover_order(sct_codetable)
        ct_compressed_size = calculate_size_database_from_codetable(converted_codetable_sco)
        sct_compressed_size = calculate_size_database_from_codetable(sct_codetable_sco)

        ratio = ct_compressed_size / sct_compressed_size
        print(f'ratio: {ratio}')
    else:
        # we need to merge the tables and then calculate everything
        codetables = []

        for i in range(args.table_idx, args.num_tables+args.table_idx):
            current_name = args.codetable_basename+'_'+str(i)+'_k'+str(args.num_tables)
            print(f'processing {current_name}...')
            aux_db_dat_table, aux_dat_db_table = tdb.read_analysis_table_bidir(current_name + '.db.analysis.txt')
            aux_codetable = ct.read_codetable(current_name+'.ct', True)
            aux_converted_codetable = ct.convert_int_codetable(aux_codetable, aux_db_dat_table)
            codetables.append(aux_converted_codetable)

            if (args.all_ratios):
                aux_dat_database = tdb.read_database_dat(current_name+'.dat')

                calculate_codetable_support(aux_dat_database, aux_converted_codetable)
                aux_codetable_sco = codetable_in_standard_cover_order(aux_converted_codetable)
                calculate_codetable_usage(aux_dat_database, aux_codetable_sco)

                aux_sct_codetable = ct.build_SCT(aux_dat_database)
                aux_sct_codetable_sco = codetable_in_standard_cover_order(aux_sct_codetable)
                aux_size = calculate_size_database_from_codetable(aux_codetable_sco)
                aux_sct_size = calculate_size_database_from_codetable(aux_sct_codetable_sco)
                aux_ratio = aux_size / aux_sct_size
                print(f'Partition {i} ratio: {aux_ratio}')

        dat_database = tdb.read_database_dat(args.database_file)
        print(f'number of codetables: {len(codetables)}')
        for c in codetables:
            print(f'size: {len(c)}')
        converted_merged_codetable = ct.merge_codetables(codetables)
        print(f'merged table size: {len(converted_merged_codetable)}')
        calculate_codetable_support(dat_database, converted_merged_codetable)
        converted_merged_codetable_sco = codetable_in_standard_cover_order(converted_merged_codetable)
        calculate_codetable_usage(dat_database, converted_merged_codetable_sco)

        sct_codetable = ct.build_SCT(dat_database)
        sct_codetable_sco = codetable_in_standard_cover_order(sct_codetable)

        merged_size = calculate_size_database_from_codetable(converted_merged_codetable_sco)
        sct_size = calculate_size_database_from_codetable(sct_codetable_sco)
        merged_ratio = merged_size / sct_size
        print(f'merged size: {merged_size}')
        print(f'sct size: {sct_size}')
        print(f'merged ratio: {merged_ratio}')

        if args.pruning_threshold != 0:
            pruned_merged_codetable = prune_by_usage_threshold(converted_merged_codetable_sco, args.pruning_threshold)
            calculate_codetable_support(dat_database, pruned_merged_codetable)
            pruned_merged_codetable_sco = codetable_in_standard_cover_order(pruned_merged_codetable)
            calculate_codetable_usage(dat_database, pruned_merged_codetable_sco)
            pruned_merged_size = calculate_size_database_from_codetable(pruned_merged_codetable_sco)
            pruned_merged_ratio = pruned_merged_size / sct_size
            print(f'pruned_merged_ratio:{pruned_merged_ratio}')