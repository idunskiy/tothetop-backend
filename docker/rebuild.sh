#!/bin/bash

# Check if service name is provided
if [ -z "$1" ]; then
    echo "Usage: ./rebuild.sh <service_name>"
    echo "Available services: frontend, backend, nginx, rabbitmq"
    exit 1
fi

SERVICE_NAME=$1

echo "🛑 Stopping $SERVICE_NAME service..."
docker compose -p tothetop stop $SERVICE_NAME

echo "🗑️ Removing $SERVICE_NAME container..."
docker compose -p tothetop rm -f $SERVICE_NAME

echo "⏳ Waiting 5 seconds before rebuilding..."
sleep 5

echo "🏗️ Rebuilding $SERVICE_NAME..."
docker compose -p tothetop up -d --build $SERVICE_NAME

echo "📝 Showing logs for $SERVICE_NAME..."
docker compose -p tothetop logs -f $SERVICE_NAME