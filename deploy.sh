#!/bin/bash

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate economato

# Start the application
docker-compose down
docker-compose up --build -d

# Show logs
docker-compose logs -f 