import os
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[
            str(BASE_DIR / "backend" / ".env"),
            str(BASE_DIR / ".env")
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    PROJECT_NAME: str = "SQL Query Generator from Plain English"
    
    # LLM Settings
    LLM_PROVIDER: str = "groq" # "groq", "gemini", or "mock"
    GROQ_API_KEY: str = Field(default="", validation_alias="GROQ_API_KEY")
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Supabase Settings
    SUPABASE_URL: str = Field(default="", validation_alias="SUPABASE_URL")
    SUPABASE_KEY: str = Field(default="", validation_alias="SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="", validation_alias="SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_STORAGE_BUCKET: str = "private-datasets"

    # RAG (Retrieval-Augmented Generation) Settings - Lightweight Pure-Python BM25
    RAG_ENABLED: bool = True
    RAG_TOP_K: int = 3
    RAG_MIN_SCORE: float = 0.1
    RAG_SIMILARITY_THRESHOLD: float = 0.1  # Backward compatibility alias for score threshold

    # Database Settings
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'sample.db'}"
    
    # Authentication Settings
    JWT_SECRET_KEY: str = "sql-query-generator-secret-key-change-in-prod-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # File Upload Settings
    UPLOAD_DIR: str = str(DATA_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 15
    MAX_UPLOAD_ROWS: int = 50000

    # Query Execution Guardrails
    MAX_RESULT_ROWS: int = 500
    QUERY_TIMEOUT_SECONDS: int = 10
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("sqlite:///"):
            path_part = v[len("sqlite:///"):]
            p = Path(path_part)
            if not p.is_absolute():
                abs_path = (BASE_DIR / path_part).resolve()
                return f"sqlite:///{abs_path}"
        return v

    @field_validator("UPLOAD_DIR", mode="before")
    @classmethod
    def resolve_upload_dir(cls, v: str) -> str:
        if isinstance(v, str):
            p = Path(v)
            if not p.is_absolute():
                return str((BASE_DIR / p).resolve())
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v

settings = Settings()
