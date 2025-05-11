#!/bin/bash

PORT=${1:-8011}

echo "Setting up reviews microservice:"
echo "- Backend port: $PORT"

sudo docker build --build-arg PORT=$PORT -t reviews-backend:$PORT ./backend

echo "Setup complete! Run the service with: ./start.sh $PORT "