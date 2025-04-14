#!/bin/bash

# Run the migrations
alembic upgrade head

python3 -m app.init_data

if [[ "$DEBUG" == "true" ]]; then
    # Try to install debugger and run server with it
    pip install debugpy
    python3 -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
else
    # Run the server
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
fi