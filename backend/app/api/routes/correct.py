from fastapi import APIRouter, HTTPException, status
from app.schemas.requests import CorrectSQLRequest
from app.schemas.responses import CorrectSQLResponse
from app.services.sql_corrector import SQLCorrectorService

router = APIRouter(prefix="/api", tags=["SQL Correction"])

@router.post("/correct-sql", response_model=CorrectSQLResponse)
def correct_sql(request: CorrectSQLRequest):
    try:
        response = SQLCorrectorService.correct(
            original_question=request.original_question,
            failed_sql=request.failed_sql,
            error_message=request.error_message
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to correct SQL: {str(e)}"
        )
