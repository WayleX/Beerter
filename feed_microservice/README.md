# Feed Microservice

This microservice is responsible for generating and managing user feeds of beer reviews in the Beer Review System. It combines data from the Reviews and User microservices to create personalized feeds that show relevant beer reviews along with the user's interaction status (liked/not liked).

## Features

- **Feed Generation**: Aggregates beer reviews and enhances them with user-specific information
- **Redis Caching**: Stores user feeds in Redis for quick access
- **Service Discovery**: Uses Consul for dynamic service discovery
- **Docker Integration**: Runs in Docker containers for easy deployment and scaling

## Architecture

- **Feed API**: FastAPI application that provides endpoints for refreshing and retrieving feeds
- **Redis**: In-memory data store for caching user feeds
- **Service Discovery**: Consul client for discovering other services

## Setup and Running

### Prerequisites

- Docker
- Docker network (default: `beer_review_network`)
- Consul service running

### Running the Service

Use the management script to start, stop, restart, or check the status of the service:

```bash
# Start the feed service with 1 instance (default)
./manage.sh start

# Start with multiple instances
./manage.sh start 3

# Stop all feed service containers and Redis
./manage.sh stop

# Restart the service
./manage.sh restart

# Check service status
./manage.sh status
```

Alternatively, you can use the original `start.sh` script:

```bash
# Start with 1 instance (default)
./start.sh

# Start with multiple instances
./start.sh 3
```

### Cleanup

To clean up all feed service resources:

```bash
./cleanup.sh
```

This will:
1. Deregister services from Consul
2. Stop and remove all feed service containers
3. Stop and remove the Redis container
4. Optionally clean up unused Docker images and volumes

## API Endpoints

- `GET /health`: Health check endpoint for Consul
- `POST /refresh_feed`: Refreshes the user's feed by fetching fresh data
- `GET /feed`: Gets the user's cached feed

## Environment Variables

- `REDIS_HOST`: Redis host (default: `feed-redis`)
- `REDIS_PORT`: Redis port (default: `6379`)
- `PORT`: API service port (default: `8000`)
- `SERVICE_NAME`: Service name for registration with Consul
- `NETWORK_NAME`: Docker network name (default: `beer_review_network`)
- `CONSUL_ADDRESS`: Consul address (default: `consul:8500`)
