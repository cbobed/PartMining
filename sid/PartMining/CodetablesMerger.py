###############################################################################
# Author: Carlos Bobed
# Date: Jan 2022
# Comments: Code to merge codetables naively, translate and store them to be
#       used as input as candidates for subsequent KRIMP algorithm
# Modifications:
###############################################################################

import math
import TransactionDatabase as tdb
import CodeTable as ct
import argparse
import time
import logging

def is_len_ordered(table):
    for i in range(len(table)-1):
        if (len(table[i]["code_set"]) > 1):
            print(f'{len(table[i]["code_set"])} {len(table[i+1]["code_set"])}')
        if (len(table[i]['code_set'])<len(table[i+1]['code_set'])):
            return False
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    # my_parser.add_argument('-database_file', action='store', required=True,
    #                        help="file of the database (must be the .dat)")
    ## REQUIRED
    my_parser.add_argument('-codetable_basename', action='store', required=False,
                               help="basename of the files of the codetables to be merged")

    my_parser.add_argument('-parallel', action='store_true', required=False,
                           help="flag to use the parallel version of calculating support and usage", default=False)
    ## REQUIRED
    my_parser.add_argument('-num_tables', action='store', type=int, required=False,
                               help="number of tables to be merged")
    my_parser.add_argument('-table_idx', action='store', type=int, required=False,
                               help='idx to start counting tables - hbscan sometimes starts at 0', default=0)
    my_parser.add_argument('-merge_method', action='store', choices=['naive', 'pruning'], required=False,
                           help="method to be applied to merge the code tables, default: naive", default='naive')

    args=my_parser.parse_args()
    start_time = time.time()

    # we need to merge the tables and then calculate everything
    codetables = []

    for i in range(args.table_idx, args.num_tables+args.table_idx):
        current_name = args.codetable_basename+'_'+str(i)+'_k'+str(args.num_tables)
        print(f'processing {current_name}...')
        aux_db_dat_table, aux_dat_db_table = tdb.read_analysis_table_bidir(current_name + '.db.analysis.txt')
        aux_codetable = ct.read_codetable(current_name+'.ct', True)
        aux_converted_codetable = ct.convert_int_codetable(aux_codetable, aux_db_dat_table)
        singleton_set = set()
        for x in [code for code in aux_converted_codetable if len(aux_converted_codetable[code]['code_set']) == 1]:
            singleton_set.update(aux_converted_codetable[x]['code_set'])
        print(f'singleton size: {len(singleton_set)}')
        codetables.append({'codetable': aux_converted_codetable, 'singletons':singleton_set})
        print(f'is_ordered {is_len_ordered(aux_converted_codetable)}')

    # dat_database = tdb.read_database_dat(args.database_file)
    print(f'number of codetables: {len(codetables)}')
    for c in codetables:
        print(f'size: {len(c["codetable"])}')

    if args.merge_method == 'naive':
        converted_merged_codetable = ct.merge_codetables_naive_converted(codetables)
        converted_merged_codetable = ct.merge_codetables_naive(codetables)
    elif args.merge_method == 'pruning':
        converted_merged_codetable = ct.merge_codetables_pruning(codetables, dat_database)

    print(f'merged table size: {len(converted_merged_codetable)}')
    # ct.calculate_codetable_support(dat_database, converted_merged_codetable, args.parallel, args.parallel, reuse_files=False)
    # converted_merged_codetable_sco = ct.codetable_in_standard_cover_order(converted_merged_codetable)

    ct.store_codetable_dat(converted_merged_codetable, args.codetable_basename+"-KRIMPMerged.ct")
