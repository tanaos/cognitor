class CognitorError(Exception):
    """
    Base exception for all domain errors.
    """


# --- Collection errors ---

class CollectionNotFoundError(CognitorError):
    """
    Raised when a collection does not exist.
    """
    def __init__(self, name: str) -> None:
        super().__init__(f"Collection '{name}' does not exist")
        self.name = name


class CollectionAlreadyExistsError(CognitorError):
    """
    Raised when creating a collection that already exists.
    """
    def __init__(self, name: str) -> None:
        super().__init__(f"Collection '{name}' already exists")
        self.name = name


class InvalidCollectionNameError(CognitorError):
    """
    Raised when a collection name fails validation.
    """


class InvalidDimensionError(CognitorError):
    """
    Raised when a dimension value is invalid or mismatched.
    """


# --- Document errors ---

class DocumentNotFoundError(CognitorError):
    """
    Raised when a document ID does not exist in the collection.
    """
    def __init__(self, doc_id: str) -> None:
        super().__init__(f"Document with id {doc_id} does not exist")
        self.doc_id = doc_id


class DimensionMismatchError(CognitorError):
    """
    Raised when a vector's dimensionality does not match the collection's.
    """


class InvalidDocumentInputError(CognitorError):
    """
    Raised when add_documents receives mismatched or malformed inputs.
    """
