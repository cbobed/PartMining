###############################################################################
# File: VectorTools.py
# Author: Carlos Bobed
# Date: Sept 2020
# Comments: Code to obtain a word embedding model out from a transactional database
# in Vreeken et al. database format
# Modifications:
#   Dec 2021: added doc2vec model to get different embeddings for the transactions
###############################################################################

import gensim, logging, os, sys, gzip
import time
import argparse

# Adapted from rdf2vecCode
# It provides an iterator which feeds the word2vec training
# two flavours for .db files:
# - non ordered sentences (as they are in the file)
# - custom ordered (heap approach: sorted ASC && then
#       the lowest data in the middle (they are the items with the biggest support)
# another iterator for .dat file

class MySentencesDB(object):
    def __init__(self, filename):
        self.filename = filename
    def __iter__(self):
        try:
            for line in open(self.filename, mode='rt', encoding='UTF-8'):
                if (line.split(':')[0].isnumeric()):
                    aux = line.split(':')[1].rstrip('\n')
                    words = filter(None,aux.split(' '))
                    yield list(words)
        except Exception:
            print ('Failed reading file: ')
            print (self.filename)

class MyDocumentsDB(object):
    def __init__(self, filename):
        self.filename = filename
    def __iter__(self):
        try:
            i = -1
            for line in open(self.filename, mode='rt', encoding='UTF-8'):
                i += 1
                if (line.split(':')[0].isnumeric()):
                    aux = line.split(':')[1].rstrip('\n')
                    words = filter(None,aux.split(' '))
                    yield gensim.models.doc2vec.TaggedDocument(list(words), [i])
        except Exception:
            print ('Failed reading file: ')
            print (self.filename)

def custom_order_db (item_list):
    atEnd = False;
    result = []
    for it in sorted(item_list):
        if not atEnd:
            result.insert(0,it)
        else:
            result.append(it)
        atEnd = not atEnd
    return result

# THis method assumes that the database items are ordered
# according to their support, this is, is a conversed database (vreeken's format)
# 0 => highest suppport
class MyOrderedSentencesDB(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        try:
            for line in open(self.filename, mode='rt', encoding='UTF-8'):
                if (line.split(':')[0].isnumeric()):
                    aux = line.split(':')[1].rstrip('\n')
                    words = filter(None,aux.split(' '))
                    ints = [int(it) for it in words]
                    words = [str(it) for it in custom_order_db(ints)]
                    yield list(words)
        except Exception:
            print ('Failed reading file: ')
            print (self.filename)

class MySentencesDat(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        try:
            for line in open(self.filename, mode='rt', encoding='UTF-8'):
                aux = line.rstrip('\n')
                words = filter(None,aux.split(' '))
                yield list(words)
        except Exception:
            print ('Failed reading file: ')
            print (self.filename)

class MyDocumentsDat(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        try:
            i=-1
            for line in open(self.filename, mode='rt', encoding='UTF-8'):
                i+=1
                aux = line.rstrip('\n')
                words = filter(None,aux.split(' '))
                yield gensim.Doc2Vec.TaggedDocument(list(words), [i])
        except Exception:
            print ('Failed reading file: ')
            print (self.filename)

if __name__ == "__main__":
    # This is the entry point to get the vectors for a database file or for
    # all the datasets that are within a given directory

    # params: -win windows_size
    #         -alg skip_gram | cbow
    #         -dim vector dimension
    #         -epochs training epochs
    #         -workers number of "workers" used in the training
    #         -file ... it can be .db or .dat
    #         -dir ... process all the files in the given directory ending in .db or .dat

    my_parser = argparse.ArgumentParser(allow_abbrev=False)

    my_parser.add_argument('-win', action='store', type=int, required=False,
                           help="windows size for the w2vec alg, default: 5", default=5)
    ## From the doc2vec documentation:
    # PV-DM is analogous to Word2Vec CBOW. The doc-vectors are obtained by training a neural
    # network on the synthetic task of predicting a center word based an average of both context
    # word-vectors and the full document’s doc-vector.
    #
    # PV-DBOW is analogous to Word2Vec SG. The doc-vectors are obtained by training a neural
    # network on the synthetic task of predicting a target word just from the full document’s doc-vector.
    # (It is also common to combine this with skip-gram testing, using both the doc-vector and nearby word-vectors
    # to predict a single target word, but only one at a time.)
    my_parser.add_argument('-alg', action='store', choices=['sg', 'cbow', 'pv-dbow', 'pv-dm'],
                           help=" use skip_gram or cbow for word2vec, default: sg",
                           default='sg')
    my_parser.add_argument('-dim', action='store', type=int, required=False,
                           help="dimension of the vectors, default: 200", default=200)
    my_parser.add_argument('-epochs', action='store', type=int, required=False,
                           help="number of training epochs, default: 10", default=10)
    my_parser.add_argument('-workers', action='store', type=int, required=False,
                       help="number of workers for the training, default: 4", default=4)
    my_parser.add_argument('-ord', action='store_true', required=False, default=False,
                        help='custom ordering for DB transactions')

    mut_group = my_parser.add_mutually_exclusive_group(required=True)
    mut_group.add_argument('-dir', action='store',
                           help='directory to be processed')
    mut_group.add_argument('-file', action='store', help='file to be processed')

    args=my_parser.parse_args()

    print('executing the script with the following parameters:')
    print(args)

    if args.file:
        list_files = [args.file]
    elif args.dir:
        list_files = [os.path.join(args.dir, f) for f in os.listdir(args.dir) if f.endswith('.dat') or f.endswith('.db')]

    print ('processing the following files')
    print(list_files)

    for fname in list_files:
        if (fname.endswith('.db')):
            if (args.alg == 'sg' or args.alg == 'cbow'):
                if (args.ord):
                    sentences = MyOrderedSentencesDB(fname)
                else:
                    sentences = MySentencesDB(fname)
            elif (args.alg == 'pv-dbow' or args.alg == 'pv-dm'):
                sentences = MyDocumentsDB(fname)
        elif (fname.endswith('.dat')):
            if (args.alg == 'sg' or args.alg == 'cbow'):
                sentences = MySentencesDat(fname)
            elif (args.alg == 'pv-dbow' or args.alg == 'pv-dm'):
                sentences = MyDocumentsDat(fname)

        out_name = fname + '_'+str(args.dim)+'_'+str(args.win)+'_'+str(args.epochs)+'_'+args.alg+'.vect'
        # we force min_count to 1 in order not to miss any item

        if (args.alg == 'sg' or args.alg == 'cbow'):
            model = gensim.models.Word2Vec(vector_size=args.dim, workers=args.workers, window=args.win,
                                    sg=(1 if args.alg == 'sg' else 0), negative=15, epochs=args.epochs, min_count=1)
        elif (args.alg == 'pv-dbow' or args.alg == 'pv-dm'):
            model = gensim.models.doc2vec.Doc2Vec(vector_size=args.dim, workers=args.workers, window=args.win,
                                                  dm=(1 if args.alg=='pv-dm' else 0), negative=15, epochs=args.epochs, min_count=1)
        model.build_vocab(sentences, progress_per=10000)
        start_time = time.time()
        model.train(sentences, total_examples=model.corpus_count, epochs=model.epochs, report_delay=1)
        end_time = time.time()

        model.save(out_name)
        with open(out_name + '-times', 'w+') as out:
            print(str(end_time - start_time))
            out.write(' time to train: ' + str(end_time - start_time))