#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python second/manage.py collectstatic --noinput