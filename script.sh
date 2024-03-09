#!/usr/bin/env bash
docker compose up -d redis
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS="./google-application-credentials.json"
python app.py
