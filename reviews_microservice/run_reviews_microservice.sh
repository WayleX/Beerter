#!/bin/bash

# Default port if not specified
PORT=${1:-8011}
NETWORK_NAME="reviews_network"
MONGO_CONTAINER="mongodb"
BACKEND_CONTAINER="reviews_backend_${PORT}"



sudo docker build --build-arg PORT=$PORT -t reviews-backend:$PORT ./backend



echo "Starting reviews microservice:"
echo "- Backend port: $PORT"

# Start backend container
sudo docker run  \
  --name $BACKEND_CONTAINER \
  --network "beer_review_network"\
  -p $PORT:$PORT \
  -e PORT=$PORT \
  -e MONGO_URI=mongodb://admin:password@$MONGO_CONTAINER:27017/ \
  -e MONGO_DB=reviews_db \
  -v "$(pwd)/backend:/app" \
  reviews-backend:$PORT

echo "Backend container started: $BACKEND_CONTAINER"
echo "Service available at http://localhost:$PORT"