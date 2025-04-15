#!/bin/bash

# Change to parent directory first
cd "$(dirname "$0")/.." || exit

# Debug: Print current directory
echo "Current directory: $(pwd)"

# Debug: Check if .env exists
if [ -f .env ]; then
    echo ".env file found"
    echo "Contents of .env:"
    cat .env
else
    echo "ERROR: .env file not found in $(pwd)"
    exit 1
fi

# Source with absolute path
source "$(pwd)/.env"

# Debug: Print some environment variables to verify they're loaded
echo "Checking environment variables:"
echo "DB_USER: $DB_USER"
echo "DB_HOST: $DB_HOST"
echo "PROJECT_NAME: $PROJECT_NAME"

docker_network="tothetop_network"

if docker network ls --filter name=$docker_network --format '{{.Name}}' | grep -w $docker_network > /dev/null; then
    echo "Network '$docker_network' exists"
else
    echo "Creating docker network '$docker_network'"
    docker network create $docker_network
fi

# Use --env-file flag explicitly
docker compose --env-file "$(pwd)/.env" -f docker/docker-compose.yml up --build -d

# Run migrations automatically
echo "Running database migrations..."
./migrate.sh