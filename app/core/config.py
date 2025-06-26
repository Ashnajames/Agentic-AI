from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ITSM RAG AI Agent"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Advanced RAG-powered ITSM knowledge assistant"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

 
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  

    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: Optional[str] = None
    WEAVIATE_CLASS_NAME: str = "ITSMDocument"

    HF_MODEL_NAME: str = "google/gemma-2-2b-it"
    HF_CACHE_DIR: str = "./models"
    HF_TOKEN: Optional[str] = None
    DEVICE: str = "cpu"  


    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384


    TARGET_URL: str = "https://zenduty.com/blog/top-itsm-tools/"
    SCRAPING_TIMEOUT: int = 30
    SCRAPING_DELAY: float = 1.0
    MAX_RETRIES: int = 3


    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_QUERY: int = 5

    DATA_REFRESH_HOURS: int = 24
    AUTO_REFRESH: bool = True


    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    @field_validator("WEAVIATE_URL")
    def validate_weaviate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("WEAVIATE_URL must start with http:// or https://")
        return v

    @field_validator("DEVICE")
    def validate_device(cls, v):
        if v not in ["cpu", "cuda", "mps"]:
            raise ValueError("DEVICE must be one of: cpu, cuda, mps")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


Path(settings.HF_CACHE_DIR).mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
