from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):

    # When True, enables remote authentication and per-user collection isolation.
    multi_tenant: bool = False
    remote_auth_url: str = ""
    remote_auth_http_method: Literal["GET", "POST"] = "GET"
    remote_auth_timeout_seconds: float = Field(default=5.0, gt=0.0)
    remote_auth_cache_ttl_seconds: int = Field(default=300, ge=0)

    # Percentage of deleted documents in a collection that triggers compaction
    compaction_threshold: float = 0.20

    emb_models: list[str] = ["BAAI/bge-m3"]
    fallback_emb_model: str = "BAAI/bge-m3"
    qa_model: str = "deepset/xlm-roberta-base-squad2"
    qa_min_score: float = Field(default=0.05, ge=0.0, le=1.0)
    rerank_model: str = "BAAI/bge-reranker-v2-m3"

    telemetry_enabled: bool = True
    telemetry_endpoint: str = "https://compute.tanaos.com/cognitor-telemetry/event"
    telemetry_api_key: str = "tk_ahS84hAzm7lU38lA84jGd7Bsl47Nm472"
    telemetry_instance_id: str = ""  # Auto-generated and persisted if left empty

    @model_validator(mode="after")
    def validate_remote_auth(self) -> "Config":
        if self.multi_tenant and not self.remote_auth_url:
            raise ValueError("remote_auth_url must be set when multi_tenant is enabled")
        return self

    @property
    def default_emb_model(self) -> str:
        return self.emb_models[0] if self.emb_models else self.fallback_emb_model

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="allow",
    )
    
@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()