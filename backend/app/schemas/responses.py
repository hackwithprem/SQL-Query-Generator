from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class UserResponse(BaseModel):
    id: Union[int, str]
    full_name: str
    email: str
    created_at: Optional[str] = None

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ColumnSchema(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    nullable: bool = True
    default: Optional[str] = None

class ForeignKeySchema(BaseModel):
    constrained_columns: List[str]
    referred_table: str
    referred_columns: List[str]

class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnSchema]
    foreign_keys: List[ForeignKeySchema] = []
    row_count: Optional[int] = None

class DatabaseSchemaResponse(BaseModel):
    dialect: str
    tables: List[TableSchema]

class GenerateSQLResponse(BaseModel):
    sql: str
    question: str
    explanation: Optional[str] = None
    clarification: Optional[str] = None
    is_safe: bool = True
    provider: str
    target_database: Optional[str] = "SQLite Sample DB"
    schema_assumed: bool = False  # True when no schema was available and table/column names were inferred
    rag_applied: bool = False
    retrieved_examples: Optional[List[Dict[str, Any]]] = None

class ExecuteSQLResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    duration_ms: float
    sql: str
    truncated: bool = False
    target_database: Optional[str] = "SQLite Sample DB"

class ExplainSQLResponse(BaseModel):
    sql: str
    explanation: str
    breakdown: Optional[List[str]] = None

class CorrectSQLResponse(BaseModel):
    original_sql: str
    corrected_sql: str
    explanation_of_fix: str
    is_safe: bool = True

class HistoryItemResponse(BaseModel):
    id: Union[int, str]
    natural_query: str
    generated_sql: str
    executed: bool
    status: str
    execution_time_ms: Optional[float] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    ai_provider: Dict[str, Any]
    version: str = "1.0.0"

class UploadedDatasetResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    file_type: str
    sheet_name: Optional[str] = None
    table_name: str
    row_count: int
    column_count: int
    columns: List[Dict[str, Any]]
    status: str = "ready"
    created_at: Optional[str] = None

class DatasetPreviewResponse(BaseModel):
    dataset: UploadedDatasetResponse
    sample_rows: List[Dict[str, Any]]

class CloudConnectionResponse(BaseModel):
    id: str
    name: str
    provider: str
    host: str
    port: int
    database_name: str
    username: str
    ssl_enabled: bool
    extra_params: Optional[Dict[str, Any]] = None
    status: str = "configured"
    created_at: Optional[str] = None

class CloudConnectionTestResponse(BaseModel):
    success: bool
    message: str
    server_version: Optional[str] = None
    duration_ms: Optional[float] = None
