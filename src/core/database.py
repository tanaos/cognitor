import json
import re
from pathlib import Path

from src.storage.collection import CollectionStorage
from src.storage.discovery import discover_collection_dim, discover_collection_info, discover_collections_with_dim
from src.core.collection import Collection


class Database:
	"""
    Database-level API for managing collection lifecycle, selection and discovery, as well as 
    collection folders and manifests.
    """

	_VALID_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

	def __init__(self, root_path: str = "storage/collections") -> None:
		"""
		Initialize the database manager.

		Args:
			root_path: Root directory containing all collections.
		"""
		self.root_path = Path(root_path)
		self.root_path.mkdir(parents=True, exist_ok=True)

	def _collection_path(self, name: str) -> Path:
		return self.root_path / name

	def _validate_collection_name(self, name: str) -> None:
		if not name:
			raise ValueError("Collection name cannot be empty")
		if not self._VALID_NAME_PATTERN.fullmatch(name):
			raise ValueError(
				"Collection name must contain only letters, numbers, underscores, or hyphens"
			)

	def create_collection(self, name: str, dim: int) -> CollectionStorage:
		"""
		Create a collection and return its storage handle.

		Args:
			name: Collection name.
			dim: Vector dimensionality for this collection.

		Returns:
			CollectionStorage bound to the created collection.
		"""
		self._validate_collection_name(name)
		if dim <= 0:
			raise ValueError("dim must be a positive integer")

		collection_path = self._collection_path(name)
		manifest_path = collection_path / "collection.json"

		if collection_path.exists():
			existing_dim = discover_collection_dim(str(self.root_path), name)
			if existing_dim is not None:
				if existing_dim != dim:
					raise ValueError(
						f"Collection '{name}' already exists with dim={existing_dim}, requested dim={dim}"
					)
				raise ValueError(f"Collection '{name}' already exists")
			raise ValueError(
				f"Collection directory '{name}' already exists but is missing a valid manifest"
			)

		collection_path.mkdir(parents=True, exist_ok=False)
		manifest_path.write_text(
			json.dumps({"name": name, "dim": dim}, indent=2),
			encoding="utf-8",
		)

		return CollectionStorage(str(collection_path), dim)

	def delete_collection(self, name: str) -> bool:
		"""
		Delete a collection by name.

		Args:
			name: Collection name.

		Returns:
			True if the collection was deleted, False if it did not exist.
		"""
		self._validate_collection_name(name)
		collection_path = self._collection_path(name)
		if not collection_path.exists():
			return False
		for item in collection_path.iterdir():
			item.unlink()
		collection_path.rmdir()
		return True

	def _get_collection(self, name: str) -> CollectionStorage:
		"""
		Retrieve a collection object by name.

		Args:
			name: Collection name.

		Returns:
			CollectionStorage bound to the requested collection.
		"""
		self._validate_collection_name(name)
		dim = discover_collection_dim(str(self.root_path), name)
		if dim is None:
			raise KeyError(f"Collection '{name}' does not exist")

		return CollectionStorage(str(self._collection_path(name)), dim)

	def get_collection_info(self, name: str) -> tuple[str, int, int]:
		"""
		Retrieve a collection's name, dimension, and document count by name.

		Args:
			name: Collection name.

		Returns:
			Tuple of (name, dim, doc_count).

		Raises:
			KeyError: If the collection does not exist.
		"""
		self._validate_collection_name(name)
		info = discover_collection_info(str(self.root_path), name)
		if info is None:
			raise KeyError(f"Collection '{name}' does not exist")
		return info

	def list_collections(self) -> list[tuple[str, int, int]]:
		"""
		List all discovered collections with their dimensions and document counts.

		Returns:
			Sorted list of (name, dim, doc_count) tuples.
		"""
		return discover_collections_with_dim(str(self.root_path))

	def get_collection_service(self, name: str) -> Collection:
		"""
		Get a Collection service instance for the specified collection name.

		Args:
			name: Collection name.

		Returns:
			Collection service instance bound to the requested collection.
		"""
		storage = self._get_collection(name)
		return Collection(storage)