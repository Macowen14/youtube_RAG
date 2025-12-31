#!/bin/bash

# Start the application using Gunicorn with Uvicorn workers
# -w 4: Use 4 workers (adjust based on CPU cores, usually 2-4 x cores)
# -k uvicorn.workers.UvicornWorker: Use Uvicorn worker class
# --bind 0.0.0.0:8000: Bind to all interfaces on port 8000

echo "Starting YouTube RAG Backend with Gunicorn..."
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
