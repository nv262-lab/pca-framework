#!/usr/bin/env python3
"""
Download a remote key from cloud to a local path using pca.multicloud.MultiCloudStore
"""
import argparse
from pca.multicloud import MultiCloudStore

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True, choices=["s3", "gcs", "azure"])
    p.add_argument("--bucket", required=True)
    p.add_argument("--remote", required=True)
    p.add_argument("--local", required=True)
    p.add_argument("--project", default=None)
    p.add_argument("--account_url", default=None)
    args = p.parse_args()

    store = MultiCloudStore(provider=args.provider, bucket=args.bucket, project=args.project, account_url=args.account_url)
    out = store.download(args.remote, args.local)
    print("Downloaded to:", out)

if _name_ == "_main_":
    main()
