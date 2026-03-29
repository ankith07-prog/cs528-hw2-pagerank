#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
ZONE="us-central1-a"
SQL_INSTANCE="hw5-sql"
WEB_VM="hw5-web-server"
SECOND_VM="hw5-second-service"

gcloud config set project "$PROJECT_ID"

echo "Deleting HW5 web server VM if it exists..."
gcloud compute instances delete "$WEB_VM" --zone="$ZONE" --quiet >/dev/null 2>&1 || true

echo "Deleting HW5 second service VM if it exists..."
gcloud compute instances delete "$SECOND_VM" --zone="$ZONE" --quiet >/dev/null 2>&1 || true

echo "Deleting firewall rule allow-hw5-8080 if it exists..."
gcloud compute firewall-rules delete allow-hw5-8080 --quiet >/dev/null 2>&1 || true

echo "Deleting firewall rule allow-hw5-5001 if it exists..."
gcloud compute firewall-rules delete allow-hw5-5001 --quiet >/dev/null 2>&1 || true

echo "Stopping Cloud SQL instance if it exists..."
if gcloud sql instances describe "$SQL_INSTANCE" >/dev/null 2>&1; then
  gcloud sql instances patch "$SQL_INSTANCE" --activation-policy=NEVER --quiet
else
  echo "Cloud SQL instance does not exist."
fi

echo "Cleanup complete."
