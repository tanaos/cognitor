#!/bin/bash
set -e

IMAGE=cognitor:$(date +%Y-%m-%d-%H-%M)
PORT=7530

# Clean up dangling images and stopped containers to free up space
docker image prune -f
docker container prune -f

docker build -t $IMAGE .

# Stop and remove the existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q '^cognitor$'; then
    docker stop cognitor
    docker rm cognitor
    echo "Stopped and removed existing 'cognitor' container."
fi

docker run -d \
  --env-file ./.env \
  -v cognitor_storage:/app/storage \
  --name cognitor \
  -p $PORT:$PORT \
  --restart unless-stopped \
  $IMAGE

echo "✅ Cognitor development container is running on port $PORT. Visit the API docs at http://localhost:$PORT/docs"