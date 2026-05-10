#!/bin/bash

# 'set -e' exits on error, '-u' errors on undefined variables, 
# '-o pipefail' ensures errors in piped commands are caught.
set -euo pipefail

# Ensures the script executes relative to its own location,
# allowing you to run it from any folder without path errors.
cd "$(dirname "$0")"

# Logic to determine which Python executable to use.
if [ -n "${PYTHON_BIN:-}" ]; then
    # Do nothing if PYTHON_BIN is already set by the user.
    :
elif [ -x ".venv/bin/python" ]; then
    # Use the virtual environment if it exists.
    PYTHON_BIN=".venv/bin/python"
else
    # Fallback to the system's default python command.
    PYTHON_BIN="python"
fi

# Run database migrations before starting the server.
echo "Running database migrations..."
"$PYTHON_BIN" -m alembic upgrade head
echo "Migrations complete."

# Execute main.py with all passed arguments
exec "$PYTHON_BIN" main.py "$@"