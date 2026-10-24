from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = ''
    openrouter_api_key: str = ''
    openrouter_model: str = ''
    staff_username: str = ''
    staff_password: str = ''
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    retrieval_threshold: float = 0.35
    cors_origins: list[str] = ['http://127.0.0.1:5173', 'http://localhost:5173']
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / '.env', extra='ignore')

@lru_cache
def settings():
    return Settings()
