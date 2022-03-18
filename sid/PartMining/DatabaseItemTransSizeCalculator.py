

import TransactionDatabase as tdb
import os
import argparse


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="file of the database")
    args=my_parser.parse_args()
    database = tdb.read_database_dat(args.database_file)
    with open(args.database_file+".transSize", "w") as output:
        output.write(str(len(database)))

    num_items = 0
    for t in database:
        num_items += len(database[t])
    with open(args.database_file+".itemSize", "w") as output:
        output.write(str(num_items))
