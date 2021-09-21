###############################################################################
# File: CodeTable.py
# Author: Carlos Bobed
# Date: Dec 2020
# Comments: Factorized methods from the original notebooks related to the
#   management of code tables
#   not OO, should be refactorized
## TODO: the codes are lists of strings, thus the lexicographical order might be
##      altered regarding the actual int order. The calculations are not affected
##      as we work with sets and intersections, but it could be speeded up by using
##      ordered lists and use early fail exit
# Modifications:
##############################################################################

import copy
import math
import statistics
import argparse
import multiprocessing as mp
import TransactionDatabase as tdb
import time

import logging

# From Visualizing Notebook ... the horror, don't try this at home ...

## method to read for the Vreeken's codetable format
## we don't need it to be a generator
## we do label each code and honor the order in the code table (length, support, lexicographical)
## following Pierre's suggestion, we keep track of the codes and the transaction IDs
def read_codetable(filename, load_all):
    codes = {}
    label = 0
    with open(filename, mode='rt', encoding='UTF-8') as file:
        for line in file:
            item_line = list(filter(None, line.rstrip('\n').split(' ')))
            ## only_used => those codes whose usage is > 0
            ## we get the last token, check whether it ends with )
            ## then, we get exactly the contents and check whether the first
            ## component is different from 0
            if (item_line[-1].endswith(')')):
                usage,support = item_line[-1][1:-1].split(',')
                if (load_all or int(usage) != 0):
                    codes[label]={'code': item_line[:-1], 'usage':int(usage), 'support':int(support)}
                    label+=1
    return codes

def build_SCT(database):
    sct_codetable = {}
    for trans in database:
        for singleton in [int(item) for item in database[trans]]:

            if singleton not in sct_codetable:
                sct_codetable[singleton] = {'code': str(singleton), 'support': 0, 'usage': 0}
            sct_codetable[singleton]['usage'] = sct_codetable[singleton]['usage'] + 1
            sct_codetable[singleton]['support'] = sct_codetable[singleton]['support'] + 1
    return sct_codetable

def convert_int_codetable (codetable, analysis_table):
    ## we have to take into account that db.analysis seems to introduce the 0 item
    ## which should never be present in the vocabularies of .dat dabases (1 .. infinity)
    converted = {}
    for label in codetable:
        translated_code = [analysis_table[int(item)] for item in codetable[label]['code'] if analysis_table[int(item)] != 0]
        str_translated_code = [str(item) for item in translated_code]
        converted[label] = {'code': str_translated_code,
                            'code_int':translated_code,
                            'code_set':set(translated_code),
                            'usage':0,
                            'support':0}
    return converted

### Methods related to cover and calculate sizes of a database
## Methods to calculate the covers, support, usage

PARALLEL = False

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
        'usage': codetable[label]['usage'],
        'old_label': label}
            for idx, label in enumerate(sorted(codetable.keys(), reverse=True,
                                               key=lambda x: (
                                               len(codetable[x]['code']) if not isinstance(codetable[x]['code'],
                                                                                           str) else 1
                                               , codetable[x]['support'])),
                                        start=0)}

#PRE: codetable with the usages already calculated
##      This requires to calculate their support, to order the codetable in sco,
##       and to calculate the support
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



# TODO: Too many duplicated calculations, storing that info would save a lot of time
# We need the STC
# L(D,CT) = L (D|CT) + L(CT|D)
# L(D|CT) == calculate_size_database_from_codetable()
# L(CT|D) == \sum_{X \in CT:usage_D(X)!=0} (L(Code_ST(X)) + L(Code_CT(X))
def calculate_complete_size (codetable, standard_codetable):
    database_size = calculate_size_database_from_codetable(codetable)
    sum_usage_codetable = 0
    sum_usage_standard_codetable = 0
    sct_codelengths = {}
    for label in codetable:
        sum_usage_codetable += codetable[label]['usage']
    for label in standard_codetable:
        sum_usage_standard_codetable += standard_codetable[label]['usage']
    for label in standard_codetable:
        if standard_codetable[label]['usage'] != 0:
            sct_codelengths[label] = -math.log(standard_codetable[label]['usage'] / sum_usage_standard_codetable)
        else:
            sct_codelengths[label] = 0
    codetable_size = 0.0
    for label in codetable:
        if codetable[label]['usage'] != 0:
            codetable_size += -math.log(codetable[label]['usage'] / sum_usage_codetable)
            for item in codetable[label]['code']:
                codetable_size += sct_codelengths[item]
    print(f'database_size: {database_size}')
    print(f'codetable_size: {codetable_size}')
    print(f'complete: {database_size+codetable_size}')
    return database_size + codetable_size



def prune_by_usage_threshold(codetable, threshold):
    return {i:{'code':codetable[i]['code'],
           'support':0,
           'usage':0,
           'code_set':codetable[i]['code_set']} for i in codetable if codetable[i]['usage'] > threshold or len(codetable[i]['code']) == 1}



## naive way of merging the codetables
## for convenience we work here with integers (we kept the codetables as string tokens to be able to handle the vector models)
def merge_codetables_naive(codetables):
    merged = {}
    non_colision_labelbase = 0
    for ct in codetables:
        for label in ct:
            current_label = str(non_colision_labelbase) + '_' + str(label)
            merged[current_label] = ct[label]
        non_colision_labelbase += 1
    # we keep track of the codes that are duplicated
    to_omit = set()
    merged_key_list = list(merged.keys())
    for i in range(len(merged_key_list)):
        if merged_key_list[i] not in to_omit:
            for j in range(i + 1, len(merged_key_list)):
                if merged_key_list[j] not in to_omit:
                    # depending on how the table has been obtained it might or not have the code_set field
                    ## converted using the analysis table (convert_int_codetable) => it has
                    ## loaded from file => it hasn't
                    if 'code_set' in merged[merged_key_list[i]]:
                        set_i = merged[merged_key_list[i]]['code_set']
                    else:
                        set_i = set([int(item) for item in merged[merged_key_list[i]]['code']])
                    if 'code_set' in merged[merged_key_list[j]]:
                        set_j = merged[merged_key_list[j]]['code_set']
                    else:
                        set_j = set([int(item) for item in merged[merged_key_list[j]]['code']])
                    if set_i == set_j:
                        to_omit.add(merged_key_list[j])
    # we get rid of the duplicated entries in the codetable
    [merged.pop(code) for code in to_omit]

    for label in merged:
        if 'code_int' in merged[label]:
            merged[label]['code'] = [str(item) for item in merged[label]['code_int']]
        merged[label]['usage'] = 0
        merged[label]['support'] = 0

    return merged

## we merge the tables and we apply the KRIMP pruning after the merging to
## avoid possible local decisions that might hid different codes
## PRE: codetables with the support and the usages calculated
def merge_codetables_pruning(codetables, database):
    merged = {}
    non_colision_labelbase = 0
    sum_usage = 0
    for ct in codetables:
        sum_usage = 0
        for label in ct:
            current_label = str(non_colision_labelbase) + '_' + str(label)
            merged[current_label] = ct[label]
            sum_usage += ct[label]['usage']
        # we extend each code with their local codelength
        for label in ct:
            if ct[label]['usage'] > 0:
                ct[label]['code_length']= -math.log(ct[label]['usage'] / sum_usage)
            else:
                ct[label]['code_length'] = 0
        non_colision_labelbase += 1

    # we keep track of the codes that are duplicated
    to_omit = set()
    merged_key_list = list(merged.keys())
    for i in range(len(merged_key_list)):
        if merged_key_list[i] not in to_omit:
            for j in range(i + 1, len(merged_key_list)):
                if merged_key_list[j] not in to_omit:
                    # depending on how the table has been obtained it might or not have the code_set field
                    ## converted using the analysis table (convert_int_codetable) => it has
                    ## loaded from file => it hasn't
                    if 'code_set' in merged[merged_key_list[i]]:
                        set_i = merged[merged_key_list[i]]['code_set']
                    else:
                        set_i = set([int(item) for item in merged[merged_key_list[i]]['code']])
                    if 'code_set' in merged[merged_key_list[j]]:
                        set_j = merged[merged_key_list[j]]['code_set']
                    else:
                        set_j = set([int(item) for item in merged[merged_key_list[j]]['code']])
                    # if we have to omit jth element, we add its usage and support
                    # to do the microaverage
                    if set_i == set_j:
                        i_table, i_code = merged_key_list[i].split('_')
                        j_table, j_code = merged_key_list[j].split('_')

                        # We could use the mean of the usage proportions as well, reflexion on that is needed
                        if 'code_lengths_array' not in merged[merged_key_list[i]]:
                            merged[merged_key_list[i]]['code_lengths_array'] = [codetables[int(i_table)][int(i_code)]['code_length']]
                            merged[merged_key_list[i]]['dbs'] = 1

                        merged[merged_key_list[i]]['code_lengths_array'].append(codetables[int(j_table)][int(j_code)]['code_length'])
                        merged[merged_key_list[i]]['dbs'] += 1

                        to_omit.add(merged_key_list[j])

    # we get rid of the duplicated entries in the codetable
    [merged.pop(code) for code in to_omit]

    new_merged = copy.deepcopy(merged)
    for label in new_merged:
        if 'code_int' in new_merged[label]:
            new_merged[label]['code'] = [str(item) for item in new_merged[label]['code_int']]
        new_merged[label]['usage'] = 0
        new_merged[label]['support'] = 0
        new_merged[label]['code_length'] = 0
        if 'dbs' in new_merged[label]:
            new_merged[label].pop('code_lengths_array')
            new_merged[label].pop('dbs')



    ## To prune according to KRIMP, we need the previous supports and usages

    calculate_codetable_support(database, new_merged)
    print(f'{new_merged.keys()}')
    converted_new_merged_sco = codetable_in_standard_cover_order(new_merged)
    print(f'{converted_new_merged_sco.keys()}')
    calculate_codetable_usage(database, converted_new_merged_sco)

    sum_usage = 0
    for label in converted_new_merged_sco:
        sum_usage += converted_new_merged_sco[label]['usage']
    for label in converted_new_merged_sco:
        if converted_new_merged_sco[label]['usage'] > 0:
            converted_new_merged_sco[label]['code_length'] = -math.log(converted_new_merged_sco[label]['usage'] / sum_usage)
        else:
            converted_new_merged_sco[label]['code_length'] = 0

    # let's check how many have changed their code_lengths
    increased_length = 0
    equal_length = 0
    decreased_length = 0
    not_used_before = 0
    not_used_after = 0

    stored_info = {}
    for label in converted_new_merged_sco:
        prev_label = converted_new_merged_sco[label]['old_label']
        if 'dbs' in merged[prev_label]:
            print(f'{[x for x in merged[prev_label]["code_lengths_array"] if x != 0]}')
            if len([x for x in merged[prev_label]['code_lengths_array'] if x != 0]) != 0:
                code_length_before = statistics.mean([x for x in merged[prev_label]['code_lengths_array'] if x != 0])
            else:
                code_length_before = 0
        else:
            code_length_before = merged[prev_label]['code_length']
        if converted_new_merged_sco[label]['code_length'] != 0 and code_length_before != 0:
            if converted_new_merged_sco[label]['code_length'] > code_length_before:
                increased_length += 1
                stored_info[label] = {'diff': converted_new_merged_sco[label]['code_length']-code_length_before}
            elif converted_new_merged_sco[label]['code_length']< code_length_before:
                decreased_length += 1
            else:
                equal_length += 1
        else:
            if converted_new_merged_sco[label]['code_length'] == 0:
                not_used_after +=1
            if code_length_before == 0:
                not_used_before += 1

    print(f'increased_length :: {increased_length}')
    print(f'equal_length :: {equal_length}')
    print(f'decreased_length ::{decreased_length }')
    print(f'not_used_before :: {not_used_before}')
    print(f'not_used_after :: {not_used_after}')
    print(f'stored_info ::{[(x,stored_info[x]["diff"]) for x in sorted(stored_info.keys(), key=lambda x: stored_info[x]["diff"], reverse=True)]}')
    ## We leave a flag to avoid duplicated calculations (to be cleaned ... sometime, somewhere ...)

    print(converted_new_merged_sco.keys())
    print(f'before pruning: {calculate_size_database_from_codetable(converted_new_merged_sco)}')
    calculate_codetable_support(database, converted_new_merged_sco)
    new_new = codetable_in_standard_cover_order(converted_new_merged_sco)
    calculate_codetable_usage(database, new_new)
    print(f'after pruning: {calculate_size_database_from_codetable(new_new)}')

    # we have all the previous information about the codes in merged and the new in new_merged, we have to
    # prune new_merged according to KRIMP prune step

    return converted_new_merged_sco

if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="file of the database (must be the .dat)")
    my_parser.add_argument('-analysis_file', action='store', required=False,
                       help="file with the analysis of the database")

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
    my_parser.add_argument('-merge_method', action='store', choices=['naive', 'pruning'], required=False,
                           help="method to be applied to merge the code tables, default: naive", default='naive')

    args=my_parser.parse_args()

    # we need to merge the tables and then calculate everything
    codetables = []

    for i in range(args.table_idx, args.num_tables + args.table_idx):
        current_name = args.codetable_basename + '_' + str(i) + '_k' + str(args.num_tables)
        print(f'processing {current_name}...')
        aux_db_dat_table, aux_dat_db_table = tdb.read_analysis_table_bidir(current_name + '.db.analysis.txt')
        aux_codetable = read_codetable(current_name + '.ct', True)
        aux_converted_codetable = convert_int_codetable(aux_codetable, aux_db_dat_table)

        if (args.merge_method == 'pruning'):
            # we need to calculate the local supports and usages
            aux_dat_database = tdb.read_database_dat(current_name + '.dat')

            calculate_codetable_support(aux_dat_database, aux_converted_codetable)
            print(f'num codes: {len(aux_codetable)}')
            print(f'codes with support 0: {[x for x in aux_converted_codetable if aux_converted_codetable[x]["support"] == 0]}')
            aux_codetable_sco = codetable_in_standard_cover_order(aux_converted_codetable)
            calculate_codetable_usage(aux_dat_database, aux_codetable_sco)
            print(f'codes with usage 0: {[x for x in aux_codetable_sco if aux_codetable_sco[x]["usage"] == 0]}')

            codetables.append(aux_codetable_sco)
        else:
            codetables.append(aux_converted_codetable)

    dat_database = tdb.read_database_dat(args.database_file)
    print(f'number of codetables: {len(codetables)}')
    for c in codetables:
        print(f'size: {len(c)}')

    if args.merge_method == 'naive':
        converted_merged_codetable = merge_codetables_naive(codetables)
    elif args.merge_method == 'pruning':
        converted_merged_codetable = merge_codetables_pruning(codetables, dat_database)

    print(f'number of codes:  {len(converted_merged_codetable)}')
    print(f'average code_length: {statistics.mean([len(converted_merged_codetable[label]["code"]) for label in converted_merged_codetable])}')
    print(f'max_length: {max([len(converted_merged_codetable[label]["code"]) for label in converted_merged_codetable])}')
