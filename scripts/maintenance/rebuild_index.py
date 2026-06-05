#!/usr/bin/env python3
"""
Manually recovery tool that triggers a rebuild of the FAISS index for one or all collections 
from the persisted vector store. This is needed in two situations:

1. If `index.faiss` is missing or corrupted.
2. After a compaction, if index rebuild is not automatically triggered.

Usage:
    python scripts/rebuild_index.py                          # rebuild all collections
    python scripts/rebuild_index.py --collection my_coll     # rebuild a specific collection
    python scripts/rebuild_index.py --root /custom/path      # custom storage root
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.collection import CollectionStorage
from src.storage.discovery import discover_collections_info


def rebuild_collection(path: str, dim: int) -> None:
    print(f"  Rebuilding {path} ...", end=" ", flush=True)
    storage = CollectionStorage(path, dim)
    storage._rebuild_index()
    print(f"{storage.index.ntotal} vectors indexed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild FAISS indexes from vector stores.")
    parser.add_argument(
        "--root",
        default="storage/collections",
        help="Root collections directory (default: storage/collections)",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Name of a specific collection to rebuild (default: all)",
    )
    args = parser.parse_args()

    infos = discover_collections_info(args.root)
    if not infos:
        print("No collections found.")
        sys.exit(0)

    if args.collection:
        infos = [i for i in infos if i.name == args.collection]
        if not infos:
            print(f"Collection '{args.collection}' not found.")
            sys.exit(1)

    for info in infos:
        path = str(Path(args.root) / info.name)
        rebuild_collection(path, info.dim)

    print("Done.")


if __name__ == "__main__":
    main()
