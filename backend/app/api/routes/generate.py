import json
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UploadedDataset, DatabaseConnectionModel
from app.schemas.requests import GenerateSQLRequest
from app.schemas.responses import GenerateSQLResponse
from app.services.sql_generator import SQLGeneratorService
from app.services.cloud_db_service import get_connector
from app.core.security import decrypt_credential
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/api", tags=["SQL Generation"])

@router.post("/generate-sql", response_model=GenerateSQLResponse)
def generate_sql(
    request: GenerateSQLRequest,
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

        response = SQLGeneratorService.generate(
            question=request.question,
            dialect=request.dialect or "sqlite",
            dataset=dataset,
            connector=connector,
            user_id=current_user.id if current_user else None,
            supabase_user_id=getattr(current_user, "supabase_id", None) if current_user else None
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SQL: {str(e)}"
        )
