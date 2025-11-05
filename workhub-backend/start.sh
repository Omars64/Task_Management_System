#!/bin/bash
set -e

echo "Waiting for database to be ready..."

# Wait for database using nc or sleep
max_attempts=40
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if command -v nc >/dev/null 2>&1; then
        if nc -z database 1433 >/dev/null 2>&1; then
            echo "Database is ready!"
            break
        fi
    fi
    echo "Waiting for database... (attempt $((attempt+1))/$max_attempts)"
    attempt=$((attempt+1))
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo "Database not ready after $max_attempts attempts. Starting anyway..."
fi

# Run database initialization and migrations (idempotent)
echo "Running database initialization and schema migrations..."
python init_db.py || echo "Init DB failed but continuing..."

# Start the Flask application
echo "Starting Flask application..."
exec python app.py
