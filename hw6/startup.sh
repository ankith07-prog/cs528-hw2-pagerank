#!/bin/bash
set -e

apt-get update
apt-get install -y python3-pip python3-venv git default-mysql-client curl ca-certificates

DB_HOST=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/DB_HOST)
DB_USER=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/DB_USER)
DB_PASSWORD=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/DB_PASSWORD)
DB_NAME=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/DB_NAME)
BUCKET_NAME=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/BUCKET_NAME)
PROJECT_ID=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/PROJECT_ID)

export DB_HOST
export DB_USER
export DB_PASSWORD
export DB_NAME
export BUCKET_NAME
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GCLOUD_PROJECT="$PROJECT_ID"

cd /root

if [ ! -d cs528-hw2-pagerank ]; then
  git clone https://github.com/ankith07-prog/cs528-hw2-pagerank.git
fi

cd cs528-hw2-pagerank

python3 -m venv /root/hw6-venv
source /root/hw6-venv/bin/activate

pip install --upgrade pip
pip install -r hw6/requirements.txt

python hw6/run_hw6.py | tee /root/hw6_run.log

# Upload outputs automatically using gcloud CLI instead of Python storage client
if [ -f /root/hw6_outputs/model1_ip_to_country_test_output.csv ]; then
  gcloud storage cp /root/hw6_outputs/model1_ip_to_country_test_output.csv "gs://${BUCKET_NAME}/hw6/"
fi

if [ -f /root/hw6_outputs/model2_income_test_output.csv ]; then
  gcloud storage cp /root/hw6_outputs/model2_income_test_output.csv "gs://${BUCKET_NAME}/hw6/"
fi

if [ -f /root/hw6_outputs/hw6_summary.txt ]; then
  gcloud storage cp /root/hw6_outputs/hw6_summary.txt "gs://${BUCKET_NAME}/hw6/"
fi