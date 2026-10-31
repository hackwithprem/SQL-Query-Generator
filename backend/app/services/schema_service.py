import json
from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, text, create_engine
from app.database.connection import engine
from app.database.models import UploadedDataset
from app.schemas.responses import DatabaseSchemaResponse, TableSchema, ColumnSchema, ForeignKeySchema

INTERNAL_TABLES = {"query_history", "users", "uploaded_datasets", "database_connections"}

class SchemaService:
    @classmethod
    def get_schema(cls) -> DatabaseSchemaResponse:
        inspector = inspect(engine)
        dialect_name = engine.dialect.name
        table_names = inspector.get_table_names()

        tables: List[TableSchema] = []
        for table_name in table_names:
            if table_name in INTERNAL_TABLES:
                continue # Skip internal system tables from business schema

            # Columns
            columns: List[ColumnSchema] = []
            pk_constraint = inspector.get_pk_constraint(table_name)
            pks = set(pk_constraint.get("constrained_columns", []))

            for col in inspector.get_columns(table_name):
                columns.append(ColumnSchema(
                    name=col["name"],
                    type=str(col["type"]),
                    primary_key=(col["name"] in pks),
                    nullable=col.get("nullable", True),
                    default=str(col.get("default")) if col.get("default") is not None else None
                ))

            # Foreign keys
            fks: List[ForeignKeySchema] = []
            for fk in inspector.get_foreign_keys(table_name):
                fks.append(ForeignKeySchema(
                    constrained_columns=fk.get("constrained_columns", []),
                    referred_table=fk.get("referred_table", ""),
                    referred_columns=fk.get("referred_columns", [])
                ))

            # Count rows
            row_count = None
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = result.scalar()
            except Exception:
                row_count = None

            tables.append(TableSchema(
                table_name=table_name,
                columns=columns,
                foreign_keys=fks,
                row_count=row_count
            ))

        return DatabaseSchemaResponse(
            dialect=dialect_name,
            tables=tables
        )

    @classmethod
    def get_schema_prompt_context(cls) -> str:
        """Creates a clean, human-readable schema text representation for LLM prompting.
        Returns an empty string if no user-facing tables exist in the sample database."""
        schema_data = cls.get_schema()

        if not schema_data.tables:
            return ""  # Signal to callers that no schema context is available

        lines = [f"Database Dialect: {schema_data.dialect.upper()}", "Available Tables and Columns:"]

        for table in schema_data.tables:
            col_strs = []
            for col in table.columns:
                pk_str = " (PRIMARY KEY)" if col.primary_key else ""
                col_strs.append(f"  - {col.name}: {col.type}{pk_str}")

            fk_strs = []
            for fk in table.foreign_keys:
                src_cols = ", ".join(fk.constrained_columns)
                ref_cols = ", ".join(fk.referred_columns)
                fk_strs.append(f"  - Foreign Key: ({src_cols}) REFERENCES {fk.referred_table}({ref_cols})")

            lines.append(f"\nTable: {table.table_name}")
            lines.append("Columns:")
            lines.extend(col_strs)
            if fk_strs:
                lines.append("Relationships:")
                lines.extend(fk_strs)

        return "\n".join(lines)

    @classmethod
    def get_dataset_prompt_context(cls, dataset: UploadedDataset) -> str:
        """Builds schema prompt context for a user-uploaded CSV/Excel dataset."""
        cols_meta = json.loads(dataset.columns_json)
        lines = [
            f"Database Dialect: SQLITE",
            f"Source File: {dataset.original_filename} (Uploaded Dataset)",
            f"Available Table: {dataset.table_name}",
            "Columns:"
        ]
        for c in cols_meta:
            display_hint = f" (Display Name in file: '{c['display_name']}')" if c['name'] != c['display_name'] else ""
            lines.append(f"  - {c['name']}: {c['type']}{display_hint}")

        return "\n".join(lines)

    @classmethod
    def get_connection_prompt_context(cls, schema_data: DatabaseSchemaResponse) -> str:
        """Builds schema prompt context for an external cloud database connection."""
        lines = [f"Database Dialect: {schema_data.dialect.upper()}", "Available Tables and Columns:"]
        for table in schema_data.tables:
            col_strs = []
            for col in table.columns:
                pk_str = " (PRIMARY KEY)" if col.primary_key else ""
                col_strs.append(f"  - {col.name}: {col.type}{pk_str}")

            fk_strs = []
            for fk in table.foreign_keys:
                src_cols = ", ".join(fk.constrained_columns)
                ref_cols = ", ".join(fk.referred_columns)
                fk_strs.append(f"  - Foreign Key: ({src_cols}) REFERENCES {fk.referred_table}({ref_cols})")

            lines.append(f"\nTable: {table.table_name}")
            lines.append("Columns:")
            lines.extend(col_strs)
            if fk_strs:
                lines.append("Relationships:")
                lines.extend(fk_strs)

        return "\n".join(lines)
