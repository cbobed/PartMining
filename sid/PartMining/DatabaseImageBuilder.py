###############################################################################
# Author: Carlos Bobed
# Date: Jul 2023
# Comments: Program to build binary images of the distribution of the databases
# Modifications:
###############################################################################

import argparse
import TransactionDatabase as tdb
from PIL import Image

if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-database_file', action='store', required=True,
                           help="filename of the database (can be either .db or .dat format")
    args = my_parser.parse_args()
    db = None
    requires_translation = False
    if (args.database_file.endswith('.db')):
        db = tdb.read_database_db(args.database_file)
        # we don't need a translation as the items have been already put in order
        items_vocab_int = set()
        for trans_id in db:
            for item_id in db[trans_id]:
                items_vocab_int.add(int(item_id))
        print(f'Seen {len(items_vocab_int)} int items')
    else:
        requires_translation = True
        db = tdb.read_database_dat(args.database_file)
        items_vocab = set()
        items_vocab_int = set()
        for trans_id in db:
            for item_id in db[trans_id]:
                items_vocab.add(item_id)
                items_vocab_int.add(int(item_id))
        print(f'Seen {len(items_vocab)} item labels, and {len(items_vocab_int)} int items')
        translation_list = list(items_vocab_int)
        translation_list.sort()
        translation_table = { item_int: item_pos for (item_pos, item_int) in enumerate (translation_list)}

    im = Image.new(mode="RGB", size=(len(items_vocab_int), len(db)), color = (200, 200, 200))

    if not requires_translation:
        # They are stored as read from the file
        for trans_id in db:
            for item_id in db[trans_id]:
                im.putpixel((int(item_id), trans_id), (0,0,0))
    else:
        for trans_id in db:
            for item_id in db[trans_id]:
                im.putpixel((translation_table[int(item_id)], trans_id), (0,0,0))

    im.save(args.database_file+'.png')