#!/bin/bash
# filepath: /home/sshyku/UCU/Systems/Project/scripts/run_facade_service.sh

# Load environment variables if .env exists
if [ -f ../.env ]; then
  source ../.env
fi

# Default values
FACADE_PORT=${FACADE_PORT:-8009}
USER_SERVICE_PORT=${USER_SERVICE_PORT:-8001}
NETWORK_NAME=${NETWORK_NAME:-beer_review_network}
CONTAINER_NAME="beer_review_facade_service"

# Build the image
echo "Building facade service image"
sudo docker build -t beer_review_facade_service ../facade_microservice

# Check if container exists
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Stopping and removing existing container"
  sudo docker stop "$CONTAINER_NAME"
  sudo docker rm "$CONTAINER_NAME"
fi

# Run the container
echo "Starting facade service container"
sudo docker run  \
  --name "$CONTAINER_NAME" \
  --network "$NETWORK_NAME" \
  -e USER_SERVICE_URL="http://beer_review_user_service:8001" \
  -p "8009:8009" \
  beer_review_facade_service

echo "Facade service started on port $FACADE_PORT"