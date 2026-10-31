import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, DatabaseConnectionModel
from app.schemas.requests import CloudConnectionTestRequest, CloudConnectionCreateRequest
from app.schemas.responses import (
    CloudConnectionResponse, 
    CloudConnectionTestResponse,
    DatabaseSchemaResponse
)
from app.core.security import encrypt_credential, decrypt_credential
from app.services.cloud_db_service import get_connector
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/connections", tags=["Database Connections"])

@router.post("/test", response_model=CloudConnectionTestResponse)
def test_connection(
    request: CloudConnectionTestRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        connector = get_connector(
            provider=request.provider,
            host=request.host,
            port=request.port,
            database=request.database_name,
            username=request.username,
            password=request.password,
            ssl_enabled=request.ssl_enabled,
            extra_params=request.extra_params
        )
        return connector.test_connection()
    except ValueError as e:
        return CloudConnectionTestResponse(success=False, message=str(e))
    except Exception as e:
        return CloudConnectionTestResponse(success=False, message=f"Test failed: {str(e)}")

@router.post("", response_model=CloudConnectionResponse)
def create_connection(
    request: CloudConnectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate that connector can be formed
        connector = get_connector(
            provider=request.provider,
            host=request.host,
            port=request.port,
            database=request.database_name,
            username=request.username,
            password=request.password,
            ssl_enabled=request.ssl_enabled,
            extra_params=request.extra_params
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Encrypt password before storage
    encrypted_pw = encrypt_credential(request.password)
    conn_id = str(uuid.uuid4())

    record = DatabaseConnectionModel(
        id=conn_id,
        user_id=current_user.id,
        name=request.name.strip(),
        provider=request.provider.lower().strip(),
        host=request.host.strip(),
        port=request.port,
        database_name=request.database_name.strip(),
        username=request.username.strip(),
        encrypted_password=encrypted_pw,
        ssl_enabled=request.ssl_enabled,
        extra_params=json.dumps(request.extra_params) if request.extra_params else None
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return CloudConnectionResponse(
        id=record.id,
        name=record.name,
        provider=record.provider,
        host=record.host,
        port=record.port,
        database_name=record.database_name,
        username=record.username,
        ssl_enabled=record.ssl_enabled,
        extra_params=json.loads(record.extra_params) if record.extra_params else None,
        status="configured",
        created_at=record.created_at.isoformat() if record.created_at else None
    )

@router.get("", response_model=List[CloudConnectionResponse])
def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    connections = (
        db.query(DatabaseConnectionModel)
        .filter(DatabaseConnectionModel.user_id == current_user.id)
        .order_by(DatabaseConnectionModel.created_at.desc())
        .all()
    )
    result = []
    for c in connections:
        result.append(CloudConnectionResponse(
            id=c.id,
            name=c.name,
            provider=c.provider,
            host=c.host,
            port=c.port,
            database_name=c.database_name,
            username=c.username,
            ssl_enabled=c.ssl_enabled,
            extra_params=json.loads(c.extra_params) if c.extra_params else None,
            status="configured",
            created_at=c.created_at.isoformat() if c.created_at else None
        ))
    return result

@router.get("/{conn_id}/schema", response_model=DatabaseSchemaResponse)
def get_connection_schema(
    conn_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn_record = (
        db.query(DatabaseConnectionModel)
        .filter(DatabaseConnectionModel.id == conn_id, DatabaseConnectionModel.user_id == current_user.id)
        .first()
    )
    if not conn_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found or access denied.")

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
        return connector.get_schema()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to inspect remote schema: {str(e)}")

@router.delete("/{conn_id}")
def delete_connection(
    conn_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn_record = (
        db.query(DatabaseConnectionModel)
        .filter(DatabaseConnectionModel.id == conn_id, DatabaseConnectionModel.user_id == current_user.id)
        .first()
    )
    if not conn_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found or access denied.")

    db.delete(conn_record)
    db.commit()
    return {"message": "Connection removed successfully", "id": conn_id}
