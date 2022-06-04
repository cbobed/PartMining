###############################################################################
# Author: Carlos Bobed
# Date: Jun 2022
# Comments: Code to get basic stats about the codes in a codetable
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

    ## REQUIRED
    my_parser.add_argument('-codetable_file', action='store', required=False,
                           help="file with the code table to analyse the compression")

    args=my_parser.parse_args()
    start_time = time.time()

    # we calculate the compression regarding the original .dat database
    # codetables are in Vreekens "space"
    codetable = ct.read_codetable_dat_format(args.codetable_file)
    num_non_singleton_codes = 0
    total_length = 0
    for label in codetable:
        if len(codetable[label]['code']) > 1:
            num_non_singleton_codes += 1
            total_length += len(codetable[label]['code'])

    print(f'{args.codetable_file}')
    print(f'#NonSingletons: {num_non_singleton_codes}')
    print(f'Avg. Trans. length: {total_length/num_non_singleton_codes}')