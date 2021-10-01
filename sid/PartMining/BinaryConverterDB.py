###############################################################################
# File: BinaryConverter.py
# Author: Carlos Bobed
# Date: Sept 2020
# Comments: Program to convert a dat file into a stream of bytes instead of
# a text file
# Modifications:
##############################################################################

import argparse
import TransactionDatabase as tdb

if __name__ == '__main__':

    # params: -model file
    #         -output file
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-model', action='store', required=True,
                           help="file with the item embeddings in dat format")
    my_parser.add_argument('-bytes_item', action='store', type=int, required=False,
                           help="number of bytes to codify each item, default: 2", default=2)
    my_parser.add_argument('-output', action='store', required=False,
                           help="binary file name")
    args = my_parser.parse_args()

    if args.output is not None:
        output_file = args.output
    else:
        output_file = args.model[:args.model.rfind(".db")]+".dbbin"

    transactions = tdb.read_database_db(args.model)
    with open(output_file, "wb") as output:
        for trans in sorted(transactions.keys(), reverse=False):

            for it in transactions[trans]:
                auxInt = int(it)
                output.write(auxInt.to_bytes(args.bytes_item, byteorder='big', signed=False))