import json
import sqlite3
from typing import Optional
from pathlib import Path

from src.config.defaults import SQLLITE_DB_PATH
from src.core.models import CollectionInfo


def discover_collections(root_path: str) -> list[str]:
    """
    Discover valid collection names under the root path.

    A collection is considered valid when:
    - it is a directory
    - it contains a `collection.json` manifest with a positive integer `dim`
    
    Args:
        root_path: Root directory to search for collections.
        
    Returns:
        Sorted list of valid collection names.
    """
    root = Path(root_path)
    if not root.exists():
        return []

    collections: list[str] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue

        dim = _read_collection_dim_from_manifest(child / "collection.json")
        if dim is not None:
            collections.append(child.name)

    collections.sort()
    return collections


def discover_collections_info(root_path: str) -> list[CollectionInfo]:
    """
    Discover valid collections, their dimensions, and document counts under the root path.

    Args:
        root_path: Root directory to search for collections.

    Returns:
        Sorted list of CollectionInfo objects for valid collections.
    """
    root = Path(root_path)
    if not root.exists():
        return []

    results: list[CollectionInfo] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue

        dim = _read_collection_dim_from_manifest(child / "collection.json")
        if dim is not None:
            results.append(
                CollectionInfo(
                    name=child.name, dim=dim, doc_count=_count_collection_documents(child)
                )
            )

    results.sort(key=lambda x: x.name)
    return results


def discover_collection_info(root_path: str, name: str) -> Optional[CollectionInfo]:
    """
    Return CollectionInfo for a single collection, or None if unavailable.

    Args:
        root_path: Root directory where collections are stored.
        name: Collection name.

    Returns:
        CollectionInfo object if the collection is valid, otherwise None.
    """
    collection_path = Path(root_path) / name
    dim = _read_collection_dim_from_manifest(collection_path / "collection.json")
    if dim is None:
        return None
    return CollectionInfo(
        name=name, dim=dim, doc_count=_count_collection_documents(collection_path)
    )


def discover_collection_dim(root_path: str, name: str) -> Optional[int]:
    """
    Return a collection dim from its manifest, or None if unavailable/invalid.
    
    Args:
        root_path: Root directory where collections are stored.
        name: Collection name.
        
    Returns:
        The collection's vector dimensionality (dim) if valid, otherwise None.
    """
    manifest_path = Path(root_path) / name / "collection.json"
    return _read_collection_dim_from_manifest(manifest_path)


def _read_collection_dim_from_manifest(manifest_path: Path) -> Optional[int]:
    """
    Read the collection manifest and extract the dim value if valid.
    
    Args:
        manifest_path: Path to the collection's manifest file.

    Returns:
        The collection's vector dimensionality (dim) if valid, otherwise None.
    """
    if not manifest_path.exists():
        return None

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        return None

    dim = data.get("dim")
    if isinstance(dim, int) and dim > 0:
        return dim

    return None


def _count_collection_documents(collection_path: Path) -> int:
    """
    Return the number of stored documents for a collection.

    Args:
        collection_path: Path to the collection directory.

    Returns:
        Number of rows in the collection metadata store, or 0 if unavailable.
    """
    db_path = collection_path / SQLLITE_DB_PATH
    if not db_path.exists():
        return 0

    try:
        with sqlite3.connect(db_path) as connection:
            row = connection.execute("SELECT COUNT(*) FROM documents").fetchone()
            return int(row[0]) if row is not None else 0
    except sqlite3.Error:
        return 0
