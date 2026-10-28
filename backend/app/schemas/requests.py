from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GenerateSQLRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")
    dialect: Optional[str] = Field("sqlite", description="Database dialect, e.g. sqlite, postgresql, mysql")

class ExecuteSQLRequest(BaseModel):
    sql: str = Field(..., min_length=1, description="SQL query to execute")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Optional maximum rows to return")

class ExplainSQLRequest(BaseModel):
    sql: str = Field(..., min_length=1, description="SQL query to explain")
    question: Optional[str] = Field(None, description="Original question if available")

class CorrectSQLRequest(BaseModel):
    original_question: str = Field(..., description="Original plain English question")
    failed_sql: str = Field(..., description="The SQL query that failed")
    error_message: str = Field(..., description="The database error message returned")
