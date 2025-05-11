#!/bin/bash

# This script brings up RabbitMQ (with management UI) in Docker
# Usage: ./rabbitmq_setup.sh

NETWORK_NAME=${NETWORK_NAME:-beer_review_network}
RABBITMQ_CONTAINER=${RABBITMQ_CONTAINER:-rabbitmq}

# Create network if not exists
if ! sudo docker network ls --format '{{.Name}}' | grep -q "^${NETWORK_NAME}$"; then
  echo "Creating Docker network ${NETWORK_NAME}"
  sudo docker network create ${NETWORK_NAME}
fi

# Start RabbitMQ broker
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${RABBITMQ_CONTAINER}$"; then
  echo "Removing existing container ${RABBITMQ_CONTAINER}"
  sudo docker rm -f ${RABBITMQ_CONTAINER}
fi

echo "Starting RabbitMQ broker on network ${NETWORK_NAME}"
sudo docker run -d \
  --name ${RABBITMQ_CONTAINER} \
  --network ${NETWORK_NAME} \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management

echo "RabbitMQ setup complete. AMQP port 5672, management UI on port 15672."