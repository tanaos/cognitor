from dataclasses import dataclass


@dataclass
class InstanceStarted:
    version: str
    emb_model_count: int
    collection_count: int


@dataclass
class SearchPerformed:
    duration_ms: float
    top_k: int
    result_count: int
    used_filters: bool
    used_query_text: bool
    reranking_applied: bool
    extractive_qa_applied: bool


@dataclass
class DocumentsAdded:
    count: int
    used_embedding: bool
    duration_ms: float


@dataclass
class DocumentDeleted:
    pass


@dataclass
class CollectionCreated:
    dim: int
    has_emb_model: bool


@dataclass
class CollectionDeleted:
    pass


@dataclass
class CompactionRun:
    vectors_before: int
    live_count: int
    deleted_count: int
    duration_ms: float


TelemetryEvent = (
    InstanceStarted
    | SearchPerformed
    | DocumentsAdded
    | DocumentDeleted
    | CollectionCreated
    | CollectionDeleted
    | CompactionRun
)
