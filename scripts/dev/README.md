# Development Scripts

These scripts are intended for local development workflows and should not be used in production environments.

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

## `seed_ecommerce.py`

Pre-populates the database with a sample e-commerce products collection so that users without their own data can still test the application.

Usage:

```bash
# Basic: targets the local instance on port 7530
python scripts/dev/seed_ecommerce.py

# Target a Docker or remote instance
python scripts/dev/seed_ecommerce.py --url http://localhost:7530

# Custom model or collection name
python scripts/dev/seed_ecommerce.py --model all-MiniLM-L6-v2 --collection demo_products

# Re-run after a reset (drops the collection first)
python scripts/dev/seed_ecommerce.py --force
```

Options:

| Flag | Default | Description |
|---|---|---|
| `--collection` | `ecommerce_products` | Name of the collection to create |
| `--model` | `BAAI/bge-m3` | Embedding model the collection should use |
| `--url` | `http://localhost:7530` | Base URL of the running Cognitor instance |
| `--api-key` | — | `X-API-Key` header value (required when `MULTI_TENANT` is enabled) |
| `--force` | — | Delete and recreate the collection if it already exists |

The script sends requests to the running Cognitor instance, which handles embedding server-side. The server must be up and its models must be loaded before running.
