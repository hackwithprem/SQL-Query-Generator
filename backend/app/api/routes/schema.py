from fastapi import APIRouter, HTTPException, status
from app.schemas.responses import DatabaseSchemaResponse
from app.services.schema_service import SchemaService

router = APIRouter(prefix="/api", tags=["Database Schema"])

@router.get("/schema", response_model=DatabaseSchemaResponse)
def get_schema():
    try:
        schema = SchemaService.get_schema()
        return schema
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect database schema: {str(e)}"
        )
