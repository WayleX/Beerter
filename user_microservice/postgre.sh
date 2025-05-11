#!/bin/bash
# filepath: /home/sshyku/UCU/Systems/Project/scripts/run_postgres.sh

# Load environment variables if .env exists
if [ -f ../.env ]; then
  source ../.env
fi

# Default values
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-users_db}
DB_PORT=${DB_PORT:-5433}
NETWORK_NAME=${NETWORK_NAME:-beer_review_network}
CONTAINER_NAME="beer_review_postgres"

# Check if container exists
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Container $CONTAINER_NAME already exists"
  
  # Check if it's running
  if sudo docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container is already running"
  else
    echo "Starting existing container"
    sudo docker start "$CONTAINER_NAME"
  fi
else
  echo "Creating and starting PostgreSQL container"
  sudo docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -p "$DB_PORT:5432" \
    -v "${CONTAINER_NAME}_data:/var/lib/postgresql/data" \
    postgres:14
fi

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until sudo docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER"; do
  echo "Waiting for PostgreSQL..."
  sleep 10
done

echo "PostgreSQL is ready"