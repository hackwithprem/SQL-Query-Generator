import time
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from app.database.connection import engine
from app.core.config import settings
from app.services.sql_validator import SQLValidator, SQLValidationError
from app.schemas.responses import ExecuteSQLResponse

class SQLExecutionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class SQLExecutor:
    @classmethod
    def execute(cls, raw_sql: str, limit: Optional[int] = None) -> ExecuteSQLResponse:
        """
        Validates and executes a read-only SQL query against the database.
        Returns columns, records, count, and duration.
        """
        # Step 1: Validate query
        validated_sql = SQLValidator.validate(raw_sql)

        # Step 2: Determine effective limit
        effective_limit = settings.MAX_RESULT_ROWS
        if limit and 1 <= limit <= settings.MAX_RESULT_ROWS:
            effective_limit = limit

        start_time = time.perf_counter()

        try:
            with engine.connect() as conn:
                # Execute query
                result = conn.execute(text(validated_sql))
                
                columns = list(result.keys()) if result.returns_rows else []
                
                # Fetch up to limit + 1 to detect truncation
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
                    # Handle date/datetime/bytes conversion if needed
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
                truncated=truncated
            )

        except SQLValidationError as e:
            raise e
        except Exception as e:
            err_msg = str(e)
            # Sanitize error message to prevent database path/secret leakage
            sanitized_msg = cls._sanitize_error(err_msg)
            raise SQLExecutionError(f"Database Execution Error: {sanitized_msg}")

    @classmethod
    def _sanitize_error(cls, error_msg: str) -> str:
        # Strip internal file paths or credentials if present
        clean = re_strip_paths = error_msg.split("[SQL:")[0].strip()
        # Clean up common sqlalchemy prefixes
        if "(sqlite3.OperationalError)" in clean:
            clean = clean.replace("(sqlite3.OperationalError)", "").strip()
        elif "(sqlite3.DatabaseError)" in clean:
            clean = clean.replace("(sqlite3.DatabaseError)", "").strip()
        return clean
