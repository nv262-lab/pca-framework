#!/usr/bin/env python3
"""
Download a remote key from cloud to a local path using pca.multicloud.MultiCloudStore or OCI SDK.
"""
import argparse
from pathlib import Path

from pca.multicloud import MultiCloudStore

def download_with_oci(local, bucket, remote, oci_namespace=None, config_file=None, profile=None):
    import oci
    if config_file:
        cfg = oci.config.from_file(config_file, profile or "DEFAULT")
    else:
        try:
            cfg = oci.config.from_file(profile=profile or "DEFAULT")
        except Exception:
            cfg = oci.config.from_env()
    client = oci.object_storage.ObjectStorageClient(cfg)
    if not oci_namespace:
        oci_namespace = client.get_namespace().data
    resp = client.get_object(oci_namespace, bucket, remote)
    Path(local).parent.mkdir(parents=True, exist_ok=True)
    with open(local, "wb") as fh:
        for chunk in resp.data.raw.stream(1024*1024, decode_content=False):
            fh.write(chunk)
    return local

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True, choices=["s3", "gcs", "azure", "oci", "gcp"])
    p.add_argument("--bucket", required=True)
    p.add_argument("--remote", required=True)
    p.add_argument("--local", required=True)
    p.add_argument("--project", default=None)
    p.add_argument("--account_url", default=None)
    # OCI specific
    p.add_argument("--oci-namespace", default=None)
    p.add_argument("--oci-config-file", default=None)
    p.add_argument("--oci-profile", default=None)
    args = p.parse_args()

    provider = args.provider
    if provider == "gcp":
        provider = "gcs"

    if provider == "oci":
        out = download_with_oci(args.local, args.bucket, args.remote, oci_namespace=args.oci_namespace, config_file=args.oci_config_file, profile=args.oci_profile)
        print("Downloaded to:", out)
        return

    store = MultiCloudStore(provider=provider, bucket=args.bucket, project=args.project, account_url=args.account_url)
    out = store.download(args.remote, args.local)
    print("Downloaded to:", out)

if _name_ == "_main_":
    main()
