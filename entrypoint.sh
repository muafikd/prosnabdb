#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Function to check database connection
wait_for_db() {
    echo "Waiting for postgres..."
    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
}

# Wait for DB if host is set
if [ "$DATABASE_HOST" ]
then
    # Use a simple python script to check connection since 'nc' might not be available or reliable for host.docker.internal depending on image
    echo "Waiting for database Connection..."
    python << END
import sys
import time
import psycopg2
import os

start_time = time.time()
while time.time() - start_time < 30:
    try:
        psycopg2.connect(
            dbname=os.environ.get('DATABASE_NAME'),
            user=os.environ.get('DATABASE_USER'),
            password=os.environ.get('DATABASE_PASSWORD'),
            host=os.environ.get('DATABASE_HOST'),
            port=os.environ.get('DATABASE_PORT')
        )
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f"Connection failed: {e}")
        time.sleep(1)
sys.exit(1)
END
fi

echo "Database available"

# Skip migrations and collectstatic if SKIP_MIGRATIONS is set (for worker containers)
if [ -z "$SKIP_MIGRATIONS" ]; then
    # Apply database migrations
    echo "Applying database migrations..."
    python manage.py migrate

    # Collect static files
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "Skipping migrations and collectstatic (SKIP_MIGRATIONS is set)"
fi

# Start command
echo "Starting command: $@"
exec "$@"
