import requests
import time

SERVER_IP = "34.170.140.10"
DURATION_SECONDS = 180
TIMEOUT_SECONDS = 5

pages = [f"/page_{i}.txt" for i in range(1, 101)]

status_counts = {}
failures = 0
total_requests = 0

start = time.time()

while time.time() - start < DURATION_SECONDS:
    for page in pages:
        if time.time() - start >= DURATION_SECONDS:
            break

        url = f"http://{SERVER_IP}:8080{page}"

        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            code = response.status_code
            status_counts[code] = status_counts.get(code, 0) + 1
        except Exception:
            failures += 1

        total_requests += 1

print("TOTAL_REQUESTS =", total_requests)
print("STATUS_COUNTS =", status_counts)
print("FAILURES =", failures)
