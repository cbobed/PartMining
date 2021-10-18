###############################################################################
# File: ParallelizingTest.py
# Author: Carlos Bobed
# Date: Oct 2021
# Comments: Just a program to test how to parallelize using multiprocessing library
# Modifications:
# Notes:
##############################################################################

import random
import multiprocessing as mp
import time
import psutil as ps

results = []

def function_to_map(list_to_process):
    local_dict = {x:0 for x in range (100)}
    for x in list_to_process:
        local_dict[x] +=1
    return local_dict

if __name__ == '__main__':
    print('initializing ... ')
    list = [[random.randint(0,99) for x in range(2000000)] for y in range (100)]

    print ('non-parallelized ... ')
    start = time.time()
    dict = {x:0 for x in range(100)}
    for x in list:
        for y in x:
            dict[y] += 1
    end = time.time()
    print(f'no parallelization: {end-start}')
    print(f'cpus: {mp.cpu_count()} - phisical: {ps.cpu_count(logical=False)}')
    print ('parallelized ... ')
    start = time.time()
    pool = mp.Pool(ps.cpu_count(logical=False))
    dict_parallel = {x:0 for x in range(100)}
    results = pool.map(function_to_map, [x for x in list])
    for dict_result in results:
        for y in dict_result:
            dict_parallel[y] += dict_result[y]
    end = time.time()
    print(f'parallelized with {ps.cpu_count(logical=False)}: {end-start}')

    print(f'everything ok: {all([dict_parallel[x] == dict[x] for x in dict_parallel])}')