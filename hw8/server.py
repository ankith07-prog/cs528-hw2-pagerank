from flask import Flask, Response, request
from google.cloud import storage
import logging
import requests
import os
import socket
from urllib.request import urlopen

app = Flask(__name__)

BUCKET_NAME = os.environ.get("BUCKET_NAME", "hw-2-486907-ankith07-pagerank-001")
REPORT_URL = os.environ.get("REPORT_URL", "")
FORBIDDEN_COUNTRIES = {
    "North Korea", "Iran", "Cuba", "Myanmar", "Iraq", "Libya",
    "Sudan", "Zimbabwe", "Syria"
}

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)


def get_zone():
    try:
        url = "http://metadata.google.internal/computeMetadata/v1/instance/zone"
        req = requests.get(url, headers={"Metadata-Flavor": "Google"}, timeout=2)
        if req.status_code == 200:
            return req.text.split("/")[-1]
    except Exception:
        pass
    return "unknown-zone"


def build_response(body, status_code=200, content_type="text/plain"):
    resp = Response(body, status=status_code, content_type=content_type)
    resp.headers["X-Zone"] = get_zone()
    resp.headers["X-Hostname"] = socket.gethostname()
    return resp


@app.route("/<path:filename>", methods=["GET"])
def serve_file(filename):
    country = request.headers.get("X-country", "")

    if country in FORBIDDEN_COUNTRIES:
        logging.critical(f"FORBIDDEN REQUEST from {country} for file {filename}")
        if REPORT_URL:
            try:
                requests.post(
                    REPORT_URL,
                    json={"country": country, "file": filename},
                    timeout=2
                )
            except Exception as e:
                logging.error(f"Failed to report forbidden request: {e}")
        return build_response("Permission denied\n", 400)

    blob = bucket.blob(filename)
    if not blob.exists():
        logging.warning(f"404 request for file {filename}")
        return build_response("Not found\n", 404)

    data = blob.download_as_text()
    return build_response(data, 200)


@app.route("/", methods=["GET"])
def root():
    return build_response("HW8 web server is running\n", 200)


@app.errorhandler(405)
def method_not_allowed(e):
    logging.warning("501 method not implemented")
    return build_response("Not implemented\n", 501)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)