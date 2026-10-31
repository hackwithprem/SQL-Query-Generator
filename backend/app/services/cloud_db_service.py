import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings
from app.core.security import encrypt_credential, decrypt_credential
from app.schemas.responses import (
    DatabaseSchemaResponse, 
    TableSchema, 
    ColumnSchema, 
    ForeignKeySchema,
    CloudConnectionTestResponse
)
from app.services.sql_validator import SQLValidator, SQLValidationError

class BaseCloudConnector(ABC):
    def __init__(self, host: str, port: int, database: str, username: str, password: str, ssl_enabled: bool = False, extra_params: Optional[Dict[str, Any]] = None):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.ssl_enabled = ssl_enabled
        self.extra_params = extra_params or {}

    @abstractmethod
    def get_connection_url(self) -> str:
        pass

    @property
    @abstractmethod
    def dialect_name(self) -> str:
        pass

    def test_connection(self) -> CloudConnectionTestResponse:
        start = time.perf_counter()
        try:
            engine = create_engine(
                self.get_connection_url(),
                pool_pre_ping=True,
                connect_args=self.get_connect_args()
            )
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1"))
                res.scalar()
            dur = round((time.perf_counter() - start) * 1000, 2)
            return CloudConnectionTestResponse(
                success=True,
                message=f"Successfully connected to {self.dialect_name.upper()} database at {self.host}:{self.port}/{self.database}",
                duration_ms=dur
            )
        except Exception as e:
            dur = round((time.perf_counter() - start) * 1000, 2)
            err_msg = str(e).split("\n")[0]
            return CloudConnectionTestResponse(
                success=False,
                message=f"Connection failed: {err_msg}",
                duration_ms=dur
            )

    def get_connect_args(self) -> Dict[str, Any]:
        return {}

    def get_schema(self) -> DatabaseSchemaResponse:
        engine = create_engine(
            self.get_connection_url(),
            pool_pre_ping=True,
            connect_args=self.get_connect_args()
        )
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        tables: List[TableSchema] = []
        for tbl in table_names[:40]: # reasonable limit
            try:
                pk_constraint = inspector.get_pk_constraint(tbl)
                pks = set(pk_constraint.get("constrained_columns", []))
            except Exception:
                pks = set()

            cols: List[ColumnSchema] = []
            try:
                for col in inspector.get_columns(tbl):
                    cols.append(ColumnSchema(
                        name=col["name"],
                        type=str(col["type"]),
                        primary_key=(col["name"] in pks),
                        nullable=col.get("nullable", True),
                        default=str(col.get("default")) if col.get("default") is not None else None
                    ))
            except Exception:
                pass

            fks: List[ForeignKeySchema] = []
            try:
                for fk in inspector.get_foreign_keys(tbl):
                    fks.append(ForeignKeySchema(
                        constrained_columns=fk.get("constrained_columns", []),
                        referred_table=fk.get("referred_table", ""),
                        referred_columns=fk.get("referred_columns", [])
                    ))
            except Exception:
                pass

            row_count = None
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
                    row_count = result.scalar()
            except Exception:
                row_count = None

            tables.append(TableSchema(
                table_name=tbl,
                columns=cols,
                foreign_keys=fks,
                row_count=row_count
            ))

        return DatabaseSchemaResponse(
            dialect=self.dialect_name,
            tables=tables
        )

    def execute_read_only(self, sql: str, limit: int = 500) -> Dict[str, Any]:
        # Validate read-only SQL
        validated_sql = SQLValidator.validate(sql)

        engine = create_engine(
            self.get_connection_url(),
            pool_pre_ping=True,
            connect_args=self.get_connect_args()
        )
        start_time = time.perf_counter()
        with engine.connect() as conn:
            result = conn.execute(text(validated_sql))
            columns = list(result.keys()) if result.returns_rows else []
            raw_rows = result.fetchmany(limit + 1) if result.returns_rows else []
        
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        truncated = len(raw_rows) > limit
        final_rows = raw_rows[:limit]

        rows = []
        for r in final_rows:
            d = {}
            for idx, col in enumerate(columns):
                val = r[idx]
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                d[col] = val
            rows.append(d)

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "duration_ms": duration_ms,
            "sql": validated_sql,
            "truncated": truncated
        }

class PostgresConnector(BaseCloudConnector):
    @property
    def dialect_name(self) -> str:
        return "postgresql"

    def get_connection_url(self) -> str:
        ssl_mode = "require" if self.ssl_enabled else "prefer"
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={ssl_mode}"

class MySQLConnector(BaseCloudConnector):
    @property
    def dialect_name(self) -> str:
        return "mysql"

    def get_connection_url(self) -> str:
        ssl_arg = "?ssl_ca=true" if self.ssl_enabled else ""
        return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}{ssl_arg}"

class OracleConnector(BaseCloudConnector):
    @property
    def dialect_name(self) -> str:
        return "oracle"

    def get_connection_url(self) -> str:
        # Use python-oracledb thin mode (no Instant Client needed)
        # Handle service_name vs SID
        is_sid = self.extra_params.get("use_sid", False)
        if is_sid:
            dsn = f"{self.host}:{self.port}/{self.database}"
        else:
            dsn = f"{self.host}:{self.port}/?service_name={self.database}"
        return f"oracle+oracledb://{self.username}:{self.password}@{self.host}:{self.port}/?service_name={self.database}"

def get_connector(
    provider: str,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    ssl_enabled: bool = False,
    extra_params: Optional[Dict[str, Any]] = None
) -> BaseCloudConnector:
    prov = provider.lower().strip()
    if prov in ["postgres", "postgresql"]:
        return PostgresConnector(host, port, database, username, password, ssl_enabled, extra_params)
    elif prov in ["mysql", "mariadb"]:
        return MySQLConnector(host, port, database, username, password, ssl_enabled, extra_params)
    elif prov in ["oracle", "oracledb"]:
        return OracleConnector(host, port, database, username, password, ssl_enabled, extra_params)
    else:
        raise ValueError(f"Unsupported database provider: '{provider}'. Supported: postgresql, mysql, oracle.")
