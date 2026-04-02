#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
ZONE="us-central1-c"
HW6_VM="hw6-model-vm"

gcloud config set project "$PROJECT_ID"

echo "Deleting HW6 VM if it exists..."
if gcloud compute instances describe "$HW6_VM" --zone="$ZONE" >/dev/null 2>&1; then
  gcloud compute instances delete "$HW6_VM" --zone="$ZONE" --quiet
  echo "Deleted $HW6_VM."
else
  echo "$HW6_VM not found in $ZONE."
fi

echo "HW6 cleanup complete."