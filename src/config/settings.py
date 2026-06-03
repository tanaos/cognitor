from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):

    # When True, enables remote authentication and per-user collection isolation.
    MULTI_TENANT: bool = False
    REMOTE_AUTH_URL: str = ""
    REMOTE_AUTH_HTTP_METHOD: Literal["GET", "POST"] = "GET"
    REMOTE_AUTH_TIMEOUT_SECONDS: float = Field(default=5.0, gt=0.0)
    REMOTE_AUTH_CACHE_TTL_SECONDS: int = Field(default=300, ge=0)

    # Percentage of deleted documents in a collection that triggers compaction
    COMPACTION_THRESHOLD: float = 0.20

    EMB_MODELS: list[str] = ["BAAI/bge-m3"]
    FALLBACK_EMB_MODEL: str = "BAAI/bge-m3"
    QA_MODEL: str = "deepset/xlm-roberta-base-squad2"
    QA_MIN_SCORE: float = Field(default=0.05, ge=0.0, le=1.0)
    RERANK_MODEL: str = "BAAI/bge-reranker-v2-m3"

    TELEMETRY_ENABLED: bool = True
    TELEMETRY_ENDPOINT: str = "https://compute.tanaos.com/cognitor-telemetry/event"
    TELEMETRY_API_KEY: str = "tk_ahS84hAzm7lU38lA84jGd7Bsl47Nm472"
    TELEMETRY_INSTANCE_ID: str = ""  # Auto-generated and persisted if left empty

    @model_validator(mode="after")
    def validate_remote_auth(self) -> "Config":
        if self.MULTI_TENANT and not self.REMOTE_AUTH_URL:
            raise ValueError("REMOTE_AUTH_URL must be set when MULTI_TENANT is enabled")
        return self

    @property
    def DEFAULT_EMB_MODEL(self) -> str:
        return self.EMB_MODELS[0] if self.EMB_MODELS else self.FALLBACK_EMB_MODEL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="allow",
    )
    
@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()