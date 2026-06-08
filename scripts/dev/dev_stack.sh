#!/usr/bin/env sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

ACTION="up"
WORKER_BRANCH=""
FORCE_BUILD=0

print_help() {
cat <<'EOF'
Usage: sh scripts/dev/dev_stack.sh [up|down] [--worker-branch <branch>]

Actions:
  up     Start the stack and build cognitor-worker locally
  down   Stop the stack

Options:
  --worker-branch <branch>  Fetch and checkout this branch in ../cognitor-worker before build
	--build                   Force image rebuild (equivalent to docker compose up --build)
	--no-build                Do not force rebuild (default)
  -h, --help                Show this help message
EOF
}

if [ "$#" -gt 0 ]; then
	case "$1" in
		up|down)
			ACTION="$1"
			shift
			;;
		-h|--help)
			print_help
			exit 0
			;;
		*)
			;;
	esac
fi

while [ "$#" -gt 0 ]; do
	case "$1" in
		--worker-branch)
			if [ "$#" -lt 2 ]; then
				echo "Missing value for --worker-branch"
				exit 1
			fi
			WORKER_BRANCH="$2"
			shift 2
			;;
		--build)
			FORCE_BUILD=1
			shift
			;;
		--no-build)
			FORCE_BUILD=0
			shift
			;;
		-h|--help)
			print_help
			exit 0
			;;
		*)
			echo "Unknown option: $1"
			print_help
			exit 1
			;;
	esac
done

if [ ! -d "../cognitor-worker" ]; then
	echo "Missing ../cognitor-worker directory."
	echo "Clone cognitor-worker next to cognitor, then retry."
	exit 1
fi

case "$ACTION" in
	up)
		if [ -n "$WORKER_BRANCH" ]; then
			if [ ! -d "../cognitor-worker/.git" ]; then
				echo "../cognitor-worker is not a git repository; cannot switch branch."
				exit 1
			fi

			(
				cd ../cognitor-worker
				git fetch --all --prune
				if git show-ref --verify --quiet "refs/heads/$WORKER_BRANCH"; then
					git checkout "$WORKER_BRANCH"
				else
					git checkout -b "$WORKER_BRANCH" "origin/$WORKER_BRANCH"
				fi
			)
		fi

		mkdir -p "$ROOT_DIR/.docker-cache/cognitor" "$ROOT_DIR/.docker-cache/cognitor-worker"
		export DOCKER_BUILDKIT=1
		export COMPOSE_DOCKER_CLI_BUILD=1

		BUILD_FLAG=""
		if [ "$FORCE_BUILD" -eq 1 ]; then
			BUILD_FLAG="--build"
		fi

		docker compose \
			-f docker-compose.yml \
			-f docker-compose.worker-local.yml \
			--profile worker up -d $BUILD_FLAG
		;;
	down)
		docker compose \
			-f docker-compose.yml \
			-f docker-compose.worker-local.yml \
			--profile worker down --remove-orphans
		;;
	*)
		print_help
		exit 1
		;;
esac
