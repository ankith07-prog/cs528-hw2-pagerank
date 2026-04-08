#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
BUCKET="hw-2-486907-ankith07-pagerank-001"
INPUT="gs://${BUCKET}/pages/*.txt"
OUTPUT_DIR="hw7/output/local"

echo "Removing old local output..."
rm -rf "${OUTPUT_DIR}"

echo "Installing dependencies..."
python3 -m pip install --user -r hw7/requirements.txt

echo "Running HW7 pipeline locally..."
time python3 hw7/src/hw7_pipeline.py \
  --input "${INPUT}" \
  --output "${OUTPUT_DIR}" \
  --runner DirectRunner

echo
echo "Local run complete. Results:"
echo "Outgoing top 5:"
cat "${OUTPUT_DIR}/outgoing_top5/result" || true
echo
echo "Incoming top 5:"
cat "${OUTPUT_DIR}/incoming_top5/result" || true
echo
echo "Bigrams top 5:"
cat "${OUTPUT_DIR}/bigrams_top5/result" || true