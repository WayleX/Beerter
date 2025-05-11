#!/bin/bash
# filepath: /home/sshyku/UCU/Systems/Project/scripts/create_network.sh

NETWORK_NAME="beer_review_network"

# Check if network exists
if ! sudo docker network inspect "$NETWORK_NAME" &>/dev/null; then
  echo "Creating network $NETWORK_NAME"
  sudo docker network create "$NETWORK_NAME"
else
  echo "Network $NETWORK_NAME already exists"
fi