from gensim.test.utils import datapath, get_tmpfile
from gensim.models import KeyedVectors
from gensim.scripts.glove2word2vec import glove2word2vec
import sys 
import os
if __name__ == '__main__': 
	glove_file = sys.argv[1]
	tmp_file = sys.argv[1].replace(".gloveVect.txt", ".w2v.vect")
	glove2word2vec(glove_file, tmp_file)

