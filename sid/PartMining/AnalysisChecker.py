###############################################################################
# Author: Carlos Bobed
# Date: Sept 2021
# Comments: Code to check the analysis of the partition to test whether the mined
# codes are correct or not
# Modifications:
###############################################################################

import math
import TransactionDatabase as tdb
import CodeTable as ct
import argparse
import time

if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="file of the database (must be the .dat)")
    ## Second group :: calculate single ratios
    ## REQUIRED
    my_parser.add_argument('-analysis_file', action='store', required=False,
                       help="file with the analysis of the database")
    ## REQUIRED
    my_parser.add_argument('-codetable_file', action='store', required=False,
                           help="file with the code table to analyse the compression")

    args=my_parser.parse_args()

    db_dat_table, dat_db_table = tdb.read_analysis_table_bidir(args.analysis_file)
    codetable = ct.read_codetable(args.codetable_file, True)
    converted_codetable = ct.convert_int_codetable(codetable, db_dat_table)
    #converted should be in .dat space
    dat_database = tdb.read_database_dat(args.database_file)

    dat_item_count = {}
    for trans in dat_database:
        for item in dat_database[trans]:
            int_item = int(item)
            if int_item not in dat_item_count:
                dat_item_count[int_item] = 0
            dat_item_count[int_item] += 1

    for db_item in sorted(db_dat_table.keys()):
        if db_dat_table[db_item] in dat_item_count:
            print(f'{db_item}::{db_dat_table[db_item]} -- SCT support: {dat_item_count[db_dat_table[db_item]]}')
        else:
            print(f'{db_item}::{db_dat_table[db_item]} lost in translation')

