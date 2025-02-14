#!/bin/bash

# Update system and install dependencies
sudo apt-get update
sudo apt-get install -y docker.io docker-compose awscli

# Configure AWS (if using ECR)
aws configure set default.region eu-west-1  # your region
aws configure set default.output json

# Create data directory
sudo mkdir -p /app/data
sudo chown -R ubuntu:ubuntu /app

# Copy your local image or pull from registry
docker-compose pull  # if image is in registry
# OR
docker load < my_app.tar  # if using local image

# Start the application
docker-compose up -d 