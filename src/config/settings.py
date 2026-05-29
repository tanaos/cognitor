from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):

    auth_enabled: bool = False

    # Percentage of deleted documents in a collection that triggers compaction
    compaction_threshold: float = 0.20

    emb_models: list[str] = ["BAAI/bge-m3"]
    fallback_emb_model: str = "BAAI/bge-m3"
    qa_model: str = "deepset/xlm-roberta-base-squad2"
    qa_min_score: float = Field(default=0.05, ge=0.0, le=1.0)

    telemetry_enabled: bool = True
    telemetry_endpoint: str = "https://compute.tanaos.com/cognitor-telemetry/event"
    telemetry_api_key: str = "tk_ahS84hAzm7lU38lA84jGd7Bsl47Nm472"
    telemetry_instance_id: str = ""  # Auto-generated and persisted if left empty

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