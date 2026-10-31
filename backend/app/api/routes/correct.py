from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UploadedDataset, DatabaseConnectionModel
from app.schemas.requests import CorrectSQLRequest
from app.schemas.responses import CorrectSQLResponse
from app.services.sql_corrector import SQLCorrectorService
from app.services.cloud_db_service import get_connector
from app.core.security import decrypt_credential
from app.api.deps import get_optional_current_user
import json

router = APIRouter(prefix="/api", tags=["SQL Correction"])

@router.post("/correct-sql", response_model=CorrectSQLResponse)
def correct_sql(
    request: CorrectSQLRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    try:
        dataset = None
        connector = None

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

        response = SQLCorrectorService.correct(
            original_question=request.original_question,
            failed_sql=request.failed_sql,
            error_message=request.error_message,
            dataset=dataset,
            connector=connector
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to correct SQL: {str(e)}"
        )
