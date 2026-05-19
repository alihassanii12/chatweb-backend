#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip and install setuptools first
pip install --upgrade pip setuptools wheel

pip install -r requirements.txt

# Create staticfiles directory if it doesn't exist
mkdir -p staticfiles

python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input
