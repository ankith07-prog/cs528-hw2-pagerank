#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
ZONE="us-central1-a"
HW6_VM="hw6-model-vm"

gcloud config set project "$PROJECT_ID"

gcloud compute instances delete "$HW6_VM" --zone="$ZONE" --quiet >/dev/null 2>&1 || true

echo "HW6 cleanup complete."
