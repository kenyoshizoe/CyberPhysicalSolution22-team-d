#! /usr/bin/bash
sudo apt update
sudo apt -y install python3-venv zbar-tools

python3 -m venv env
source env/bin/activate

pip3 install -r requirements.txt
