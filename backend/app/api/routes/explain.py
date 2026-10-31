from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UploadedDataset, DatabaseConnectionModel
from app.schemas.requests import ExplainSQLRequest
from app.schemas.responses import ExplainSQLResponse
from app.services.sql_explainer import SQLExplainerService
from app.services.cloud_db_service import get_connector
from app.core.security import decrypt_credential
from app.api.deps import get_optional_current_user
import json

router = APIRouter(prefix="/api", tags=["SQL Explanation"])

@router.post("/explain-sql", response_model=ExplainSQLResponse)
def explain_sql(
    request: ExplainSQLRequest,
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

        response = SQLExplainerService.explain(
            sql=request.sql,
            question=request.question,
            dataset=dataset,
            connector=connector
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain SQL: {str(e)}"
        )
