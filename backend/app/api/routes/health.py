from fastapi import APIRouter
from sqlalchemy import text
from app.database.connection import engine
from app.core.config import settings
from app.services.llm_provider import get_llm_provider
from app.schemas.responses import HealthResponse

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health():
    # Check DB
    db_ok = False
    table_count = 0
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()
            db_ok = True
    except Exception:
        db_ok = False

    provider = get_llm_provider()

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        database={
            "connected": db_ok,
            "dialect": engine.dialect.name,
            "read_only_enforced": True
        },
        ai_provider={
            "provider": provider.provider_name,
            "is_configured": provider.is_configured,
            "configured_provider": settings.LLM_PROVIDER
        },
        version="1.0.0"
    )
