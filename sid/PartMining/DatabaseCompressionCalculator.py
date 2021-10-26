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
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
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

    my_parser.add_argument('-parallel', action='store_true', required=False,
                           help="flag to use the parallel version of calculating support and usage", default=False)
    my_parser.add_argument('-conservative_parallelization', action='store_true', required=False,
                           help="flag to only use two processors in the big tables", default=False)
    ## REQUIRED
    my_parser.add_argument('-num_tables', action='store', type=int, required=False,
                               help="number of tables to be merged")
    my_parser.add_argument('-table_idx', action='store', type=int, required=False,
                               help='idx to start counting tables - hbscan sometimes starts at 0', default=0)
    my_parser.add_argument('-merge_method', action='store', choices=['naive', 'pruning'], required=False,
                           help="method to be applied to merge the code tables, default: naive", default='naive')
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
    start_time = time.time()
    if not args.merge_codetables:
        db_dat_table, dat_db_table = tdb.read_analysis_table_bidir(args.analysis_file)
        # we calculate the compression regarding the original .dat database
        # codetables are in Vreekens "space"
        codetable = ct.read_codetable(args.codetable_file, True)
        converted_codetable = ct.convert_int_codetable(codetable, db_dat_table)
        #converted should be in .dat space
        dat_database = tdb.read_database_dat(args.database_file)

        #converted_codetable = ct.merge_codetables([converted_codetable])
        if args.conservative_parallelization:
            ct.calculate_codetable_support(dat_database, converted_codetable, args.parallel, 2)
        else:
            ct.calculate_codetable_support(dat_database, converted_codetable, args.parallel)
        converted_codetable_sco = ct.codetable_in_standard_cover_order(converted_codetable)

        if args.conservative_parallelization:
            ct.calculate_codetable_usage(dat_database, converted_codetable_sco, args.parallel, 2)
        else:
            ct.calculate_codetable_usage(dat_database, converted_codetable_sco, args.parallel)

        # we create the singleton code table
        sct_codetable = ct.build_SCT(dat_database, False)
        sct_codetable_sco = ct.codetable_in_standard_cover_order(sct_codetable)
        ct_compressed_size = ct.calculate_size_database_from_codetable(converted_codetable_sco)
        sct_compressed_size = ct.calculate_size_database_from_codetable(sct_codetable_sco)

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

            if (args.all_ratios or args.merge_method=='pruning'):
                # we need to calculate the local supports and usages
                aux_dat_database = tdb.read_database_dat(current_name + '.dat')

                ct.calculate_codetable_support(aux_dat_database, aux_converted_codetable, args.parallel)
                print(f'num codes: {len(aux_codetable)}')
                print(f'num codes with support 0: {len([x for x in aux_converted_codetable if aux_converted_codetable[x]["support"] == 0])}')
                for x in aux_converted_codetable:
                    if aux_converted_codetable[x]["support"] == 0:
                        print(f'code with support 0: {aux_converted_codetable[x]}')
                aux_codetable_sco = ct.codetable_in_standard_cover_order(aux_converted_codetable)
                ct.calculate_codetable_usage(aux_dat_database, aux_codetable_sco, args.parallel)
                print(f'num codes with usage 0: {len([x for x in aux_codetable_sco if aux_codetable_sco[x]["usage"] == 0])}')

                codetables.append(aux_codetable_sco)
            else:
                codetables.append(aux_converted_codetable)

            if (args.all_ratios):
                # This must be only done if we are calculating the ratios
                aux_sct_codetable = ct.build_SCT(aux_dat_database, False)
                aux_sct_codetable_sco = ct.codetable_in_standard_cover_order(aux_sct_codetable)
                aux_size = ct.calculate_size_database_from_codetable(aux_codetable_sco)
                aux_sct_size = ct.calculate_size_database_from_codetable(aux_sct_codetable_sco)
                aux_ratio = aux_size / aux_sct_size
                print(f'Partition {i} ratio: {aux_ratio}')

        dat_database = tdb.read_database_dat(args.database_file)
        print(f'number of codetables: {len(codetables)}')
        for c in codetables:
            print(f'size: {len(c)}')

        if args.merge_method == 'naive':
            converted_merged_codetable = ct.merge_codetables_naive(codetables)
        elif args.merge_method == 'pruning':
            converted_merged_codetable = ct.merge_codetables_pruning(codetables, dat_database)


        print(f'merged table size: {len(converted_merged_codetable)}')
        if args.conservative_parallelization:
            ct.calculate_codetable_support(dat_database, converted_merged_codetable, args.parallel, 2)
        else:
            ct.calculate_codetable_support(dat_database, converted_merged_codetable, args.parallel)
        converted_merged_codetable_sco = ct.codetable_in_standard_cover_order(converted_merged_codetable)
        if args.conservative_parallelization:
            ct.calculate_codetable_usage(dat_database, converted_merged_codetable_sco, args.parallel, 2)
        else:
            ct.calculate_codetable_usage(dat_database, converted_merged_codetable_sco, args.parallel)

        sct_codetable = ct.build_SCT(dat_database, False)
        sct_codetable_sco = ct.codetable_in_standard_cover_order(sct_codetable)

        merged_size = ct.calculate_size_database_from_codetable(converted_merged_codetable_sco)
        sct_size = ct.calculate_size_database_from_codetable(sct_codetable_sco)
        merged_ratio = merged_size / sct_size
        print(f'merged size: {merged_size}')
        print(f'sct size: {sct_size}')
        print(f'merged ratio: {merged_ratio}')

        if args.pruning_threshold != 0:
            pruned_merged_codetable = ct.prune_by_usage_threshold(converted_merged_codetable_sco, args.pruning_threshold)
            if args.conservative_parallelization:
                ct.calculate_codetable_support(dat_database, pruned_merged_codetable, args.parallel, 2)
            else:
                ct.calculate_codetable_support(dat_database, pruned_merged_codetable, args.parallel)

            pruned_merged_codetable_sco = ct.codetable_in_standard_cover_order(pruned_merged_codetable)
            if args.conservative_parallelization:
                ct.calculate_codetable_usage(dat_database, pruned_merged_codetable_sco, args.parallel, 2)
            else:
                ct.calculate_codetable_usage(dat_database, pruned_merged_codetable_sco, args.parallel)
            pruned_merged_size = ct.calculate_size_database_from_codetable(pruned_merged_codetable_sco)
            pruned_merged_ratio = pruned_merged_size / sct_size
            print(f'pruned_merged_ratio:{pruned_merged_ratio}')
    end = time.time()
    print(f'time elapsed: {end-start_time}')