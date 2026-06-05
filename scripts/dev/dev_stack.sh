#!/usr/bin/env sh
set -eu

ACTION="${1:-up}"

if [ ! -d "../cognitor-worker" ]; then
  echo "Missing ../cognitor-worker directory."
  echo "Clone cognitor-worker next to cognitor, then retry."
  exit 1
fi

case "$ACTION" in
  up)
    docker compose \
      -f docker-compose.yml \
      -f docker-compose.worker-local.yml \
      --profile worker up -d --build
    ;;
  down)
    docker compose \
      -f docker-compose.yml \
      -f docker-compose.worker-local.yml \
      --profile worker down --remove-orphans
    ;;
  *)
    echo "Usage: sh scripts/dev/dev_stack.sh [up|down]"
    exit 1
    ;;
esac
