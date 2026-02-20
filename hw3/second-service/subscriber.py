import json
from google.cloud import pubsub_v1
from google.cloud import storage

PROJECT_ID = "hw-2-486907"
SUBSCRIPTION_NAME = "ankith-hw3-sub"
BUCKET_NAME = "hw-2-486907-ankith07-pagerank-001"
LOG_FILE_PATH = "forbidden-logs/forbidden_requests.txt"

subscriber = pubsub_v1.SubscriberClient()
storage_client = storage.Client()

subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)

def callback(message):
    data = json.loads(message.data.decode("utf-8"))

    log_message = (
        f"FORBIDDEN ACCESS: "
        f"Country={data['country']} "
        f"File={data['file']} "
        f"Timestamp={data['timestamp']}\n"
    )

    print(log_message)

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(LOG_FILE_PATH)

    existing_content = ""
    if blob.exists():
        existing_content = blob.download_as_text()

    blob.upload_from_string(existing_content + log_message)

    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print("Listening for forbidden messages...")

try:
    streaming_pull_future.result()
except KeyboardInterrupt:
    streaming_pull_future.cancel()
