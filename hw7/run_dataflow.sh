#!/bin/bash
set -euo pipefail

PROJECT_ID="hw-2-486907"
BUCKET="hw-2-486907-ankith07-pagerank-001"

REGION="us-west1"
WORKER_ZONE="us-west1-c"
MACHINE_TYPE="e2-small"

INPUT="gs://${BUCKET}/pages/*.txt"
TS=$(date +%Y%m%d-%H%M%S)
OUTPUT="gs://${BUCKET}/hw7-output/${REGION}-${WORKER_ZONE}-${TS}"
TEMP_LOCATION="gs://${BUCKET}/hw7-temp/${REGION}-${WORKER_ZONE}-${TS}"
STAGING_LOCATION="gs://${BUCKET}/hw7-staging/${REGION}-${WORKER_ZONE}-${TS}"
JOB_NAME="hw7-${TS}"

python3 -m pip install --user -r hw7/requirements.txt

gcloud services enable dataflow.googleapis.com compute.googleapis.com storage.googleapis.com

time python3 hw7/src/hw7_pipeline.py \
  --input "${INPUT}" \
  --output "${OUTPUT}" \
  --runner DataflowRunner \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --worker_zone "${WORKER_ZONE}" \
  --machine_type "${MACHINE_TYPE}" \
  --num_workers 1 \
  --max_num_workers 1 \
  --temp_location "${TEMP_LOCATION}" \
  --staging_location "${STAGING_LOCATION}" \
  --job_name "${JOB_NAME}"

echo "Output path: ${OUTPUT}"