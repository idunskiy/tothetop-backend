#!/bin/bash

# Change to parent directory first
cd "$(dirname "$0")/.." || exit

source .env

docker_network="tothetop_network"

if docker network ls --filter name=$docker_network --format '{{.Name}}' | grep -w $docker_network > /dev/null; then
    echo "Network '$docker_network' exists"
else
    echo "Creating docker network '$docker_network'"
    docker network create $docker_network
fi

# Build and start the service
docker compose -f docker/docker-compose.yml up --build -d

# Run migrations automatically
echo "Running database migrations..."
./migrate.sh