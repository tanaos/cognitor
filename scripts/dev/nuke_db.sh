#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

LOCAL_STORAGE_DIR="${ROOT_DIR}/storage"
LOCAL_COLLECTIONS_DIR="${LOCAL_STORAGE_DIR}/collections"
DOCKER_VOLUME_NAME="cognitor_storage"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"

DO_LOCAL=true
DO_DOCKER=true
ASSUME_YES=false

print_help() {
    cat <<'EOF'
Usage: scripts/nuke_db.sh [OPTIONS]

Permanently remove Cognitor database data for developer workflows.

By default, this script attempts both:
1) Local reset: remove ./storage and recreate empty ./storage/collections
2) Docker reset: docker compose down -v and remove the cognitor_storage volume

Options:
  --local-only   Reset only local storage
  --docker-only  Reset only Docker volume data
  -y, --yes      Skip interactive confirmation
  -h, --help     Show this help message
EOF
}

log() {
    printf '[nuke-db] %s\n' "$1"
}

fail() {
    printf '[nuke-db] ERROR: %s\n' "$1" >&2
    exit 1
}

detect_compose_cmd() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        echo "docker compose"
        return
    fi
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
        return
    fi
    echo ""
}

for arg in "$@"; do
    case "$arg" in
        --local-only)
            DO_LOCAL=true
            DO_DOCKER=false
            ;;
        --docker-only)
            DO_LOCAL=false
            DO_DOCKER=true
            ;;
        -y|--yes)
            ASSUME_YES=true
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            fail "Unknown option: ${arg}. Use --help for usage."
            ;;
    esac
done

if [[ "${DO_LOCAL}" != true && "${DO_DOCKER}" != true ]]; then
    fail "Invalid option combination."
fi

if [[ "${ASSUME_YES}" != true ]]; then
    cat <<EOF
This will permanently remove Cognitor database data.

Selected actions:
  local reset:  ${DO_LOCAL}
  docker reset: ${DO_DOCKER}

Repository root: ${ROOT_DIR}
Local storage:   ${LOCAL_STORAGE_DIR}
Docker volume:   ${DOCKER_VOLUME_NAME}

Type NUKE to continue:
EOF
    read -r confirmation
    if [[ "${confirmation}" != "NUKE" ]]; then
        log "Aborted. Nothing was deleted."
        exit 0
    fi
fi

if [[ "${DO_LOCAL}" == true ]]; then
    if [[ -d "${LOCAL_STORAGE_DIR}" ]]; then
        rm -rf "${LOCAL_STORAGE_DIR}"
        log "Removed ${LOCAL_STORAGE_DIR}"
    else
        log "Local storage directory not found: ${LOCAL_STORAGE_DIR}"
    fi

    mkdir -p "${LOCAL_COLLECTIONS_DIR}"
    log "Recreated ${LOCAL_COLLECTIONS_DIR}"
fi

if [[ "${DO_DOCKER}" == true ]]; then
    if ! command -v docker >/dev/null 2>&1; then
        log "Docker not found; skipping Docker reset."
    else
        COMPOSE_CMD="$(detect_compose_cmd)"

        if [[ -n "${COMPOSE_CMD}" && -f "${COMPOSE_FILE}" ]]; then
            # shellcheck disable=SC2086
            ${COMPOSE_CMD} -f "${COMPOSE_FILE}" down --volumes --remove-orphans || true
            log "Ran compose down with --volumes"
        else
            log "Compose command or compose file not found; skipping compose down."
        fi

        if docker volume inspect "${DOCKER_VOLUME_NAME}" >/dev/null 2>&1; then
            docker volume rm -f "${DOCKER_VOLUME_NAME}" >/dev/null
            log "Removed Docker volume ${DOCKER_VOLUME_NAME}"
        else
            log "Docker volume not found: ${DOCKER_VOLUME_NAME}"
        fi
    fi
fi

log "Database reset completed."
