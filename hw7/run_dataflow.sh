#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
BUCKET="hw-2-486907-ankith07-pagerank-001"
REGION="us-central1"
WORKER_ZONE="us-central1-c"
MACHINE_TYPE="e2-standard-2"

INPUT="gs://${BUCKET}/pages/*.txt"
OUTPUT="gs://${BUCKET}/hw7-output"
TEMP_LOCATION="gs://${BUCKET}/hw7-temp"
STAGING_LOCATION="gs://${BUCKET}/hw7-staging"
JOB_NAME="hw7-$(date +%Y%m%d-%H%M%S)"

echo "Installing dependencies..."
python3 -m pip install --user -r hw7/requirements.txt

echo "Enabling required services..."
gcloud services enable dataflow.googleapis.com compute.googleapis.com storage.googleapis.com

echo "Removing old Dataflow output..."
gsutil -m rm -r "${OUTPUT}" || true

echo "Running HW7 pipeline on Dataflow..."
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

echo
echo "Dataflow job submitted."
echo "Job name: ${JOB_NAME}"
echo "Output path: ${OUTPUT}"