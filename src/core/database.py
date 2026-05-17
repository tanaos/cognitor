import json
import re
from pathlib import Path

from src.storage.collection import CollectionStorage
from src.storage.discovery import discover_collection_dim, discover_collections


class Database:
	"""
    Database-level API for managing named vector collections.
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

	def get_collection(self, name: str) -> CollectionStorage:
		"""
		Retrieve an existing collection by name.

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

	def list_collections(self) -> list[str]:
		"""
		List all discovered collection names.

		Returns:
			Sorted list of collection names.
		"""
		return discover_collections(str(self.root_path))