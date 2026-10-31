import json
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UploadedDataset, DatabaseConnectionModel
from app.schemas.requests import ExecuteSQLRequest
from app.schemas.responses import ExecuteSQLResponse
from app.services.sql_executor import SQLExecutor, SQLExecutionError
from app.services.sql_validator import SQLValidationError
from app.services.history_service import HistoryService
from app.services.cloud_db_service import get_connector
from app.core.security import decrypt_credential
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/api", tags=["SQL Execution"])

@router.post("/execute-sql", response_model=ExecuteSQLResponse)
def execute_sql(
    request: ExecuteSQLRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    dataset = None
    connector = None
    user_id = current_user.id if current_user else None
    supabase_user_id = getattr(current_user, "supabase_id", None) if current_user else None

    if request.dataset_id:
        dataset_query = db.query(UploadedDataset).filter(UploadedDataset.id == request.dataset_id)
        if current_user:
            dataset_query = dataset_query.filter(UploadedDataset.user_id == current_user.id)
        dataset = dataset_query.first()
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified uploaded dataset was not found.")

    elif request.connection_id:
        conn_query = db.query(DatabaseConnectionModel).filter(DatabaseConnectionModel.id == request.connection_id)
        if current_user:
            conn_query = conn_query.filter(DatabaseConnectionModel.user_id == current_user.id)
        conn_record = conn_query.first()
        if not conn_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified cloud database connection was not found.")

        decrypted_pw = decrypt_credential(conn_record.encrypted_password)
        connector = get_connector(
            provider=conn_record.provider,
            host=conn_record.host,
            port=conn_record.port,
            database=conn_record.database_name,
            username=conn_record.username,
            password=decrypted_pw,
            ssl_enabled=conn_record.ssl_enabled,
            extra_params=json.loads(conn_record.extra_params) if conn_record.extra_params else None
        )

    try:
        result = SQLExecutor.execute(
            request.sql, 
            limit=request.limit, 
            dataset=dataset, 
            connector=connector
        )
        
        # Record successful execution in history
        HistoryService.record_query(
            natural_query="(Direct Execution / Review)",
            generated_sql=result.sql,
            executed=True,
            status="executed",
            execution_time_ms=result.duration_ms,
            row_count=result.row_count,
            user_id=user_id,
            supabase_user_id=supabase_user_id
        )
        return result
    except SQLValidationError as e:
        HistoryService.record_query(
            natural_query="(Validation Error)",
            generated_sql=request.sql,
            executed=False,
            status="failed",
            error_message=e.message,
            user_id=user_id,
            supabase_user_id=supabase_user_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security/Validation Violation: {e.message}"
        )
    except SQLExecutionError as e:
        err_detail = e.message
        # Provide a clear, honest explanation when execution fails due to missing table/schema mismatch.
        # This commonly happens when a schema-assumed query is executed against the sample DB
        # which doesn't contain the requested table (e.g. 'products' table not in University DB).
        lower_err = e.message.lower()
        if any(phrase in lower_err for phrase in ["no such table", "doesn't exist", "does not exist", "undefined table", "relation"]):
            err_detail = (
                f"{e.message}\n\n"
                "ℹ️ This query was generated without a specific database schema. "
                "To execute it, please upload a compatible dataset (CSV/Excel) or connect to a cloud database "
                "that contains the referenced tables. The University Sample Database only contains: "
                "students, courses, departments, enrollments, and marks tables."
            )
        HistoryService.record_query(
            natural_query="(Execution Failure)",
            generated_sql=request.sql,
            executed=True,
            status="failed",
            error_message=err_detail,
            user_id=user_id,
            supabase_user_id=supabase_user_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error executing query: {str(e)}"
        )
