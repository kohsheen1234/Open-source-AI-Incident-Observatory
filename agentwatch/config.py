from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENTWATCH_", env_file=".env")

    database_url: str = "sqlite+pysqlite:///./agentwatch.sqlite3"
    artifact_dir: str = "./artifacts"
    author_hash_salt: str = "change-me-in-production"
    log_level: str = "INFO"
    environment: str = "local"
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    api_key: str | None = None
    # Set when the API is served behind a reverse proxy under a sub-path (e.g. "/api"),
    # so the OpenAPI docs load the spec from the correct URL. Empty when served at root.
    api_root_path: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
