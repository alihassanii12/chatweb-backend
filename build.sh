#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip and install setuptools first
pip install --upgrade pip setuptools wheel

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
