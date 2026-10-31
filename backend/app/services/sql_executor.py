import time
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text
from app.database.connection import engine as sample_engine
from app.core.config import settings
from app.services.sql_validator import SQLValidator, SQLValidationError
from app.schemas.responses import ExecuteSQLResponse
from app.database.models import UploadedDataset
from app.services.cloud_db_service import BaseCloudConnector

class SQLExecutionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class SQLExecutor:
    @classmethod
    def execute(
        cls, 
        raw_sql: str, 
        limit: Optional[int] = None,
        dataset: Optional[UploadedDataset] = None,
        connector: Optional[BaseCloudConnector] = None
    ) -> ExecuteSQLResponse:
        """
        Validates and executes a read-only SQL query against the target database
        (Sample Academic DB, User Uploaded CSV/Excel SQLite DB, or Cloud Database).
        """
        # Step 1: Validate query
        validated_sql = SQLValidator.validate(raw_sql)

        # Step 2: Determine effective limit
        effective_limit = settings.MAX_RESULT_ROWS
        if limit and 1 <= limit <= settings.MAX_RESULT_ROWS:
            effective_limit = limit

        # If Cloud Connector
        if connector:
            try:
                res_dict = connector.execute_read_only(validated_sql, limit=effective_limit)
                return ExecuteSQLResponse(
                    columns=res_dict["columns"],
                    rows=res_dict["rows"],
                    row_count=res_dict["row_count"],
                    duration_ms=res_dict["duration_ms"],
                    sql=res_dict["sql"],
                    truncated=res_dict["truncated"],
                    target_database=f"Cloud Database ({connector.dialect_name.upper()})"
                )
            except SQLValidationError as e:
                raise e
            except Exception as e:
                clean_err = cls._sanitize_error(str(e))
                raise SQLExecutionError(f"Cloud Database Error: {clean_err}")

        # Target Engine: User Uploaded DB or Sample DB
        if dataset:
            from app.services.dataset_service import DatasetService
            DatasetService.ensure_sqlite_db_exists(dataset)
            target_engine = create_engine(f"sqlite:///{dataset.sqlite_db_path}", connect_args={"check_same_thread": False})
            target_desc = f"Uploaded Dataset ({dataset.original_filename})"
        else:
            target_engine = sample_engine
            target_desc = "SQLite Sample DB"

        start_time = time.perf_counter()

        try:
            with target_engine.connect() as conn:
                result = conn.execute(text(validated_sql))
                columns = list(result.keys()) if result.returns_rows else []
                raw_rows = result.fetchmany(effective_limit + 1) if result.returns_rows else []

            end_time = time.perf_counter()
            duration_ms = round((end_time - start_time) * 1000, 2)

            truncated = len(raw_rows) > effective_limit
            final_rows_data = raw_rows[:effective_limit]

            # Convert rows to dicts with JSON-safe values
            rows: List[Dict[str, Any]] = []
            for row in final_rows_data:
                row_dict = {}
                for idx, col in enumerate(columns):
                    val = row[idx]
                    if hasattr(val, "isoformat"):
                        val = val.isoformat()
                    row_dict[col] = val
                rows.append(row_dict)

            return ExecuteSQLResponse(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                duration_ms=duration_ms,
                sql=validated_sql,
                truncated=truncated,
                target_database=target_desc
            )

        except SQLValidationError as e:
            raise e
        except Exception as e:
            err_msg = str(e)
            sanitized_msg = cls._sanitize_error(err_msg)
            raise SQLExecutionError(f"Database Execution Error: {sanitized_msg}")

    @classmethod
    def _sanitize_error(cls, error_msg: str) -> str:
        clean = error_msg.split("[SQL:")[0].strip()
        if "(sqlite3.OperationalError)" in clean:
            clean = clean.replace("(sqlite3.OperationalError)", "").strip()
        elif "(sqlite3.DatabaseError)" in clean:
            clean = clean.replace("(sqlite3.DatabaseError)", "").strip()
        return clean
