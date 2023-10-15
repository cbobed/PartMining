###############################################################################
# File: CodeTable.py
# Author: Carlos Bobed
# Date: Dec 2020
# Comments: Factorized methods from the original notebooks related to the
#   management of code tables
#   not OO, should be refactorized
## BEWARE: apply does not add concurrency of the processes, it centralizes the
## calculations, use starmap instead, using tuples as elements of the iterator
##  to be mapped as arguments.
## TODO: the codes are lists of strings, thus the lexicographical order might be
##      altered regarding the actual int order. The calculations are not affected
##      as we work with sets and intersections, but it could be speeded up by using
##      ordered lists and use early fail exit

# Modifications:
#   Oct 2021: Added a parallelized version of calculate support and usage
##      TODO: Instead of using a loop to gather all the information after the calculation,
##      we could try to share the information across subprocesses via a Manager (might be worthy
##      for the database, but mainly for the codetable to be updated) ->
##      thread-safety MUST be considered
##############################################################################

import copy
import math
import statistics
import argparse
import multiprocessing as mp
import TransactionDatabase as tdb
import time
import glob
import os

from collections import Counter

import multiprocessing as mp

import psutil as ps

import logging

NUMBER_OF_PROCESSORS=4
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

def read_codetable_dat_format (filename):
    codes = {}
    label = 0
    with open(filename, mode='rt', encoding='UTF-8') as file:
        for line in file:
            item_line = list(filter(None, line.rstrip('\n').split(' ')))
            if (item_line[-2] == "#SUP:"):
                usage = 0
                support = int(item_line[-1])
                codes[label] = {'code': item_line[:-2],
                                'code_int':[int(item) for item in item_line[:-2]],
                                'code_set':set([int(item) for item in item_line[:-2]]),
                                'usage': int(usage), 'support': int(support)}
                label += 1
            elif (item_line[-1].startswith('#SUP:')):
                usage = 0
                support = int(item_line[-1].split(':')[1])
                codes[label] = {'code': item_line[:-1],
                                'code_int':[int(item) for item in item_line[:-1]],
                                'code_set':set([int(item) for item in item_line[:-1]]),
                                'usage': int(usage), 'support': int(support)}
                label += 1
            else:
                usage = 0
                support = 0
                codes[label] = {'code': item_line,
                                'code_int':[int(item) for item in item_line],
                                'code_set':set([int(item) for item in item_line]),
                                'usage': int(usage), 'support': int(support)}
                label += 1
    return codes

def add_sct (codetable, sct_codetable):
    max_label = max(codetable.keys()) + 1
    for label in sct_codetable:
        aux_set = set()
        aux_set.add(int(sct_codetable[label]['code']))
        codetable[max_label] = {'code': [sct_codetable[label]['code']],
                            'code_int': [int(sct_codetable[label]['code'])],
                            'code_set': aux_set,
                            'usage': 0,
                            'support':0}
        max_label +=1


## it assumes that it has been already sorted if required (calculate_cover_order)
def store_codetable_dat(codetable, filename):
    with open(filename, mode='w', encoding='UTF-8') as file:
        for code_label in codetable:
            for item in codetable[code_label]['code']:
                file.write(item + ' ')
            file.write('#SUP: ')
            file.write(str(codetable[code_label]['support']))
            file.write('\n')

def calculate_sct_support_usage (database):
    result = {}
    for trans in database:
        for singleton in [int(item) for item in database[trans]]:
            if singleton not in result:
                result[singleton] = {'code': str(singleton), 'support': 0, 'usage': 0}
            result[singleton]['usage'] = result[singleton]['usage'] + 1
            result[singleton]['support'] = result[singleton]['support'] + 1
    return result

def build_SCT(database, parallel=False, num_processors=NUMBER_OF_PROCESSORS):
    sct_codetable = {}
    if (not parallel):
        for trans in database:
            for singleton in [int(item) for item in database[trans]]:

                if singleton not in sct_codetable:
                    sct_codetable[singleton] = {'code': str(singleton), 'support': 0, 'usage': 0}
                sct_codetable[singleton]['usage'] = sct_codetable[singleton]['usage'] + 1
                sct_codetable[singleton]['support'] = sct_codetable[singleton]['support'] + 1
    else:
        pool = mp.Pool(num_processors)
        chunk_length = len(database) // num_processors
        limits = [i * chunk_length for i in range(num_processors)]
        limits.append(len(database))
        print(f'chunks ... {limits}')
        results = pool.map(calculate_sct_support_usage,
                               [dict(list(database.items())[limits[i]:limits[i + 1]]) for i in
                                range(num_processors)])
        logging.debug('reducing the results ... ')
        ## each result is a dict
        for result_dict in results:
            for label in result_dict:
                if label not in sct_codetable:
                    sct_codetable[label]={'code': result_dict[label]['code'],
                                          'support': result_dict[label]['support'],
                                          'usage': result_dict[label]['usage']}
                else:
                    sct_codetable[label]['support'] += result_dict[label]['support']
                    sct_codetable[label]['usage'] += result_dict[label]['usage']

        pool.close()
    logging.debug('<-- leaving support')
    return sct_codetable

def convert_int_codetable (codetable, analysis_table):
    ## we have to take into account that db.analysis seems to introduce the 0 item
    ## which should never be present in the vocabularies of .dat dabases (1 .. infinity)

    ## IT MIGHT BE A PROBLEM WITH THE SLIM VERSION => uint16 does not cover the
    ## item vocabulary and caused an overflow :: USE OUR modified version to do so
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

# Reminder:
# Standard cover order
# |X|↓ suppD(X) ↓ lexicographically ↑
# Standard candidate order
# suppD(X) ↓|X|↓ lexicographically ↑

# def calculate_transaction_cover(transaction, codetable):
#     item_set = set(transaction)
#     codes = []
#     current_code = 0
#     while (len(item_set) != 0 and current_code < len(codetable)):
#         aux_code_set = set(codetable[current_code]['code'])
#         if (aux_code_set.issubset(item_set)):
#             codes.append(current_code)
#             item_set.difference_update(aux_code_set)
#         current_code += 1
#     return codes

def calculate_transaction_support (database, codetable):
    result = {}
    for trans in database:
        item_set = set([int(item) for item in database[trans]])
        for label in codetable:
            if len(codetable[label]['code_set'].intersection(item_set)) == len(codetable[label]['code_set']):
                if label not in result:
                    result[label] = 0
                result[label] += 1
        # we return all the labels of the codes supported by these transactions
        # we need to reduce the data afterwards
    return result

def calculate_transaction_support_from_file (filename, codetable):
    result = {}
    with open(filename, mode='rt', encoding='UTF-8') as file:
        lines = file.readlines()
        for line in lines:
            aux = line.rstrip('\n')
            words = filter(None, aux.split(' '))
            item_set = set([int(item) for item in list(words)])
            for label in codetable:
                if len(codetable[label]['code_set'].intersection(item_set)) == len(codetable[label]['code_set']):
                    if label not in result:
                        result[label] = 0
                    result[label] += 1
        # we return all the labels of the codes supported by these transactions
        # we need to reduce the data afterwards
    return result

def calculate_codetable_support(database, codetable, parallel=False, use_file_splitting=False, reuse_files=False, num_processors=NUMBER_OF_PROCESSORS):
    logging.debug('--> entering support')
    logging.debug('cleaning the codetable ... ')
    for label in codetable:
        if 'code_set' not in codetable[label]:
            codetable[label]['code_set'] = set([int(item) for item in codetable[label]['code']])
        # it might not be initialized
        codetable[label]['support'] = 0
    logging.debug('calculating the supports ...')
    if (not parallel):
        for trans in database:
            item_set = set([int(item) for item in database[trans]])
            ## we have to check all the codes in the code table
            ## this might be expensive ... we could just get the sum of the supports in the different databases
            ## note that this is additive so in a better implementation it wouldn't be a problem
            for label in codetable:
                ## if the intersection of the code is complete with the transaction
                if len(codetable[label]['code_set'].intersection(item_set)) == len(codetable[label]['code_set']):
                    codetable[label]['support'] += 1
    else:
        # pool = mp.get_context("spawn").Pool(ps.cpu_count(logical=False))
        pool = mp.Pool(num_processors)
        chunk_length = len(database) // num_processors
        limits = [i * chunk_length for i in range(num_processors)]
        limits.append(len(database))
        print(f'chunks ... {limits}')

        if (not use_file_splitting):
            results = pool.starmap(calculate_transaction_support, [(dict(list(database.items())[limits[i]:limits[i+1]]), codetable)  for i in range(num_processors)])
        else:
            if (not reuse_files):
                listing = glob.glob('tmp_split*')
                # we clean the previous existing files
                for filename in listing:
                    if os.path.exists(filename):
                        os.remove(filename)
                for i in range(num_processors):
                    with open('tmp_split_'+str(i)+'.dat', 'w', encoding='UTF-8') as output:
                        for trans_tuple in list(database.items())[limits[i]:limits[i + 1]]:
                            for item in trans_tuple[1]:
                                output.write(item+' ')
                            output.write('\n')


            results = pool.starmap(calculate_transaction_support_from_file, [('tmp_split_'+str(i)+'.dat', codetable) for i in range(num_processors)])

        logging.debug('reducing the results ... ')
        for result_set in results:
            for label in result_set:
                codetable[label]['support'] += result_set[label]

        pool.close()
    logging.debug('<-- leaving support')

## Note that I cannot do it until I have the codetable

def calculate_transaction_usage (database, codetable):
    result = {}
    for trans in database:
        remaining_item_set = set([int(item) for item in database[trans]])
        current_code = 0
        while len(remaining_item_set) != 0 and current_code < len(codetable):
            # if len(codetable[current_code]['code_set'].intersection(remaining_item_set)) == len(
            #         codetable[current_code]['code_set']):
            #     result.append(current_code)
            #     remaining_item_set = remaining_item_set - codetable[current_code]['code_set']

            if codetable[current_code]['code_set'].issubset(remaining_item_set):
                if current_code not in result:
                    result[current_code] = 0
                result[current_code] += 1
                remaining_item_set.difference_update(codetable[current_code]['code_set'])
            current_code += 1
        #if len(remaining_item_set) != 0:
        #    print(f'non-covered{remaining_item_set}')
        #    print(f'singletons: {[codetable[idx]["code"] for idx in codetable if len(codetable[idx]["code"]) == 1]}')
        #    print('This codetable is not covering properly the database ... is the SCT added?')
    return result


def calculate_transaction_usage_from_file (filename, codetable):
    result = {}
    with open(filename, mode='rt', encoding='UTF-8') as file:
        lines = file.readlines()
        for line in lines:
            aux = line.rstrip('\n')
            words = filter(None, aux.split(' '))
            remaining_item_set = set([int(item) for item in list(words)])
            current_code = 0
            while len(remaining_item_set) != 0 and current_code < len(codetable):
                if codetable[current_code]['code_set'].issubset(remaining_item_set):
                    if current_code not in result:
                        result[current_code] = 0
                    result[current_code] += 1
                    remaining_item_set.difference_update(codetable[current_code]['code_set'])
                current_code += 1
            #if len(remaining_item_set) != 0:
            #    print(f'non-covered{remaining_item_set}')
            #    print(f'singletons: {[codetable[idx]["code"] for idx in codetable if len(codetable[idx]["code"]) == 1]}')
            #    print('This codetable is not covering properly the database ... is the SCT added?')
    return result

def calculate_codetable_usage(database, codetable, parallel=False, use_file_splitting=False, reuse_files=False, num_processors=NUMBER_OF_PROCESSORS):
    logging.debug('--> entering usage')
    logging.debug('cleaning the codetable ... ')
    for label in codetable:
        if 'code_set' not in codetable[label]:
            codetable[label]['code_set'] = set([int(item) for item in codetable[label]['code']])
        # we make sure that the usage is initialized to 0
        codetable[label]['usage'] = 0
    logging.debug('calculating the usages ... ')
    if (not parallel):
        for trans in database:
            remaining_item_set = set([int(item) for item in database[trans]])
            current_code = 0
            while len(remaining_item_set) != 0 and current_code < len(codetable):
                if len(codetable[current_code]['code_set'].intersection(remaining_item_set)) == len(
                        codetable[current_code]['code_set']):
                    codetable[current_code]['usage'] += 1
                    remaining_item_set = remaining_item_set - codetable[current_code]['code_set']
                current_code += 1

            #if len(remaining_item_set) != 0:
            #    print(f'non-covered{remaining_item_set}')
            #    print(f'singletons: {[codetable[idx]["code"] for idx in codetable if len(codetable[idx]["code"]) == 1]}')
            #    print('This codetable is not covering properly the database ... is the SCT added?')
    else:
        # pool = mp.get_context("spawn").Pool(ps.cpu_count(logical=False))
        pool = mp.Pool(num_processors)
        chunk_length = len(database) // num_processors
        limits = [i * chunk_length for i in range(num_processors)]
        limits.append(len(database))
        print(f'chunks ... {limits}')

        if (not use_file_splitting):
            results = pool.starmap(calculate_transaction_usage,
                                   [(dict(list(database.items())[limits[i]:limits[i + 1]]), codetable) for i in
                                    range(num_processors)])
        else:
            if (not reuse_files):
                listing = glob.glob('tmp_split*')
                # we clean the previous existing files
                for filename in listing:
                    if os.path.exists(filename):
                        os.remove(filename)
                for i in range(num_processors):
                    with open('tmp_split_' + str(i) + '.dat', 'w', encoding='UTF-8') as output:
                        for trans_tuple in list(database.items())[limits[i]:limits[i + 1]]:
                            for item in trans_tuple[1]:
                                output.write(item + ' ')
                            output.write('\n')
            results = pool.starmap(calculate_transaction_usage_from_file,
                                   [('tmp_split_' + str(i) + '.dat', codetable) for i in range(num_processors)])


        logging.debug('reducing the results ... ')
        # we apply the data to the codetable
        for result_set in results:
            for label in result_set:
                codetable[label]['usage'] += result_set[label]

        pool.close()
    logging.debug('<--leaving usage ')

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
                codetable_size += sct_codelengths[int(item)]
    print(f'database_size: {database_size}')
    print(f'codetable_size: {codetable_size}')
    print(f'complete: {database_size+codetable_size}')
    return database_size + codetable_size

def calculate_complete_size_sct (standard_codetable):
    database_size = calculate_size_database_from_codetable(standard_codetable)
    sum_usage_standard_codetable = 0
    sct_codetable_size = 0.0
    for label in standard_codetable:
        sum_usage_standard_codetable += standard_codetable[label]['usage']
    for label in standard_codetable:
        if standard_codetable[label]['usage'] != 0:
            sct_codetable_size += -math.log(standard_codetable[label]['usage'] / sum_usage_standard_codetable)
    print(f'database_size: {database_size}')
    print(f'codetable_size: {sct_codetable_size}')
    print(f'complete: {database_size+sct_codetable_size}')
    return database_size + sct_codetable_size



def prune_by_usage_threshold(codetable, threshold):
    return {i:{'code':codetable[i]['code'],
           'support':0,
           'usage':0,
           'code_set':codetable[i]['code_set']} for i in codetable if codetable[i]['usage'] > threshold or len(codetable[i]['code']) == 1}


def calculate_generalized_jaccard_index_from_scts(sct_1, sct_2):
    num = 0.0;
    den = 0.0;
    for item in set(sct_1.keys()).union(sct_2.keys()):
        ## sum (min (x_i, y_i)) / sum (max (x_i, y_i))
        num += min (sct_1[item]['support'] if item in sct_1 else 0,
                    sct_2[item]['support'] if item in sct_2 else 0)
        den += max(sct_1[item]['support'] if item in sct_1 else 0,
                   sct_2[item]['support'] if item in sct_2 else 0)
    return (num/den)

## naive way of merging the codetables
## for convenience we work here with integers (we kept the codetables as string tokens to be able to handle the vector models)
def merge_codetables_naive(codetables_info):

    logging.debug(f'deduplicating codes')
    # table i vs table j in each, we store the
    # repeated in to_omit[j]
    to_omit = {}
    for i in range(len(codetables_info)-1):
        logging.debug(f'processing {i} {len(codetables_info[i]["codetable"])} against ... ')
        for j in range(i+1, len(codetables_info)):
            logging.debug(f' ... {j} - {len(codetables_info[j]["codetable"])}')
            if j not in to_omit:
                to_omit[j] = set()
            table_i = codetables_info[i]['codetable']
            table_j = codetables_info[j]['codetable']
            auxCount = 0
            ## deduplicate i against j
            for code_i_label in table_i:
                auxCount +=1
                if auxCount % 10000 == 0:
                    logging.debug(f'{auxCount} codes of this table processed ')
                if not (i in to_omit and code_i_label in to_omit[i]):
                    for code_j_label in table_j:
                        if code_j_label not in to_omit[j]:
                            if len(table_i[code_i_label]['code']) == len(table_j[code_j_label]['code']):
                                if 'code_set' in table_i[code_i_label]:
                                    set_i = table_i[code_i_label]['code_set']
                                else:
                                    set_i = set([int(item) for item in table_i[code_i_label]['code']])
                                if 'code_set' in table_j[code_j_label]:
                                    set_j = table_j[code_j_label]['code_set']
                                else:
                                    set_j = set([int(item) for item in table_j[code_j_label]['code']])
                                if set_i == set_j:
                                    to_omit[j].add(code_j_label)
    merged = {}
    non_colision_labelbase = 0
    for i in range(len(codetables_info)):
        ## we skip the codes marked to be omitted
        for label in codetables_info[i]['codetable']:
            if not (i in to_omit and label in to_omit[i]):
                current_label = str(non_colision_labelbase) + '_' + str(label)
                merged[current_label] = codetables_info[i]['codetable'][label]
        non_colision_labelbase += 1
    logging.debug('merging done ...')

    for label in merged:
        if 'code_int' in merged[label]:
            merged[label]['code'] = [str(item) for item in merged[label]['code_int']]
        merged[label]['usage'] = 0
        merged[label]['support'] = 0

    return merged

def merge_codetables_naive_converted(codetables_info):

    logging.debug(f'deduplicating codes')
    # table i vs table j in each, we store the
    # repeated in to_omit[j]
    to_omit = {}
    for i in range(len(codetables_info)-1):
        logging.debug(f'processing {i} {len(codetables_info[i]["codetable"])} against ... ')
        for j in range(i+1, len(codetables_info)):
            logging.debug(f' ... {j} - {len(codetables_info[j]["codetable"])}')
            if j not in to_omit:
                to_omit[j] = set()
            table_i = codetables_info[i]['codetable']
            table_j = codetables_info[j]['codetable']
            auxCount = 0
            ## deduplicate i against j
            for code_i_label in table_i:
                if not (i in to_omit and code_i_label in to_omit[i]):
                    for code_j_label in table_j:
                        if code_j_label not in to_omit[j]:
                            if 'code_set' in table_i[code_i_label]:
                                set_i = table_i[code_i_label]['code_set']
                            else:
                                set_i = set([int(item) for item in table_i[code_i_label]['code']])
                            if 'code_set' in table_j[code_j_label]:
                                set_j = table_j[code_j_label]['code_set']
                            else:
                                set_j = set([int(item) for item in table_j[code_j_label]['code']])
                            if set_i == set_j:
                                to_omit[j].add(code_j_label)
        logging.debug(f'omitting {len(to_omit[j])} ... from table {j}')

    merged = {}
    non_colision_labelbase = 0
    for i in range(len(codetables_info)):
        ## we skip the codes marked to be omitted
        for label in codetables_info[i]['codetable']:
            if not (i in to_omit and label in to_omit[i]):
                current_label = str(non_colision_labelbase) + '_' + str(label)
                merged[current_label] = codetables_info[i]['codetable'][label]
        non_colision_labelbase += 1
    logging.debug('merging done ...')

    for label in merged:
        if 'code_int' in merged[label]:
            merged[label]['code'] = [str(item) for item in merged[label]['code_int']]
        merged[label]['usage'] = 0
        merged[label]['support'] = 0

    return merged


## we merge the tables and we apply the KRIMP pruning after the merging to
## avoid possible local decisions that might hid different codes
## PRE: codetables with the support and the usages calculated

# we adapt the post-acceptance pruning to the case where we have different
# source tables, w don't care about the original lengths, but about the original
# code usages (sum of all the usages in the original tables for the repeated
# codes)

def merge_codetables_pruning(codetables_info, database):
    merged = {}
    non_colision_labelbase = 0

    for ct in [x['codetable'] for x in codetables_info]:
        for label in ct:
            current_label = str(non_colision_labelbase) + '_' + str(label)
            merged[current_label] = ct[label]
        non_colision_labelbase += 1

    # we keep track of the codes that are duplicated
    to_omit = set()
    merged_groups = {}
    merged_key_list = list(merged.keys())
    for i in range(len(merged_key_list)):
        if merged_key_list[i] not in to_omit:
            current_label = merged_key_list[i]
            merged_groups[current_label] = [merged_key_list[i]]
            for j in range(i + 1, len(merged_key_list)):
                if merged_key_list[j] not in to_omit:
                    # depending on how the table has been obtained it might or not have the code_set field
                    ## converted using the analysis table (convert_int_codetable) => it has
                    ## loaded from file => it hasn't
                    if 'code_set' in merged[current_label]:
                        set_i = merged[current_label]['code_set']
                    else:
                        set_i = set([int(item) for item in merged[current_label]['code']])
                    if 'code_set' in merged[merged_key_list[j]]:
                        set_j = merged[merged_key_list[j]]['code_set']
                    else:
                        set_j = set([int(item) for item in merged[merged_key_list[j]]['code']])

                    if set_i == set_j:
                        # mark the duplicated label to get rid of, but add it to the associated
                        # group
                        to_omit.add(merged_key_list[j])
                        merged_groups[current_label].append(merged_key_list[j])


    new_merged = copy.deepcopy(merged)
    for label in new_merged:
        if 'code_int' in new_merged[label]:
            new_merged[label]['code'] = [str(item) for item in new_merged[label]['code_int']]
        new_merged[label]['usage'] = 0
        new_merged[label]['support'] = 0

    # we get rid of the duplicated entries in the codetable
    [new_merged.pop(code) for code in to_omit]
    # I copy this version as my clean candidate codetable
    new_merged_candidate = copy.deepcopy(new_merged)

    for label in merged_groups:
        for entry in merged_groups[label]:
            new_merged[label]['usage'] += merged[entry]['usage']
            new_merged[label]['support'] += merged[entry]['support']

    ## To prune according to KRIMP, we need the previous supports and usages
    calculate_codetable_support(database, new_merged_candidate)
    converted_new_merged_candidate_sco = codetable_in_standard_cover_order(new_merged_candidate)
    calculate_codetable_usage(database, converted_new_merged_candidate_sco)

    # let's check how many have changed their usages
    increased_usage = 0
    equal_usage = 0
    decreased_usage = 0
    not_used_before = 0
    not_used_after = 0

    stored_info = {}
    for label in converted_new_merged_candidate_sco:
        prev_label = converted_new_merged_candidate_sco[label]['old_label']
        code_usage_before = new_merged[prev_label]['usage']
        if converted_new_merged_candidate_sco[label]['usage'] != 0 and code_usage_before != 0:
            if converted_new_merged_candidate_sco[label]['usage'] > code_usage_before:
                increased_usage += 1
                stored_info[label] = {'diff': converted_new_merged_candidate_sco[label]['usage'] - code_usage_before}
            elif converted_new_merged_candidate_sco[label]['usage']< code_usage_before:
                decreased_usage += 1
            else:
                equal_usage += 1

        else:
            if converted_new_merged_candidate_sco[label]['usage'] == 0:
                not_used_after +=1
            if code_usage_before == 0:
                not_used_before += 1

    print(f'increased_usage :: {increased_usage}')
    print(f'equal_usage :: {equal_usage}')
    print(f'decreased_usage ::{decreased_usage }')
    print(f'not_used_before :: {not_used_before}')
    print(f'not_used_after :: {not_used_after}')
    # print(f'stored_info ::{[(x,stored_info[x]["diff"]) for x in sorted(stored_info.keys(), key=lambda x: stored_info[x]["diff"], reverse=True)]}')
    ## We leave a flag to avoid duplicated calculations (to be cleaned ... sometime, somewhere ...)

    print(f'starting the pruning ... ')
    # we have new_merged with the previous information merged
    # we have converted_new_merged_candidate_sco with the information adapted to the global database
    # we have also the code labels (of new_merged_candidate) of the codes that have decreased their usage
    ##      According to KRIMP's algorithm: those are the starting prune candidate set

    #In the original algorithm, it test all the codes
    # PruneCand ← X ∈ PruneSet    with lowest usageCTc (X)
    # we skip the singletons, just to be sure

    database_sct = build_SCT(database)
    print(f'number of codes before pruning: {len(converted_new_merged_candidate_sco)}')
    print(f'database size before: {calculate_size_database_from_codetable(converted_new_merged_candidate_sco)}')
    prune_set = set(label for label in stored_info if len(converted_new_merged_candidate_sco[label]['code']) > 1)
    print(f'prune_candidate_set: {len(prune_set)}')
    while len(prune_set) != 0:
        code_candidate = sorted([label for label in prune_set], key=lambda x: len(converted_new_merged_candidate_sco[x]['code']), reverse=True)[0]
        prune_set.remove(code_candidate)
        print(f'checking: {converted_new_merged_candidate_sco[code_candidate]["code"]}')
        print(f'prune_candidate_set: {len(prune_set)}')
        aux_pruned = copy.deepcopy(converted_new_merged_candidate_sco)
        aux_pruned.pop(code_candidate)

        # we wouldn't have to update the supports, as the D hasn't change,
        # we have only to update the usages, but there might be a problem with the support
        # of the singletons => TODO
        for aux_label in aux_pruned:
            aux_pruned[aux_label]['support'] = 0
            aux_pruned[aux_label]['usage'] = 0

        calculate_codetable_support(database, aux_pruned)
        converted_new_merged_pruned_sco = codetable_in_standard_cover_order(aux_pruned)
        calculate_codetable_usage(database, converted_new_merged_pruned_sco)

        current_size = calculate_complete_size(converted_new_merged_candidate_sco, database_sct)
        pruned_size = calculate_complete_size(converted_new_merged_pruned_sco, database_sct)

        if pruned_size < current_size:
            for label in converted_new_merged_pruned_sco:
                if len(converted_new_merged_pruned_sco[label]['code']) > 1:
                    if (converted_new_merged_pruned_sco[label]['usage']<converted_new_merged_candidate_sco[label]['usage']):
                        prune_set.add(label)
            converted_new_merged_candidate_sco = converted_new_merged_pruned_sco
            print(f'code pruned __ before: {current_size} -> after: {pruned_size}')
    print(f'number of codes after pruning: {len(converted_new_merged_candidate_sco)}')
    print(f'database size after: {calculate_size_database_from_codetable(converted_new_merged_candidate_sco)}')
    # we have all the previous information about the codes in merged and the new in new_merged, we have to
    # prune new_merged according to KRIMP prune step
    return converted_new_merged_candidate_sco

## naive plus way of merging the codetables:
## for convenience we work here with integers (we kept the codetables as string tokens to be able to handle the vector models)
## we just get the one with the best compression ratio
def merge_codetables_naive_plus(codetables_info, database):
    aux_sct_codetable = build_SCT(database, False)
    aux_sct_size = calculate_complete_size_sct(aux_sct_codetable)

    for current_ct in codetables_info:
        ## beware, here we have a problem with the code's id's ... it's not straightforward:
        ## SCTs codes ids ARE directly the items
        ## While this is not the same for standard codetables
        # We gather first the singletons in the codetable, and then we add them without collisions (using the successor of the
        # max of the keys in the codetable)
        ## recall: 'code' == list of strings , 'code_int' list of integers
        singleton_ct_ids = set ([item for item in current_ct['codetable'] if len(current_ct['codetable'][item]['code']) == 1])
        singleton_ids = set([int(current_ct['codetable'][item]['code'][0]) for item in (singleton_ct_ids)])
        print(f'current singletons: {singleton_ids}')
        max_id = max([idx for idx in current_ct['codetable']])
        aux_count = 0
        added = set()
        for singleton in aux_sct_codetable:
            if singleton not in singleton_ids:
                max_id += 1
                aux_count += 1
                current_ct['codetable'][max_id] = {'code': [str(singleton)], 'code_int': [singleton], 'support': 0, 'usage': 0}
                added.add(singleton)

        print(f'Added {aux_count} singletons')
        print(f'added:  {added}')
        calculate_codetable_support(database, current_ct['codetable'], True, True,
                                       reuse_files=False)
        print(f'num codes: {len(current_ct["codetable"])}')
        print(f'num codes with support 0: {len([x for x in current_ct["codetable"] if current_ct["codetable"][x]["support"] == 0])}')
        #for x in current_ct["codetable"] :
        #    if current_ct["codetable"] [x]["support"] == 0:
        #        print(f'code with support 0: {current_ct["codetable"] [x]}')
        aux_codetable_sco = codetable_in_standard_cover_order(current_ct["codetable"])
        calculate_codetable_usage(database, aux_codetable_sco, True, True,
                                     reuse_files=True)
        aux_size = calculate_complete_size(aux_codetable_sco, aux_sct_codetable)
        aux_ratio = aux_size / aux_sct_size
        current_ct['global_ratio'] = aux_ratio
        print(f'Partition ratio: {aux_ratio}')

    ratios = [ct['global_ratio'] for ct in codetables_info]
    return codetables_info[ratios.index(min(ratios))]['codetable']

    ## we order the candidates according to their (global compression ratio * current_codetable_similarity).

def merge_codetables_informed (codetables_info, database, early_finish=False):

    global_sct_codetable = build_SCT(database, False)
    sct_compressed_size = calculate_complete_size_sct(global_sct_codetable)

    merge_codetables_naive_plus(codetables_info, database)
    ratios = [ct['global_ratio'] for ct in codetables_info]
    initial_index = ratios.index(min(ratios))
    current_codetable = copy.deepcopy(codetables_info[initial_index]['codetable'])
    current_sct = copy.deepcopy(codetables_info[initial_index]['sct_codetable'])
    current_ratio = codetables_info[initial_index]['global_ratio']
    to_process = set(range(len(codetables_info)))
    to_process.remove(initial_index)
    merged = set()
    merged.add(initial_index)
    print (f'initial ratio: {current_ratio}')
    print (f'merged: {merged}')
    go_on = True
    while (len(to_process) != 0 and go_on):
        print(f'merged: {merged}')
        print(f'to_process: {to_process}')
        # we want to add first those with high compression ratio (low value) and low similarity (low gji)
        candidate_similarity_pairs = [ (idx,calculate_generalized_jaccard_index_from_scts(codetables_info[idx]['sct_codetable'], current_sct) * codetables_info[idx]['global_ratio'])
                                        for idx in to_process ]
        candidate_similarity_values = [x[1] for x in candidate_similarity_pairs]
        # we want the lowest value
        candidate_pos =  candidate_similarity_values.index(min(candidate_similarity_values))
        print (candidate_similarity_pairs)
        next_candidate_index = candidate_similarity_pairs[candidate_pos][0]
        print(f'next_candidate: {next_candidate_index}')
        aux_codetable = merge_codetables_naive([{'codetable':current_codetable},{'codetable':codetables_info[next_candidate_index]['codetable']}])
        calculate_codetable_support(database, aux_codetable, True, True, reuse_files=False)
        aux_codetable_sco = codetable_in_standard_cover_order(aux_codetable)
        calculate_codetable_usage(database, aux_codetable_sco, True, True, reuse_files=True)

        aux_compressed_size = calculate_complete_size(aux_codetable_sco, global_sct_codetable)
        aux_ratio = aux_compressed_size / sct_compressed_size
        print(f'current_ratio: {current_ratio} --- candidate_ratio:{aux_ratio}')
        to_process.remove(next_candidate_index)
        if (aux_ratio < current_ratio):
            current_ratio = aux_ratio
            print(f'!!!!! ********* merge accepted ... ')
            merged.add(next_candidate_index)
            current_codetable = aux_codetable_sco
            # we update the current_sct with the usages of the previous ones
            for item in codetables_info[next_candidate_index]['sct_codetable']:
                if item not in current_sct:
                    current_sct[item]={'code': [str(item)], 'usage':0, 'support': 0}
                current_sct[item]['usage'] += codetables_info[next_candidate_index]['sct_codetable'][item]['usage']
                current_sct[item]['support'] = current_sct[item]['usage']

        else:
            if (early_finish):
                go_on = False
            print(f'!!!!! ********* merge rejected ... ')
    return current_codetable

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

        # if (args.merge_method == 'pruning'):
        #     # we need to calculate the local supports and usages
        #     aux_dat_database = tdb.read_database_dat(current_name + '.dat')
        #
        #     calculate_codetable_support(aux_dat_database, aux_converted_codetable)
        #     print(f'num codes: {len(aux_codetable)}')
        #     print(f'codes with support 0: {[x for x in aux_converted_codetable if aux_converted_codetable[x]["support"] == 0]}')
        #     aux_codetable_sco = codetable_in_standard_cover_order(aux_converted_codetable)
        #     calculate_codetable_usage(aux_dat_database, aux_codetable_sco)
        #     print(f'codes with usage 0: {[x for x in aux_codetable_sco if aux_codetable_sco[x]["usage"] == 0]}')
        #
        #     codetables.append(aux_codetable_sco)
        # else:
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
