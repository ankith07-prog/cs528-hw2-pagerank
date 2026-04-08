#!/bin/bash
set -euo pipefail

PROJECT_ID="hw-2-486907"
BUCKET="hw-2-486907-ankith07-pagerank-001"
INPUT="gs://${BUCKET}/pages/*.txt"
BASE_OUTPUT="gs://${BUCKET}/hw7-output"
BASE_TEMP="gs://${BUCKET}/hw7-temp"
BASE_STAGING="gs://${BUCKET}/hw7-staging"
MACHINE_TYPE="e2-medium"

# Same-region region/zone pairs only.
CANDIDATES=(
  "us-east1 us-east1-c"
  "us-east1 us-east1-b"
  "us-east4 us-east4-b"
  "us-east4 us-east4-c"
  "us-west1 us-west1-b"
  "us-west1 us-west1-c"
  "us-central1 us-central1-f"
)

echo "Installing dependencies..."
python3 -m pip install --user -r hw7/requirements.txt

echo "Enabling required services..."
gcloud services enable dataflow.googleapis.com compute.googleapis.com storage.googleapis.com

for pair in "${CANDIDATES[@]}"; do
  REGION=$(echo "$pair" | awk '{print $1}')
  WORKER_ZONE=$(echo "$pair" | awk '{print $2}')
  TS=$(date +%Y%m%d-%H%M%S)
  JOB_NAME="hw7-${TS}"
  OUTPUT="${BASE_OUTPUT}/${REGION}-${WORKER_ZONE}-${TS}"
  TEMP_LOCATION="${BASE_TEMP}/${REGION}-${WORKER_ZONE}-${TS}"
  STAGING_LOCATION="${BASE_STAGING}/${REGION}-${WORKER_ZONE}-${TS}"

  echo
  echo "=================================================="
  echo "Trying REGION=${REGION} WORKER_ZONE=${WORKER_ZONE}"
  echo "JOB_NAME=${JOB_NAME}"
  echo "OUTPUT=${OUTPUT}"
  echo "=================================================="

  set +e
  python3 hw7/src/hw7_pipeline.py \
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
  STATUS=$?
  set -e

  if [ $STATUS -eq 0 ]; then
    echo
    echo "Submitted successfully."
    echo "Region: ${REGION}"
    echo "Worker zone: ${WORKER_ZONE}"
    echo "Output: ${OUTPUT}"
    echo
    echo "Check job status:"
    echo "gcloud dataflow jobs list --region=${REGION}"
    echo
    echo "Check results after it finishes:"
    echo "gsutil cat ${OUTPUT}/outgoing_top5/result"
    echo "gsutil cat ${OUTPUT}/incoming_top5/result"
    echo "gsutil cat ${OUTPUT}/bigrams_top5/result"
    exit 0
  fi

  echo "Submission/run failed for ${REGION} / ${WORKER_ZONE}. Trying next candidate..."
done

echo "All candidate region/zone pairs failed due to capacity or submission issues."
exit 1