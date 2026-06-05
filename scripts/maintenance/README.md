# Maintenance Scripts

These scripts are operational tools for storage/index maintenance. Run them from the repository root with the project environment active.

## `compact.py`

Compacts one or all collections by physically removing soft-deleted vectors and rebuilding index state.

Usage:

```bash
python scripts/maintenance/compact.py my-collection
python scripts/maintenance/compact.py --all
```

## `rebuild_index.py`

Rebuilds FAISS indexes from persisted vectors.

Usage:

```bash
python scripts/maintenance/rebuild_index.py
python scripts/maintenance/rebuild_index.py --collection my-collection
python scripts/maintenance/rebuild_index.py --root storage/collections
```
