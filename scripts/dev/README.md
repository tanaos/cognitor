# Development Scripts

These scripts are intended for local development workflows. They should not be used in production environments, or by end users.

## `dev_stack.sh`

Start or stop Cognitor together with a locally built `cognitor-worker` from the sibling repository (`../cognitor-worker`).

Usage:

```bash
sh scripts/dev/dev_stack.sh up
sh scripts/dev/dev_stack.sh down
```

Notes:

- Requires `docker compose`.
- Requires `../cognitor-worker` to exist next to this repository.

## `nuke_db.sh`

Permanently deletes local Cognitor data for development reset workflows.

Usage:

```bash
./scripts/dev/nuke_db.sh
./scripts/dev/nuke_db.sh --local-only
./scripts/dev/nuke_db.sh --docker-only
./scripts/dev/nuke_db.sh --yes
./scripts/dev/nuke_db.sh --help
```

By default it resets both local storage (`./storage`) and Docker volume data (`cognitor_storage`).
