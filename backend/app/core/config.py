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
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Database Settings
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'sample.db'}"
    
    # Query Execution Guardrails
    MAX_RESULT_ROWS: int = 500
    QUERY_TIMEOUT_SECONDS: int = 10
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

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
