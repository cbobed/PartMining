"""
All-but-the-Top: Simple and Effective Postprocessing for Word Representations
Paper: https://arxiv.org/abs/1702.01417
Last Updated: Fri 15 Nov 2019 11:47:00 AM CET
**Prior version had serious issues, please excuse any inconveniences.**
"""
import numpy as np
from sklearn.decomposition import PCA

def all_but_the_top(v, D):
	"""
	Arguments:
	:v: word vectors of shape (n_words, n_dimensions)
	:D: number of principal components to subtract
	"""
	# 1. Subtract mean vector
	v_tilde = v - np.mean(v, axis=0)
	# 2. Compute the first `D` principal components
	#    on centered embedding vectors
	u = PCA(n_components=D).fit(v_tilde).components_  # [D, emb_size]
	# Subtract first `D` principal components
	# [vocab_size, emb_size] @ [emb_size, D] @ [D, emb_size] -> [vocab_size, emb_size]
	return v_tilde - (v @ u.T @ u)


def top_but_the_all(v, D):
	"""
	Arguments:
	:v: word vectors of shape (n_words, n_dimensions)
	:D: number of principal components to subtract
	"""
	# 1. Subtract mean vector
	v_tilde = v - np.mean(v, axis=0)
	# 2. Compute the first `D` principal components
	#    on centered embedding vectors
	u = PCA().fit(v_tilde).components_  # [emb_size, emb_size]
	u_rest = u[D:,]
	# Subtract first `D` principal components
	# [vocab_size, emb_size] @ [emb_size, emb_size-D] @ [emb_size-D, emb_size] -> [vocab_size, emb_size]
	return v_tilde - (v @ u_rest.T @ u_rest)