#!/bin/bash

# Use the project virtual environment directly if it exists.
PYTHON_BIN="python"
if [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
fi

# Set default port to 8080 if PORT variable is not set by Sevalla
PORT=${PORT:-8080}

echo "Starting YouTube RAG Backend on port $PORT..."

# CHANGES MADE:
# 1. Used 0.0.0.0:$PORT to bind to the dynamic port Sevalla assigns.
# 2. Reduced workers (-w) to 1. 
#    WHY: RAG apps are memory heavy. 4 workers = 4x memory usage = Crash.
#    Increase this only if your server has massive RAM.
# 3. Added --timeout 120. 
#    WHY: RAG models take time to load. The default timeout (30s) is often too short.

exec "$PYTHON_BIN" -m gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT --timeout 120
