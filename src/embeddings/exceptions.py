class EmbeddingError(Exception):
    """Base exception for embedding errors."""


class EmbedderNotFoundError(EmbeddingError):
    """Raised when no embedder is registered for a given model ID."""

    def __init__(self, model_id: str) -> None:
        super().__init__(f"No embedder registered for model '{model_id}'")
        self.model_id = model_id
