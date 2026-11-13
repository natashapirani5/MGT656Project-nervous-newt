#!/usr/bin/env bash
# Render build step. Migrations + seed run in the pre-deploy step (render.yaml).
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
