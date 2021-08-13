###############################################################################
# File: CodeTable.py
# Author: Carlos Bobed
# Date: Dec 2020
# Comments: Factorized methods from the original notebooks related to the
#   management of code tables
#   not OO, should be refactorized
# Modifications:
##############################################################################

import DatabaseCompressionCalculator as dcc
import copy
import math
import statistics

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
    converted = {}
    for label in codetable:
        translated_code = [analysis_table[int(item)] for item in codetable[label]['code']]
        str_translated_code = [str(item) for item in translated_code]
        converted[label] = {'code': str_translated_code,
                            'code_int':translated_code,
                            'code_set':set(translated_code),
                            'usage':0,
                            'support':0}
    return converted


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

    dcc.calculate_codetable_support(database, new_merged, parallelize=False)
    converted_new_merged_sco = dcc.codetable_in_standard_cover_order(new_merged)
    dcc.calculate_codetable_usage(database, converted_new_merged_sco, parallelize=False)

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
    for label in converted_new_merged_sco:
        if 'dbs' in converted_new_merged_sco[label]:
            print(f'{[x for x in merged[label]["code_lengths_array"] if x != 0]}')
            if len([x for x in merged[label]['code_lengths_array'] if x != 0]) != 0:
                code_length_before = statistics.mean([x for x in merged[label]['code_lengths_array'] if x != 0])
            else:
                code_length_before = 0
        else:
            code_length_before = merged[label]['code_length']
        print(f'{converted_new_merged_sco[label]["code_length"]} .. {code_length_before}')
        if converted_new_merged_sco[label]['code_length'] != 0 and code_length_before != 0:
            if converted_new_merged_sco[label]['code_length'] > code_length_before:
                increased_length += 1
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
    ## We leave a flag to avoid duplicated calculations (to be cleaned ... sometime, somewhere ...)
    converted_new_merged_sco['alreadyUpdated'] = True

    # we have all the previous information about the codes in merged and the new in new_merged, we have to
    # prune new_merged according to KRIMP prune step

    return converted_new_merged_sco

