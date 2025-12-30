"""
Compatibility wrapper for top-level pca usage within pp_core.
Re-exports the pca package objects for from pp_core.pca import ... style imports.
"""
from pca import TfidfIndexer, poison_corpus, iter_corpus, MultiCloudStore

_all_ = ["TfidfIndexer", "poison_corpus", "iter_corpus", "MultiCloudStore"]
