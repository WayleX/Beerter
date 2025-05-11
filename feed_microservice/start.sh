#!/bin/bash

# Load environment variables if .env exists
if [ -f ../.env ]; then
  source ../.env
fi

# Configuration
REDIS_CONTAINER="feed-redis"
REDIS_PORT=6379
NETWORK_NAME=${NETWORK_NAME:-beer_review_network}
APP_IMAGE="feed-service"
APP_CONTAINER_PREFIX="feed-service"


# Start Redis on the shared network
# Remove any existing Redis container to avoid port conflicts
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
    echo "Removing existing Redis container $REDIS_CONTAINER"
    sudo docker stop "$REDIS_CONTAINER" &>/dev/null || true
    sudo docker rm "$REDIS_CONTAINER" &>/dev/null || true
fi

# Start a fresh Redis container on the shared network (no host port mapping)
echo "Starting Redis container $REDIS_CONTAINER on network $NETWORK_NAME"
sudo docker run -d --name "$REDIS_CONTAINER" \
    --network "$NETWORK_NAME" \
    redis:alpine

sudo docker build -t "$APP_IMAGE" .
# Stop and remove any existing containers
echo "Cleaning up any existing service containers..."
for container in $(sudo docker ps -a --filter "name=$APP_CONTAINER_PREFIX-*" --format "{{.Names}}"); do
    echo "Stopping and removing $container..."
    sudo docker stop "$container" &>/dev/null
    sudo docker rm "$container" &>/dev/null
done

# Number of API instances to run
NUM_INSTANCES=${1:-2}
BASE_PORT=8020

echo "Starting $NUM_INSTANCES FastAPI instances in Docker..."

# Start each API instance on a different port
for ((i=0; i<$NUM_INSTANCES; i++))
do
    PORT=$((BASE_PORT + i))
    CONTAINER_NAME="$APP_CONTAINER_PREFIX-$i"
    echo "Starting Feed instance $i on port $PORT..."
    sudo docker run -d\
        --name "$CONTAINER_NAME" \
        --hostname "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        --network-alias "$CONTAINER_NAME" \
        -p $PORT:8000 \
        -e SERVICE_NAME="$CONTAINER_NAME" \
        -e REDIS_HOST="$REDIS_CONTAINER" \
        -e REDIS_PORT="$REDIS_PORT" \
        -e PORT="8000" \
        -e SERVICE_PORT="$PORT" \
        "$APP_IMAGE"
done

echo "All instances started."
echo "API instances are accessible at the following ports:"
for ((i=0; i<$NUM_INSTANCES; i++))
do
    PORT=$((BASE_PORT + i))
    echo " - http://localhost:$PORT"
done

echo "To connect additional services to Redis, use Docker network: $NETWORK_NAME"
echo "To stop all containers: docker stop $REDIS_CONTAINER \
    \$(docker ps -a --filter name=$APP_CONTAINER_PREFIX-* --format '{{.Names}}')"