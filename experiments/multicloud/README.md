# Multicloud utilities for experiments

This folder contains lightweight scripts to upload/download experiment artifacts using pca.multicloud.MultiCloudStore.

Quick examples:

# upload local file to cloud
python experiments/multicloud/upload_to_cloud.py --provider s3 --bucket my-bucket --local experiments/out/llm_preds.jsonl --remote runs/demo/llm_preds.jsonl

# download from cloud to local
python experiments/multicloud/download_from_cloud.py --provider gcs --bucket my-gcs-bucket --remote runs/demo/llm_preds.jsonl --local experiments/out/llm_preds_from_gcs.jsonl

Credentials:
- AWS: set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (or rely on default credentials)
- GCP: set GOOGLE_APPLICATION_CREDENTIALS to service account json or rely on ADC
- Azure: set AZURE_STORAGE_CONNECTION_STRING or provide account_url + AZURE_STORAGE_KEY

See top-level README for more provider details.
