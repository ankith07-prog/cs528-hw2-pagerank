#!/bin/bash
set -e

apt-get update
apt-get install -y python3-pip python3-venv git default-mysql-client curl

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

export DB_HOST
export DB_USER
export DB_PASSWORD
export DB_NAME
export BUCKET_NAME

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
