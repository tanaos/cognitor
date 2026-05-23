#!/usr/bin/env python3
"""
Manual compaction script.

Run while the server is offline to physically remove soft-deleted vectors,
reclaim disk space, and rebuild the FAISS index.

Usage:
    # Compact a single collection
    python scripts/compact.py my-collection

    # Compact all collections
    python scripts/compact.py --all
"""

import argparse
import sys
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.defaults import SQLLITE_DB_PATH
from src.storage.collection import CollectionStorage
from src.storage.compaction import compact
from src.storage.discovery import discover_collections, discover_collection_dim

COLLECTIONS_ROOT = "storage/collections"


def compact_collection(name: str) -> None:
    dim = discover_collection_dim(COLLECTIONS_ROOT, name)
    if dim is None:
        print(f"  error: '{name}' is not a valid collection", file=sys.stderr)
        sys.exit(1)

    storage = CollectionStorage(str(Path(COLLECTIONS_ROOT) / name), dim)
    result = compact(name, storage)

    if result.deleted_count == 0:
        print(f"  {name}: nothing to compact ({result.live_count} live vectors)")
    else:
        reclaimed = result.vectors_before - result.live_count
        print(
            f"  {name}: {result.vectors_before} → {result.live_count} vectors "
            f"({reclaimed} removed)"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compact one or all cognitor collections.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("collection", nargs="?", help="Name of the collection to compact")
    group.add_argument("--all", action="store_true", help="Compact all collections")
    args = parser.parse_args()

    if args.all:
        names = discover_collections(COLLECTIONS_ROOT)
        if not names:
            print("No collections found.")
            return
        print(f"Compacting {len(names)} collection(s)...")
        for name in names:
            compact_collection(name)
    else:
        print(f"Compacting '{args.collection}'...")
        compact_collection(args.collection)

    print("Done.")


if __name__ == "__main__":
    main()
