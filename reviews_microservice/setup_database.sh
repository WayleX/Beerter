
MONGO_PORT=${2:-27017}

NETWORK_NAME="beer_review_network"
MONGO_CONTAINER="mongodb"


sudo docker network create $NETWORK_NAME || true

echo "- MongoDB port: $MONGO_PORT"
sudo docker run -d \
  --name $MONGO_CONTAINER \
  --network $NETWORK_NAME \
  -p $MONGO_PORT:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -v mongo_data:/data/db \
  mongo:latest

echo "MongoDB container started: $MONGO_CONTAINER"