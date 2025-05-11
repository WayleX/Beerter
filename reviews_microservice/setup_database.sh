#!/bin/bash

# Usage: setup_database.sh [NUM_NODES] [BASE_PORT]
NUM_NODES=${1:-3}
BASE_PORT=${2:-27017}
NETWORK_NAME="beer_review_network"
RS_NAME="rs0"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# create network if missing
sudo docker network create $NETWORK_NAME || true

# clean up existing replica containers
for i in $(seq 0 $((NUM_NODES-1))); do
  name="mongodb-$i"
  if sudo docker ps -a --format '{{.Names}}' | grep -q "^${name}$"; then
    echo "Removing existing $name"
    sudo docker rm -f $name
  fi
done

# start each mongod instance with replSet, NO authentication
for i in $(seq 0 $((NUM_NODES-1))); do
  port=$((BASE_PORT + i))
  name="mongodb-$i"
  echo "Starting $name on port $port"
  sudo docker run -d --name $name \
    --network $NETWORK_NAME \
    -p ${port}:27017 \
    mongo:latest --replSet $RS_NAME --bind_ip_all
done

# wait for each mongod to accept connections 
for i in $(seq 0 $((NUM_NODES-1))); do
  name="mongodb-$i"
  echo "Waiting for $name to be ready..."
  until sudo docker exec $name mongosh --quiet --eval "db.adminCommand({ping:1})" &>/dev/null; do
    echo "Waiting for $name..."
    sleep 2
  done
  echo "$name is ready!"
done

# build replica set config
members=""
for i in $(seq 0 $((NUM_NODES-1))); do
  members+="{ _id: $i, host: \"mongodb-$i:27017\" },"
done
members=${members%,}
config="{ _id: '$RS_NAME', members: [ $members ] }"

echo "Initiating replica set $RS_NAME"
sudo docker exec mongodb-0 mongosh --eval "rs.initiate($config)"

# wait for replication to initialize and primary to be elected
echo "Waiting for replica set to initialize and elect primary..."
PRIMARY_READY=false
MAX_WAIT=60
WAITED=0

while [ "$PRIMARY_READY" = false ] && [ $WAITED -lt $MAX_WAIT ]; do
  echo "Checking for primary node... (${WAITED}s of ${MAX_WAIT}s max)"
  if sudo docker exec mongodb-0 mongosh --quiet --eval 'rs.isMaster().ismaster' | grep -q true; then
    PRIMARY_READY=true
    echo "Primary node elected!"
  else
    sleep 5
    WAITED=$((WAITED+5))
  fi
done

if [ "$PRIMARY_READY" = true ]; then
  # Now initialize root user on the primary after replica set is established
  echo "Creating admin user..."
  sudo docker exec mongodb-0 mongosh --eval "
    db = db.getSiblingDB('admin');
    db.createUser({
      user: 'admin',
      pwd: 'password',
      roles: [ { role: 'root', db: 'admin' } ]
    });
  "
  echo "Admin user created."
else
  echo "Warning: Timed out waiting for primary. No admin user created."
fi

echo "Replica set initiated with $NUM_NODES members; if NUM_NODES < majority, cluster will remain without primary (read-only)"
echo "Connect using: mongodb://admin:password@localhost:${BASE_PORT}/?replicaSet=${RS_NAME}"