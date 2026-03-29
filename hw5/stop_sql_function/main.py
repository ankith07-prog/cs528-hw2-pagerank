import os
import requests

PROJECT_ID = os.environ.get("PROJECT_ID", "hw-2-486907")
INSTANCE_ID = os.environ.get("INSTANCE_ID", "hw5-sql")

def stop_sql(request):
    metadata_url = (
        "http://metadata.google.internal/computeMetadata/v1/"
        "instance/service-accounts/default/token"
    )
    headers = {"Metadata-Flavor": "Google"}

    token_resp = requests.get(metadata_url, headers=headers, timeout=10)
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]

    url = (
        f"https://sqladmin.googleapis.com/sql/v1beta4/projects/"
        f"{PROJECT_ID}/instances/{INSTANCE_ID}/stop"
    )

    api_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=api_headers, timeout=30)

    return (
        f"Stop request sent for Cloud SQL instance {INSTANCE_ID}. "
        f"Status code: {resp.status_code}. Response: {resp.text}",
        200,
    )

