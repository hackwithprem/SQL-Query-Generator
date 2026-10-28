from fastapi import APIRouter, HTTPException, status
from app.schemas.requests import ExecuteSQLRequest
from app.schemas.responses import ExecuteSQLResponse
from app.services.sql_executor import SQLExecutor, SQLExecutionError
from app.services.sql_validator import SQLValidationError
from app.services.history_service import HistoryService

router = APIRouter(prefix="/api", tags=["SQL Execution"])

@router.post("/execute-sql", response_model=ExecuteSQLResponse)
def execute_sql(request: ExecuteSQLRequest):
    try:
        result = SQLExecutor.execute(request.sql, limit=request.limit)
        
        # Record successful execution in history
        HistoryService.record_query(
            natural_query="(Direct Execution / Review)",
            generated_sql=result.sql,
            executed=True,
            status="executed",
            execution_time_ms=result.duration_ms,
            row_count=result.row_count
        )
        return result
    except SQLValidationError as e:
        HistoryService.record_query(
            natural_query="(Validation Error)",
            generated_sql=request.sql,
            executed=False,
            status="failed",
            error_message=e.message
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security/Validation Violation: {e.message}"
        )
    except SQLExecutionError as e:
        HistoryService.record_query(
            natural_query="(Execution Failure)",
            generated_sql=request.sql,
            executed=True,
            status="failed",
            error_message=e.message
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error executing query: {str(e)}"
        )
