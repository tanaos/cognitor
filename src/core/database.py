import json
import re
from pathlib import Path

from src.storage.collection import CollectionStorage
from src.storage.discovery import discover_collection_dim, discover_collection_info, discover_collections_info
from src.core.collection import Collection
from src.core.models import CollectionInfo
from src.core.exceptions import (
	CollectionAlreadyExistsError,
	CollectionNotFoundError,
	CognitorError,
	InvalidCollectionNameError,
	InvalidDimensionError,
)


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
			raise InvalidCollectionNameError("Collection name cannot be empty")
		if not self._VALID_NAME_PATTERN.fullmatch(name):
			raise InvalidCollectionNameError(
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
			raise InvalidDimensionError("dim must be a positive integer")

		collection_path = self._collection_path(name)
		manifest_path = collection_path / "collection.json"

		if collection_path.exists():
			existing_dim = discover_collection_dim(str(self.root_path), name)
			if existing_dim is not None:
				if existing_dim != dim:
					raise InvalidDimensionError(
						f"Collection '{name}' already exists with dim={existing_dim}, requested dim={dim}"
					)
				raise CollectionAlreadyExistsError(name)
			raise CognitorError(
				f"Collection directory '{name}' already exists but is missing a valid manifest"
			)

		collection_path.mkdir(parents=True, exist_ok=False)
		manifest_path.write_text(
			json.dumps({"name": name, "dim": dim}, indent=2),
			encoding="utf-8",
		)

		return CollectionStorage(str(collection_path), dim)

	def delete_collection(self, name: str) -> None:
		"""
		Delete a collection by name.

		Args:
			name: Collection name.

		Raises:
			CollectionNotFoundError: If the collection does not exist.
		"""
		self._validate_collection_name(name)
		collection_path = self._collection_path(name)
		if not collection_path.exists():
			raise CollectionNotFoundError(name)
		for item in collection_path.iterdir():
			item.unlink()
		collection_path.rmdir()

	def get_collection_ref(self, name: str) -> CollectionStorage:
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
			raise CollectionNotFoundError(name)

		return CollectionStorage(str(self._collection_path(name)), dim)

	def get_collection_info(self, name: str) -> CollectionInfo:
		"""
		Retrieve a collection's information by name.

		Args:
			name: Collection name.

		Returns:
			CollectionInfo object containing information on the collection.
		"""
		self._validate_collection_name(name)
		info = discover_collection_info(str(self.root_path), name)
		if info is None:
			raise CollectionNotFoundError(name)
		return info

	def list_collections(self) -> list[CollectionInfo]:
		"""
		List all discovered collections with their dimensions and document counts.

		Returns:
			Sorted list of CollectionInfo objects.

		"""
		return discover_collections_info(str(self.root_path))

	def get_collection_service(self, name: str) -> Collection:
		"""
		Get a Collection service instance for the specified collection name.

		Args:
			name: Collection name.

		Returns:
			Collection service instance bound to the requested collection.
		"""
		storage = self.get_collection_ref(name)
		return Collection(storage)