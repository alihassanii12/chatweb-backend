#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip and install setuptools with pkg_resources support
pip install --upgrade pip
pip install "setuptools>=65.5.0" wheel

# Install all dependencies
pip install -r requirements.txt

# Run Django management commands
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Seed test users (will only create if they don't exist)
python manage.py seed_users
