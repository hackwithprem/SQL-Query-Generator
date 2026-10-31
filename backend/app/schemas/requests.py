from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

class UserSignUpRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="User full name")
    email: str = Field(..., min_length=5, max_length=150, description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password with minimum 8 characters")

class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=1)

class GenerateSQLRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")
    dialect: Optional[str] = Field("sqlite", description="Database dialect, e.g. sqlite, postgresql, mysql, oracle")
    dataset_id: Optional[str] = Field(None, description="Optional uploaded dataset ID")
    connection_id: Optional[str] = Field(None, description="Optional external cloud connection ID")

class ExecuteSQLRequest(BaseModel):
    sql: str = Field(..., min_length=1, description="SQL query to execute")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Optional maximum rows to return")
    dataset_id: Optional[str] = Field(None, description="Optional uploaded dataset ID to execute against")
    connection_id: Optional[str] = Field(None, description="Optional external cloud connection ID to execute against")

class ExplainSQLRequest(BaseModel):
    sql: str = Field(..., min_length=1, description="SQL query to explain")
    question: Optional[str] = Field(None, description="Original question if available")
    dataset_id: Optional[str] = Field(None, description="Optional uploaded dataset ID")
    connection_id: Optional[str] = Field(None, description="Optional external cloud connection ID")

class CorrectSQLRequest(BaseModel):
    original_question: str = Field(..., description="Original plain English question")
    failed_sql: str = Field(..., description="The SQL query that failed")
    error_message: str = Field(..., description="The database error message returned")
    dataset_id: Optional[str] = Field(None, description="Optional uploaded dataset ID")
    connection_id: Optional[str] = Field(None, description="Optional external cloud connection ID")

class CloudConnectionTestRequest(BaseModel):
    provider: str = Field(..., description="oracle, postgresql, or mysql")
    name: Optional[str] = "Test Connection"
    host: str = Field(..., min_length=1)
    port: int = Field(...)
    database_name: str = Field(..., min_length=1, description="Database name or Oracle Service Name/SID")
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ssl_enabled: bool = False
    extra_params: Optional[Dict[str, Any]] = None

class CloudConnectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., description="oracle, postgresql, or mysql")
    host: str = Field(..., min_length=1)
    port: int = Field(...)
    database_name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ssl_enabled: bool = False
    extra_params: Optional[Dict[str, Any]] = None
