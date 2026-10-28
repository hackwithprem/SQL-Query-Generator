from fastapi import APIRouter, HTTPException, status
from app.schemas.requests import ExplainSQLRequest
from app.schemas.responses import ExplainSQLResponse
from app.services.sql_explainer import SQLExplainerService

router = APIRouter(prefix="/api", tags=["SQL Explanation"])

@router.post("/explain-sql", response_model=ExplainSQLResponse)
def explain_sql(request: ExplainSQLRequest):
    try:
        response = SQLExplainerService.explain(request.sql, question=request.question)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain SQL: {str(e)}"
        )
