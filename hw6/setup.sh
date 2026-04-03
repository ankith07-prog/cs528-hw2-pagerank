#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
ZONE="us-central1-c"

SQL_INSTANCE="hw5-sql"
SQL_DB="hw5db"
SQL_USER="hw5user"
SQL_PASSWORD="hw5pass123"

BUCKET_NAME="hw-2-486907-ankith07-pagerank-001"
HW6_VM="hw6-model-vm"

gcloud config set project "$PROJECT_ID"

echo "Ensuring required services are enabled..."
gcloud services enable compute.googleapis.com sqladmin.googleapis.com storage.googleapis.com

echo "Starting / enabling Cloud SQL instance..."
gcloud sql instances patch "$SQL_INSTANCE" --activation-policy=ALWAYS --quiet

echo "Waiting for Cloud SQL instance to become RUNNABLE..."
while true; do
  SQL_STATUS=$(gcloud sql instances describe "$SQL_INSTANCE" --format="value(state)")
  echo "Cloud SQL state: $SQL_STATUS"
  if [ "$SQL_STATUS" = "RUNNABLE" ]; then
    break
  fi
  sleep 10
done

echo "Getting Cloud SQL IP..."
DB_HOST=$(gcloud sql instances describe "$SQL_INSTANCE" --format="value(ipAddresses[0].ipAddress)")
echo "DB_HOST=$DB_HOST"

echo "Getting current Cloud Shell IP..."
MY_IP=$(curl -s ifconfig.me)
echo "MY_IP=$MY_IP"

echo "Deleting old HW6 VM if it exists..."
gcloud compute instances delete "$HW6_VM" --zone="$ZONE" --quiet >/dev/null 2>&1 || true

echo "Creating HW6 VM..."
gcloud compute instances create "$HW6_VM" \
  --zone="$ZONE" \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata=PROJECT_ID="$PROJECT_ID",DB_HOST="$DB_HOST",DB_USER="$SQL_USER",DB_PASSWORD="$SQL_PASSWORD",DB_NAME="$SQL_DB",BUCKET_NAME="$BUCKET_NAME" \
  --metadata-from-file startup-script=hw6/startup.sh

VM_IP=$(gcloud compute instances describe "$HW6_VM" \
  --zone="$ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "VM_IP=$VM_IP"

echo "Authorizing both Cloud Shell IP and VM IP for Cloud SQL..."
gcloud sql instances patch "$SQL_INSTANCE" \
  --authorized-networks="${MY_IP}/32,${VM_IP}/32" \
  --quiet

echo "Waiting for HW6 outputs to appear in the bucket..."

MAX_TRIES=40
SLEEP_SECS=15
FOUND=0

for i in $(seq 1 $MAX_TRIES); do
  echo "Check $i/$MAX_TRIES..."
  if gcloud storage ls "gs://$BUCKET_NAME/hw6/" >/tmp/hw6_bucket_check.txt 2>/dev/null; then
    if grep -q "hw6_summary.txt\|model1_ip_to_country_test_output.csv\|model2_income_test_output.csv" /tmp/hw6_bucket_check.txt; then
      FOUND=1
      break
    fi
  fi
  sleep $SLEEP_SECS
done

if [ "$FOUND" -eq 1 ]; then
  echo "HW6 outputs found in bucket:"
  cat /tmp/hw6_bucket_check.txt
else
  echo "Timed out waiting for HW6 outputs in bucket."
  echo
  echo "You can inspect the VM with:"
  echo "gcloud compute ssh $HW6_VM --zone=$ZONE --command=\"journalctl -u google-startup-scripts.service --no-pager | tail -120\""
fi

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
echo "Deleting HW6 VM..."
gcloud compute instances delete "$HW6_VM" --zone="$ZONE" --quiet || true

echo "Stopping Cloud SQL instance..."
gcloud sql instances patch "$SQL_INSTANCE" --activation-policy=NEVER --quiet

echo
echo "HW6 setup complete."
echo "Database stopped and VM deleted."