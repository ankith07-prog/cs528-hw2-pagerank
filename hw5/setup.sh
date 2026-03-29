#!/bin/bash
set -e

PROJECT_ID="hw-2-486907"
ZONE="us-central1-a"
REGION="us-central1"

WEB_VM="hw5-web-server"
SECOND_VM="hw5-second-service"
SQL_INSTANCE="hw5-sql"
SQL_DB="hw5db"
SQL_USER="hw5user"
SQL_PASSWORD="hw5pass123"
WEB_SERVER_SA="hw4-server-sa@hw-2-486907.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"

echo "Enabling required services..."
gcloud services enable compute.googleapis.com sqladmin.googleapis.com cloudfunctions.googleapis.com cloudscheduler.googleapis.com cloudbuild.googleapis.com run.googleapis.com

echo "Creating Cloud SQL instance if needed..."
if ! gcloud sql instances describe "$SQL_INSTANCE" >/dev/null 2>&1; then
  gcloud sql instances create "$SQL_INSTANCE" \
    --database-version=MYSQL_8_0 \
    --cpu=1 \
    --memory=3840MB \
    --region="$REGION" \
    --root-password="$SQL_PASSWORD"
else
  echo "Cloud SQL instance already exists."
fi

echo "Ensuring database exists..."
if ! gcloud sql databases describe "$SQL_DB" --instance="$SQL_INSTANCE" >/dev/null 2>&1; then
  gcloud sql databases create "$SQL_DB" --instance="$SQL_INSTANCE"
else
  echo "Database already exists."
fi

echo "Ensuring SQL user exists..."
if ! gcloud sql users list --instance="$SQL_INSTANCE" --format="value(name)" | grep -qx "$SQL_USER"; then
  gcloud sql users create "$SQL_USER" \
    --instance="$SQL_INSTANCE" \
    --password="$SQL_PASSWORD"
else
  echo "SQL user already exists."
fi

echo "Getting Cloud SQL IP..."
DB_HOST=$(gcloud sql instances describe "$SQL_INSTANCE" --format="value(ipAddresses[0].ipAddress)")
echo "DB_HOST=$DB_HOST"

echo "Authorizing current Cloud Shell IP for Cloud SQL..."
MY_IP=$(curl -s ifconfig.me)
echo "MY_IP=$MY_IP"
gcloud sql instances patch "$SQL_INSTANCE" \
  --authorized-networks="${MY_IP}/32" \
  --quiet

echo "Running schema setup through mysql client..."
sudo apt-get update
sudo apt-get install -y mysql-client

cat <<EOF > /tmp/hw5_schema.sql
CREATE DATABASE IF NOT EXISTS ${SQL_DB};
USE ${SQL_DB};

CREATE TABLE IF NOT EXISTS request_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    country VARCHAR(100),
    client_ip VARCHAR(100),
    gender VARCHAR(50),
    age INT NULL,
    income VARCHAR(100),
    is_banned BOOLEAN,
    time_of_day VARCHAR(50),
    requested_file VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS error_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    requested_file VARCHAR(255),
    error_code INT
);
EOF

mysql --host="$DB_HOST" --user="$SQL_USER" --password="$SQL_PASSWORD" < /tmp/hw5_schema.sql
rm -f /tmp/hw5_schema.sql

echo "Deleting old HW5 VMs if they already exist..."
gcloud compute instances delete "$WEB_VM" --zone="$ZONE" --quiet >/dev/null 2>&1 || true
gcloud compute instances delete "$SECOND_VM" --zone="$ZONE" --quiet >/dev/null 2>&1 || true

echo "Creating second service VM..."
gcloud compute instances create "$SECOND_VM" \
  --zone="$ZONE" \
  --machine-type=e2-micro \
  --tags=http-server \
  --no-address \
  --metadata-from-file startup-script=hw5/second_service_startup.sh

echo "Getting second service internal IP..."
SECOND_VM_INTERNAL_IP=$(gcloud compute instances describe "$SECOND_VM" \
  --zone="$ZONE" \
  --format='get(networkInterfaces[0].networkIP)')
echo "SECOND_VM_INTERNAL_IP=$SECOND_VM_INTERNAL_IP"

echo "Creating web server VM..."
gcloud compute instances create "$WEB_VM" \
  --zone="$ZONE" \
  --machine-type=e2-micro \
  --tags=http-server \
  --service-account="$WEB_SERVER_SA" \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata=PROJECT_ID="$PROJECT_ID",DB_HOST="$DB_HOST",DB_USER="$SQL_USER",DB_PASSWORD="$SQL_PASSWORD",DB_NAME="$SQL_DB",ALERT_SERVICE_URL="http://$SECOND_VM_INTERNAL_IP:5001/alert" \
  --metadata-from-file startup-script=hw5/startup.sh

echo "Ensuring firewall for 8080 exists..."
gcloud compute firewall-rules create allow-hw5-8080 \
  --allow=tcp:8080 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server >/dev/null 2>&1 || true

echo "Ensuring firewall for 5001 exists..."
gcloud compute firewall-rules create allow-hw5-5001 \
  --allow=tcp:5001 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server >/dev/null 2>&1 || true

echo "Setup complete."
echo "Web server external IP:"
gcloud compute instances describe "$WEB_VM" --zone="$ZONE" --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

echo "Second service internal IP:"
echo "$SECOND_VM_INTERNAL_IP"
