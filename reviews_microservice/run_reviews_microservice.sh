#!/bin/bash

# Default port if not specified
PORT=${1:-8011}
NETWORK_NAME="beer_review_network"
MONGO_REPLICA_SET="rs0"  # Match the RS_NAME from setup_database.sh
BACKEND_CONTAINER="reviews_backend_${PORT}"

sudo docker build --build-arg PORT=$PORT -t reviews-backend:$PORT ./backend

echo "Starting reviews microservice:"
echo "- Backend port: $PORT"

# Start backend container with replica set connection string
sudo docker run \
  --name $BACKEND_CONTAINER \
  --network "$NETWORK_NAME" \
  -p $PORT:$PORT \
  -e PORT=$PORT \
  -e MONGO_URI="mongodb://admin:password@mongodb-0:27017,mongodb-1:27017,mongodb-2:27017/?replicaSet=$MONGO_REPLICA_SET" \
  -e MONGO_DB=reviews_db \
  -v "$(pwd)/backend:/app" \
  reviews-backend:$PORT

echo "Backend container started: $BACKEND_CONTAINER"
echo "Service available at http://localhost:$PORT"