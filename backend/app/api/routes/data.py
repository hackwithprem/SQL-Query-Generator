import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UploadedDataset
from app.schemas.responses import UploadedDatasetResponse, DatasetPreviewResponse
from app.services.dataset_service import DatasetService
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/data", tags=["Data Upload"])

@router.post("/upload", response_model=UploadedDatasetResponse)
async def upload_file(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing."
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    try:
        dataset_record = DatasetService.process_and_save_upload(
            user=current_user,
            filename=file.filename,
            file_bytes=content,
            sheet_name=sheet_name
        )
        db.add(dataset_record)
        db.commit()
        db.refresh(dataset_record)

        cols = json.loads(dataset_record.columns_json)
        return UploadedDatasetResponse(
            id=dataset_record.id,
            original_filename=dataset_record.original_filename,
            file_size_bytes=dataset_record.file_size_bytes,
            file_type=dataset_record.file_type,
            sheet_name=dataset_record.sheet_name,
            table_name=dataset_record.table_name,
            row_count=dataset_record.row_count,
            column_count=dataset_record.column_count,
            columns=cols,
            status="ready",
            created_at=dataset_record.created_at.isoformat() if dataset_record.created_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload processing failed: {str(e)}")

@router.get("/files", response_model=List[UploadedDatasetResponse])
@router.get("/datasets", response_model=List[UploadedDatasetResponse])
def list_user_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    datasets = (
        db.query(UploadedDataset)
        .filter(UploadedDataset.user_id == current_user.id)
        .order_by(UploadedDataset.created_at.desc())
        .all()
    )
    result = []
    for d in datasets:
        cols = json.loads(d.columns_json)
        result.append(UploadedDatasetResponse(
            id=d.id,
            original_filename=d.original_filename,
            file_size_bytes=d.file_size_bytes,
            file_type=d.file_type,
            sheet_name=d.sheet_name,
            table_name=d.table_name,
            row_count=d.row_count,
            column_count=d.column_count,
            columns=cols,
            status="ready",
            created_at=d.created_at.isoformat() if d.created_at else None
        ))
    return result

@router.get("/files/{file_id}/preview", response_model=DatasetPreviewResponse)
@router.get("/preview/{file_id}", response_model=DatasetPreviewResponse)
@router.get("/datasets/{file_id}/preview", response_model=DatasetPreviewResponse)
def get_file_preview(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = (
        db.query(UploadedDataset)
        .filter(UploadedDataset.id == file_id, UploadedDataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found or access denied.")

    return DatasetService.get_dataset_preview(dataset)

@router.delete("/files/{file_id}")
@router.delete("/datasets/{file_id}")
def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = (
        db.query(UploadedDataset)
        .filter(UploadedDataset.id == file_id, UploadedDataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found or access denied.")

    DatasetService.delete_dataset(dataset)
    db.delete(dataset)
    db.commit()
    return {"message": "Dataset deleted successfully", "id": file_id}

from pydantic import BaseModel
class RenameDatasetRequest(BaseModel):
    new_name: str

@router.patch("/files/{file_id}/rename")
@router.patch("/datasets/{file_id}/rename")
def rename_dataset(
    file_id: str,
    req: RenameDatasetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = (
        db.query(UploadedDataset)
        .filter(UploadedDataset.id == file_id, UploadedDataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found or access denied.")
    clean_name = req.new_name.strip()
    if not clean_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be empty.")
    dataset.original_filename = clean_name
    db.commit()
    return {"message": "Dataset renamed successfully", "id": file_id, "new_name": clean_name}

