#!/bin/bash

NETWORK_NAME="reviews_network"

MONGO_CONTAINER="mongodb"

sudo docker stop $MONGO_CONTAINER || true
sudo docker rm $MONGO_CONTAINER || true

sudo docker network rm $NETWORK_NAME || true

echo "Cleanup complete!"