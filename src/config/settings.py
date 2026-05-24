from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):

    auth_enabled: bool = False

    # Percentage of deleted documents in a collection that triggers compaction
    compaction_threshold: float = 0.20
    
    emb_models: list[str] = ["all-MiniLM-L6-v2"]
    @property
    def default_emb_model(self) -> str:
        return self.emb_models[0] if self.emb_models else "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="allow",
    )
    
@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()