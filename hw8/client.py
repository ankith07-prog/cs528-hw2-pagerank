import requests
import sys
import time
from collections import Counter

if len(sys.argv) < 2:
    print("Usage: python3 client.py <lb_ip> [path]")
    sys.exit(1)

lb_ip = sys.argv[1]
path = sys.argv[2] if len(sys.argv) > 2 else "/pages/page_17162.txt"
url = f"http://{lb_ip}:8080{path}"

counts = Counter()
start = time.time()

while True:
    try:
        r = requests.get(url, timeout=5)
        zone = r.headers.get("X-Zone", "missing-zone")
        counts[zone] += 1
        print(f"[{int(time.time()-start):4d}s] status={r.status_code} zone={zone} counts={dict(counts)}")
    except Exception as e:
        print(f"[{int(time.time()-start):4d}s] ERROR {e}")
    time.sleep(1)