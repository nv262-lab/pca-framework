Multi-cloud usage for experiments
--------------------------------

See top-level docs. Short examples:

from pca import MultiCloudStore
store = MultiCloudStore(provider="s3", bucket="my-bucket")
store.upload("experiments/out/idx.pkl", "idxs/demo/idx.pkl")
