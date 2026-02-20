import json
from datetime import datetime
from google.cloud import storage
from google.cloud import pubsub_v1

PROJECT_ID = "hw-2-486907"
BUCKET = "hw-2-486907-ankith07-pagerank-001"
TOPIC = "ankith-hw3-topic"

FORBIDDEN_COUNTRIES = {
    "North Korea", "Iran", "Cuba", "Myanmar", "Iraq",
    "Libya", "Sudan", "Zimbabwe", "Syria"
}

storage_client = storage.Client()
publisher = pubsub_v1.PublisherClient()

def http_handler(request):
    method = request.method
    file_name = request.args.get("file")
    country = request.headers.get("X-country")

    if country and country in FORBIDDEN_COUNTRIES:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "country": country,
            "file": file_name
        }

        try:
            topic_path = publisher.topic_path(PROJECT_ID, TOPIC)
            publisher.publish(
                topic_path,
                json.dumps(payload).encode("utf-8")
            )
            print(f"FORBIDDEN REQUEST from {country} for file {file_name}")
        except Exception as e:
            print(f"PUBLISH FAILED: {str(e)}")

        return ("Permission denied\n", 400)

    if method != "GET":
        print(f"METHOD NOT IMPLEMENTED: {method} for file {file_name}")
        return ("Not implemented\n", 501)

    if not file_name:
        print("NO FILE PARAMETER PROVIDED")
        return ("Not found\n", 404)

    bucket = storage_client.bucket(BUCKET)
    blob = bucket.blob(file_name)

    if not blob.exists():
        print(f"FILE NOT FOUND: {file_name}")
        return ("Not found\n", 404)

    content = blob.download_as_text()
    print(f"FILE SERVED SUCCESSFULLY: {file_name}")
    return (content, 200)
