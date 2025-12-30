#!/usr/bin/env python3
"""
Upload a local file to cloud using pca.multicloud.MultiCloudStore
"""
import argparse
import os
from pca.multicloud import MultiCloudStore

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True, choices=["s3", "gcs", "azure"])
    p.add_argument("--bucket", required=True)
    p.add_argument("--local", required=True)
    p.add_argument("--remote", required=True)
    p.add_argument("--project", default=None)
    p.add_argument("--account_url", default=None)
    args = p.parse_args()

    if not os.path.exists(args.local):
        raise SystemExit("Local file not found: " + args.local)

    store = MultiCloudStore(provider=args.provider, bucket=args.bucket, project=args.project, account_url=args.account_url)
    url = store.upload(args.local, args.remote)
    print("Uploaded to:", url)

if _name_ == "_main_":
    main()
