#!/bin/bash

apt update
apt install -y python3-pip

pip3 install google-cloud-storage flask requests

cat <<EOF > server.py
from flask import Flask, Response, request
from google.cloud import storage
import logging
import requests

app = Flask(__name__)

BUCKET_NAME = "hw-2-486907-ankith07-pagerank-001"
storage_client = storage.Client()

FORBIDDEN_COUNTRIES = [
"North Korea","Iran","Cuba","Myanmar",
"Iraq","Libya","Sudan","Zimbabwe","Syria"
]

@app.route('/<path:filename>', methods=['GET'])
def get_file(filename):

    country = request.headers.get("X-country")

    if country in FORBIDDEN_COUNTRIES:
        logging.critical(f"Forbidden request from {country}")

        requests.post(
            "http://10.128.0.4:5001/alert",
            json={"country": country}
        )

        return Response("Forbidden", status=403)

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("pages/" + filename)

    if blob.exists():
        data = blob.download_as_text()
        return Response(data, status=200, mimetype='text/plain')
    else:
        logging.warning("404 request")
        return Response("File not found", status=404)

@app.errorhandler(405)
def method_not_allowed(e):
    logging.warning("501 method not implemented")
    return Response("Not implemented", status=501)

app.run(host="0.0.0.0", port=8080)
EOF

python3 server.py
