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
import args
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


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="file of the database (must be the .dat)")

    mut_group = my_parser.add_mutual_exclusive_group(required=True)
    several_group = mut_group.add_argument_group('several codetables')
    several_group.add_argument('-merge_codetables', action='store_true', required=False,
                           help="flag to tell that we are merging tables", default=False)
    several_group.add_argument('-codetable_basename', action='store', required=True,
                               help="basename of the files of the codetables to be merged")
    several_group.add_argument('-num_tables', action='store', type=int, requited=True,
                               help="number of tables to be merged", required=True)
    several_group.add_argument('-table_idx', action='store', type=int, required=False,
                               help='idx to start counting tables - hbscan sometimes starts at 0', default=0)
    several_group.add_argument('-all_ratios', action='store_true', required=True,
                               help="calculate all the partial ratios, default: False", default=False)
    single_group = mut_group.add_argument_group('single codetable')
    single_group.add_argument('-analysis_file', action='store', required=True,
                       help="file with the analysis of the database")
    single_group.add_argument('-codetable_file', action='store', required=True,
                           help="file with the code table to analyse the compression")

    args=my_parser.parse_args()
    if not args.merge_codetables:
        db_dat_table, dat_db_table = ct.read_analysis_table_bidir(args.analysis_file)
        # we calculate the compression regarding the original .dat database
        codetable = ct.read_codetable(args.codetable_file, True)
        converted_codetable = ct.convert_int_codetable(codetable, db_dat_table)
        dat_database = tdb.read_database_dat(args.database_file)

        #some checks to compare to the notebook
        print(len(converted_codetable))
        print(converted_codetable[0])
        print(codetable[0])

        #converted_orig_codetable = ct.merge_codetables([converted_codetable])
        calculate_codetable_support(dat_database, converted_codetable)
        converted_codetable_sco = codetable_in_standard_cover_order(converted_codetable)

        # some checks to compare to the notebook
        print(len(converted_codetable))
        print(converted_codetable['0_1'])
        print(converted_codetable_sco[0])

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
            aux_db_dat_table, aux_dat_db_table = tdb.read_analysis_table_bidir(current_name + '.db.analysis.txt')
            aux_codetable = ct.read_codetable(current_name, True)
            aux_converted_codetable = ct.convert_int_codetable(aux_codetable, aux_db_dat_table)
            codetables.append(aux_converted_codetable)

            if (args.all_ratios):
                aux_dat_database = tdb.read_database_dat(args.current_name+'.dat')
                calculate_codetable_support(aux_dat_database, aux_codetable)
                aux_codetable_sco = codetable_in_standard_cover_order(aux_codetable)
                aux_sct_codetable = ct.build_SCT(aux_dat_database)
                aux_sct_codetable_sco = codetable_in_standard_cover_order(aux_sct_codetable)
                aux_size = calculate_size_database_from_codetable(aux_codetable_sco)
                aux_sct_size = calculate_size_database_from_codetable(aux_sct_codetable_sco)
                aux_ratio = aux_size / aux_sct_size
                print(f'Partition {i} ratio: {aux_ratio}')

        dat_database = tdb.read_database_dat(args.database_file)
        converted_merged_codetable = ct.merge_codetables(codetables)

        calculate_codetable_support(dat_database, converted_merged_codetable)
        converted_merged_codetable_sco = codetable_in_standard_cover_order(converted_merged_codetable)

        sct_codetable = ct.build_SCT(dat_database)
        sct_codetable_sco = codetable_in_standard_cover_order(sct_codetable)

        merged_size = calculate_size_database_from_codetable(converted_merged_codetable_sco)
        sct_size = calculate_size_database_from_codetable(sct_codetable_sco)
        merged_ratio = merged_size / sct_size
        print(f'merged ratio: {merged_ratio}')