import os
import re
import json
import uuid
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings, DATA_DIR
from app.database.models import UploadedDataset, User
from app.schemas.responses import UploadedDatasetResponse, DatasetPreviewResponse
from app.services.supabase_service import SupabaseService

UPLOAD_BASE_DIR = Path(settings.UPLOAD_DIR)

def sanitize_identifier(raw_name: str) -> str:
    """Converts raw column or file names into safe, clean SQL identifiers."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", raw_name.strip())
    clean = re.sub(r"_+", "_", clean).strip("_")
    if not clean or clean[0].isdigit():
        clean = f"col_{clean}"
    return clean.lower()[:60]

def make_unique_column_names(columns: List[str]) -> List[Tuple[str, str]]:
    """
    Returns list of tuples (safe_sql_col_name, original_display_name).
    Ensures duplicate columns are made unique safely.
    """
    seen = {}
    result = []
    for col in columns:
        orig = str(col).strip() if str(col).strip() else "column"
        safe = sanitize_identifier(orig)
        if safe in seen:
            seen[safe] += 1
            safe = f"{safe}_{seen[safe]}"
        else:
            seen[safe] = 0
        result.append((safe, orig))
    return result

class DatasetService:
    @classmethod
    def get_user_upload_dir(cls, user_id: Any) -> Path:
        user_dir = UPLOAD_BASE_DIR / f"user_{user_id}"
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    @classmethod
    def parse_file_to_df(cls, filename: str, file_bytes: bytes, sheet_name: Optional[str] = None) -> Tuple[pd.DataFrame, str, Optional[str]]:
        ext = Path(filename).suffix.lower()
        file_stream = io.BytesIO(file_bytes)

        if ext == ".csv":
            try:
                df = pd.read_csv(file_stream, encoding="utf-8", low_memory=False)
            except UnicodeDecodeError:
                file_stream.seek(0)
                df = pd.read_csv(file_stream, encoding="latin1", low_memory=False)
            file_type = "csv"
            used_sheet = None
        else:
            excel_file = pd.ExcelFile(file_stream, engine="openpyxl")
            available_sheets = excel_file.sheet_names
            if not available_sheets:
                raise ValueError("Excel file contains no worksheets.")
            target_sheet = sheet_name if sheet_name and sheet_name in available_sheets else available_sheets[0]
            df = pd.read_excel(excel_file, sheet_name=target_sheet)
            file_type = "excel"
            used_sheet = target_sheet

        return df, file_type, used_sheet

    @classmethod
    def process_and_save_upload(
        cls,
        user: User,
        filename: str,
        file_bytes: bytes,
        sheet_name: Optional[str] = None
    ) -> UploadedDataset:
        # Enforce size limit
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValueError(f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

        ext = Path(filename).suffix.lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            raise ValueError("Unsupported file format. Please upload a .csv, .xlsx, or .xls file.")

        dataset_id = str(uuid.uuid4())
        user_dir = cls.get_user_upload_dir(user.id)
        db_path = user_dir / f"{dataset_id}.db"

        # Parse data safely in memory
        try:
            df, file_type, used_sheet = cls.parse_file_to_df(filename, file_bytes, sheet_name)
        except Exception as e:
            raise ValueError(f"Failed to parse data file: {str(e)}")

        if df.empty:
            raise ValueError("The uploaded file does not contain any data rows.")

        if len(df) > settings.MAX_UPLOAD_ROWS:
            raise ValueError(f"File contains {len(df)} rows, exceeding limit of {settings.MAX_UPLOAD_ROWS} rows.")

        # Normalize column names
        raw_cols = list(df.columns)
        unique_cols = make_unique_column_names(raw_cols)
        col_mapping = {raw: safe for raw, (safe, _) in zip(raw_cols, unique_cols)}
        df.rename(columns=col_mapping, inplace=True)

        columns_meta = []
        for safe_name, orig_display in unique_cols:
            dtype_str = str(df[safe_name].dtype)
            if "int" in dtype_str:
                sql_type = "INTEGER"
            elif "float" in dtype_str:
                sql_type = "REAL"
            elif "datetime" in dtype_str:
                sql_type = "DATETIME"
            else:
                sql_type = "TEXT"

            columns_meta.append({
                "name": safe_name,
                "display_name": orig_display,
                "type": sql_type,
                "nullable": bool(df[safe_name].isnull().any())
            })

        # Base table name from original file name
        base_name = Path(filename).stem
        table_name = sanitize_identifier(base_name) or "uploaded_data"

        # Save to user's isolated SQLite database
        sqlite_url = f"sqlite:///{db_path}"
        dataset_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        df.to_sql(table_name, dataset_engine, if_exists="replace", index=False)

        # Upload to Supabase Storage if configured
        storage_path = None
        user_supabase_id = getattr(user, "supabase_id", None) or str(user.id)
        if SupabaseService.is_configured():
            try:
                storage_path = SupabaseService.upload_private_file(user_supabase_id, filename, file_bytes)
            except Exception as e:
                print(f"Notice: Supabase file upload: {e}")

        # Create UploadedDataset record
        dataset_record = UploadedDataset(
            id=dataset_id,
            user_id=user.id,
            original_filename=filename,
            file_size_bytes=len(file_bytes),
            file_type=file_type,
            sheet_name=used_sheet,
            table_name=table_name,
            row_count=len(df),
            column_count=len(columns_meta),
            columns_json=json.dumps(columns_meta),
            sqlite_db_path=str(db_path),
            storage_path=storage_path
        )
        return dataset_record

    @classmethod
    def ensure_sqlite_db_exists(cls, dataset: UploadedDataset):
        """Ensures the isolated SQLite database file exists; rebuilds it from Supabase Storage if missing."""
        db_file = Path(dataset.sqlite_db_path)
        if db_file.exists():
            return

        # Missing locally — attempt reconstruction from Supabase Storage
        if dataset.storage_path and SupabaseService.is_configured():
            file_bytes = SupabaseService.download_private_file(dataset.storage_path)
            if file_bytes:
                df, _, _ = cls.parse_file_to_df(dataset.original_filename, file_bytes, dataset.sheet_name)
                # Re-apply column names
                cols = json.loads(dataset.columns_json)
                col_names = [c["name"] for c in cols]
                if len(col_names) == len(df.columns):
                    df.columns = col_names
                db_file.parent.mkdir(parents=True, exist_ok=True)
                engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
                df.to_sql(dataset.table_name, engine, if_exists="replace", index=False)

    @classmethod
    def get_dataset_preview(cls, dataset: UploadedDataset) -> DatasetPreviewResponse:
        cls.ensure_sqlite_db_exists(dataset)
        sqlite_url = f"sqlite:///{dataset.sqlite_db_path}"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        
        rows = []
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {dataset.table_name} LIMIT 15"))
                keys = list(result.keys())
                for r in result.fetchall():
                    row_dict = {}
                    for idx, k in enumerate(keys):
                        row_dict[k] = r[idx]
                    rows.append(row_dict)
        except Exception:
            rows = []

        cols = json.loads(dataset.columns_json)
        return DatasetPreviewResponse(
            dataset=UploadedDatasetResponse(
                id=dataset.id,
                original_filename=dataset.original_filename,
                file_size_bytes=dataset.file_size_bytes,
                file_type=dataset.file_type,
                sheet_name=dataset.sheet_name,
                table_name=dataset.table_name,
                row_count=dataset.row_count,
                column_count=dataset.column_count,
                columns=cols,
                status="ready",
                created_at=dataset.created_at.isoformat() if dataset.created_at else None
            ),
            sample_rows=rows
        )

    @classmethod
    def delete_dataset(cls, dataset: UploadedDataset):
        """Safely removes dataset from Supabase Storage and deletes SQLite file."""
        if dataset.storage_path and SupabaseService.is_configured():
            try:
                SupabaseService.delete_private_file(dataset.storage_path)
            except Exception as e:
                print(f"Warning deleting from Supabase Storage: {e}")

        try:
            p = Path(dataset.sqlite_db_path)
            if p.exists():
                p.unlink()
        except Exception:
            pass
