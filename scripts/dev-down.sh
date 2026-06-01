#!/bin/bash
set -e

CONTAINER_NAME=cognitor
LOG_FILE="./logs/cognitor.log"

echo "Stopping Cognitor dev container..."

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker stop "$CONTAINER_NAME"
    echo "Stopped running container: $CONTAINER_NAME"
else
    echo "No running container found: $CONTAINER_NAME"
fi

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker rm "$CONTAINER_NAME"
    echo "Removed container: $CONTAINER_NAME"
else
    echo "No container to remove: $CONTAINER_NAME"
fi

# Kill background log tail if it exists
if pgrep -f "docker logs -f ${CONTAINER_NAME}" > /dev/null; then
    pkill -f "docker logs -f ${CONTAINER_NAME}" || true
    echo "Stopped log tail process."
fi

echo ""
echo "✅ Dev environment shut down cleanly."
echo "Logs preserved at: $LOG_FILE"