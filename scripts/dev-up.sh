#!/bin/bash
set -e

IMAGE=cognitor:$(date +%Y-%m-%d-%H-%M)
PORT=7530

mkdir -p ./logs

LOG_FILE="./logs/cognitor.log"

docker image prune -f
docker container prune -f

docker build -t $IMAGE .

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q '^cognitor$'; then
    docker stop cognitor
    docker rm cognitor
    echo "Stopped and removed existing 'cognitor' container."
fi

# Start the container with source code mounted for live reloading
docker run -d \
  --env-file ./.env \
  -v $(pwd)/src:/app/src \
  -v cognitor_storage:/app/storage \
  --name cognitor \
  -p $PORT:$PORT \
  --restart unless-stopped \
  $IMAGE \
  uvicorn src.server.app:app --host 0.0.0.0 --port $PORT --reload

echo "Container started. Tailing logs into $LOG_FILE..."

nohup docker logs -f cognitor >> "$LOG_FILE" 2>&1 &

echo ""
echo "🚀 Cognitor development container is running on port $PORT." 
echo "- Visit docs at http://localhost:$PORT/docs"
echo "- Logs are being written to $LOG_FILE"