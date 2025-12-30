#!/usr/bin/env python3
"""
Upload a local file to cloud using pca.multicloud.MultiCloudStore or direct OCI SDK.
Supports s3, gcs, azure via MultiCloudStore; OCI via oci SDK.
"""
import argparse
import os
from pathlib import Path

from pca.multicloud import MultiCloudStore

def upload_with_oci(local, bucket, remote, oci_namespace=None, config_file=None, profile=None):
    import oci
    # load config
    if config_file:
        cfg = oci.config.from_file(config_file, profile or "DEFAULT")
    else:
        # prefer env-based or default config
        try:
            cfg = oci.config.from_file(profile=profile or "DEFAULT")
        except Exception:
            cfg = oci.config.from_env()  # fallback
    client = oci.object_storage.ObjectStorageClient(cfg)
    if not oci_namespace:
        oci_namespace = client.get_namespace().data
    with open(local, "rb") as fh:
        client.put_object(oci_namespace, bucket, remote, fh)
    return f"oci://{oci_namespace}/{bucket}/{remote}"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True, choices=["s3", "gcs", "azure", "oci", "gcp"])
    p.add_argument("--bucket", required=True)
    p.add_argument("--local", required=True)
    p.add_argument("--remote", required=True)
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

    if not os.path.exists(args.local):
        raise SystemExit("Local file not found: " + args.local)

    if provider == "oci":
        url = upload_with_oci(args.local, args.bucket, args.remote, oci_namespace=args.oci_namespace, config_file=args.oci_config_file, profile=args.oci_profile)
        print("Uploaded to:", url)
        return

    store = MultiCloudStore(provider=provider, bucket=args.bucket, project=args.project, account_url=args.account_url)
    url = store.upload(args.local, args.remote)
    print("Uploaded to:", url)

if _name_ == "_main_":
    main()
