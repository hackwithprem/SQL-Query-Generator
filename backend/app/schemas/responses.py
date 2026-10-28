from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ColumnSchema(BaseModel):
    name: str
    type: str
    primary_key: bool
    nullable: bool
    default: Optional[str] = None

class ForeignKeySchema(BaseModel):
    constrained_columns: List[str]
    referred_table: str
    referred_columns: List[str]

class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnSchema]
    foreign_keys: List[ForeignKeySchema]
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

class ExecuteSQLResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    duration_ms: float
    sql: str
    truncated: bool = False

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
    id: int
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
