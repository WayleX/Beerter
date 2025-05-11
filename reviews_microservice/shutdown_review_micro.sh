#!/bin/bash

# Default port if not specified
PORT=${1:-8011}
MONGO_CONTAINER="mongodb_${PORT}"
BACKEND_CONTAINER="reviews_backend_${PORT}"

echo "Stopping reviews microservice (port $PORT)..."

sudo docker stop $BACKEND_CONTAINER || true
sudo docker rm $BACKEND_CONTAINER || true
sudo docker stop $MONGO_CONTAINER || true
sudo docker rm $MONGO_CONTAINER || true

echo "Service stopped!"