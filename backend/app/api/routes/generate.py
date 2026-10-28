from fastapi import APIRouter, HTTPException, status
from app.schemas.requests import GenerateSQLRequest
from app.schemas.responses import GenerateSQLResponse
from app.services.sql_generator import SQLGeneratorService

router = APIRouter(prefix="/api", tags=["SQL Generation"])

@router.post("/generate-sql", response_model=GenerateSQLResponse)
def generate_sql(request: GenerateSQLRequest):
    try:
        response = SQLGeneratorService.generate(request.question, dialect=request.dialect or "sqlite")
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SQL: {str(e)}"
        )
