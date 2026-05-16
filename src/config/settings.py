from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="allow",
    )
    
@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()