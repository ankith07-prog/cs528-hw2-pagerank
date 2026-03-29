#!/bin/bash
set -e

LOCK_FILE="/var/log/hw5_second_service_startup_done"

if [ -f "$LOCK_FILE" ]; then
  echo "HW5 second service startup script already ran. Skipping."
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update || true
dpkg --configure -a || true
apt-get install -f -y || true
apt-get update
apt-get install -y python3 python3-pip

pip3 install --break-system-packages flask

cat <<'EOF' > /second_service.py
from flask import Flask, request

app = Flask(__name__)

@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json()
    print("FORBIDDEN REQUEST FROM", data, flush=True)
    return "received", 200

app.run(host="0.0.0.0", port=5001)
EOF

python3 /second_service.py > /var/log/hw5_second_service.log 2>&1 &

touch "$LOCK_FILE"
