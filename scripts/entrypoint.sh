#!/bin/bash
# Positive_test/scripts/entrypoint.sh

set -e

echo "Waiting for services to be ready..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until python -c "import asyncpg; import asyncio; asyncio.get_event_loop().run_until_complete(asyncpg.connect('postgresql://${POSTGRES_USER:-positive_user}:${POSTGRES_PASSWORD:-positive_pass}@${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-positive_db}'))" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL is ready!"

# Initialize MinIO bucket
echo "Initializing MinIO bucket..."
python /app/scripts/init_minio.py || echo "Warning: MinIO initialization failed, continuing anyway"

# Run Alembic migrations
echo "Running database migrations..."
cd /app && alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"