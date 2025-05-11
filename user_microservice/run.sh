#!/bin/bash
# filepath: /home/sshyku/UCU/Systems/Project/scripts/run_user_service.sh

# Load environment variables if .env exists
if [ -f ../.env ]; then
  source ../.env
fi

# Default values
USER_SERVICE_PORT=${USER_SERVICE_PORT:-8001}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-users_db}
SECRET_KEY=${SECRET_KEY:-your_super_secret}
NETWORK_NAME=${NETWORK_NAME:-beer_review_network}
CONTAINER_NAME="beer_review_user_service_${USER_SERVICE_PORT}"

# Build the image
echo "Building user microservice image"
sudo docker build -t beer_review_user_service ../user_microservice

# Check if container exists
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Stopping and removing existing container"
  sudo docker stop "$CONTAINER_NAME"
  sudo docker rm "$CONTAINER_NAME"
fi

# Run the container
echo "Starting user microservice container"
sudo docker run  \
  --name "$CONTAINER_NAME" \
  --network "$NETWORK_NAME" \
  -e USER_SERVICE_PORT="$USER_SERVICE_PORT" \
  -e DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@beer_review_postgres:5432/${POSTGRES_DB}" \
  -e SECRET_KEY="$SECRET_KEY" \
  -p "$USER_SERVICE_PORT:$USER_SERVICE_PORT" \
  beer_review_user_service

echo "User microservice started on port $USER_SERVICE_PORT"