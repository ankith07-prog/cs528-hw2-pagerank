#!/bin/bash
set -e

apt-get update
apt-get install -y python3-pip python3-venv git default-mysql-client

cd /root

if [ ! -d cs528-hw2-pagerank ]; then
  git clone https://github.com/ankith07-prog/cs528-hw2-pagerank.git
fi

cd cs528-hw2-pagerank

python3 -m venv /root/hw6-venv
source /root/hw6-venv/bin/activate

pip install --upgrade pip
pip install -r hw6/requirements.txt

python hw6/run_hw6.py | tee /root/hw6_run.log
