#!/bin/bash

PROJECT_ID="hw-2-486907"
ZONE="us-central1-a"

echo "Setting project..."
gcloud config set project $PROJECT_ID

echo "Creating firewall rules..."

gcloud compute firewall-rules create allow-8080 \
--allow tcp:8080 \
--target-tags web-server \
--quiet || true

gcloud compute firewall-rules create allow-5001 \
--allow tcp:5001 \
--target-tags second-service \
--quiet || true


echo "Creating second service VM..."

gcloud compute instances create hw4-second-service \
--zone=$ZONE \
--machine-type=e2-micro \
--tags=second-service \
--image-family=debian-11 \
--image-project=debian-cloud \
--metadata=startup-script='#! /bin/bash
apt update
apt install -y python3-pip
pip3 install flask
cat <<EOF > second_service.py
from flask import Flask, request
app = Flask(__name__)
@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json()
    print("FORBIDDEN REQUEST FROM", data, flush=True)
    return "received", 200
app.run(host="0.0.0.0", port=5001)
EOF
python3 second_service.py'



echo "Creating web server VM..."

gcloud compute instances create hw4-web-server \
--zone=$ZONE \
--machine-type=e2-micro \
--tags=web-server \
--scopes=https://www.googleapis.com/auth/devstorage.read_only \
--image-family=debian-11 \
--image-project=debian-cloud \
--metadata-from-file startup-script=startup_script.sh


echo "Deployment complete!"
echo "Wait about 60 seconds for servers to start."
echo "Then access your web server using:"
echo "http://<WEB_SERVER_EXTERNAL_IP>:8080/page1.txt"
