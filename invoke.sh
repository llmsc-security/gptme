#!/bin/bash
set -e

# Build the Docker image
docker build -t gptme-server:latest \
    --build-arg BUILD_DIR=. \
    .

# Run the container with port mapping 11130:8000
docker run -it --rm \
    -p 11130:8000 \
    -v "${PWD}:/workspace" \
    -e GPTME_DISABLE_AUTH=true \
    --name gptme-server \
    gptme-server:latest
