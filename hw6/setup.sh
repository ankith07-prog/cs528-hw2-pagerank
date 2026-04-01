#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
ZONE="us-central1-a"
REGION="us-central1"

SQL_INSTANCE="hw5-sql"
SQL_DB="hw5db"
SQL_USER="hw5user"
SQL_PASSWORD="hw5pass123"

BUCKET_NAME="hw-2-486907-ankith07-pagerank-001"

HW6_VM="hw6-model-vm"

gcloud config set project "$PROJECT_ID"

echo "Ensuring required services are enabled..."
gcloud services enable compute.googleapis.com sqladmin.googleapis.com storage.googleapis.com

echo "Getting Cloud SQL IP..."
DB_HOST=$(gcloud sql instances describe "$SQL_INSTANCE" --format="value(ipAddresses[0].ipAddress)")
echo "DB_HOST=$DB_HOST"

echo "Authorizing current Cloud Shell IP for Cloud SQL..."
MY_IP=$(curl -s ifconfig.me)
echo "MY_IP=$MY_IP"
gcloud sql instances patch "$SQL_INSTANCE" \
  --authorized-networks="${MY_IP}/32" \
  --quiet

echo "Deleting old HW6 VM if it exists..."
gcloud compute instances delete "$HW6_VM" --zone="$ZONE" --quiet >/dev/null 2>&1 || true

echo "Creating HW6 VM..."
gcloud compute instances create "$HW6_VM" \
  --zone="$ZONE" \
  --machine-type=e2-standard-2 \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata=DB_HOST="$DB_HOST",DB_USER="$SQL_USER",DB_PASSWORD="$SQL_PASSWORD",DB_NAME="$SQL_DB",BUCKET_NAME="$BUCKET_NAME" \
  --metadata-from-file startup-script=hw6/startup.sh

echo "Waiting for VM startup to finish..."
sleep 120

echo "Listing HW6 outputs in bucket..."
gcloud storage ls "gs://$BUCKET_NAME/hw6/" || true

echo
echo "===== hw6_summary.txt ====="
gcloud storage cp "gs://$BUCKET_NAME/hw6/hw6_summary.txt" - || true

echo
echo "===== model1_ip_to_country_test_output.csv (first 10 lines) ====="
gcloud storage cp "gs://$BUCKET_NAME/hw6/model1_ip_to_country_test_output.csv" - 2>/dev/null | head -10 || true

echo
echo "===== model2_income_test_output.csv (first 10 lines) ====="
gcloud storage cp "gs://$BUCKET_NAME/hw6/model2_income_test_output.csv" - 2>/dev/null | head -10 || true

echo
echo "HW6 setup complete."
echo "When finished, run: bash hw6/cleanup.sh"
