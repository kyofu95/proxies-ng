#!/bin/bash

# get amount of workers from env or use default value of 3
uvicorn_workers="${UVICORN_WORKERS:-3}"

if [[ "$DEBUG" == "true" ]]; then
    # Try to install debugger and run server with it
    pip install debugpy
    python3 -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips="*" --log-config uvicorn_logging.yml --log-level debug
else
    # Run the server
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips="*" --log-config uvicorn_logging.yml --log-level info --workers "$uvicorn_workers"
fi