from typing import List, Dict, Any
from sqlalchemy import inspect, text
from app.database.connection import engine
from app.schemas.responses import DatabaseSchemaResponse, TableSchema, ColumnSchema, ForeignKeySchema

class SchemaService:
    @classmethod
    def get_schema(cls) -> DatabaseSchemaResponse:
        inspector = inspect(engine)
        dialect_name = engine.dialect.name
        table_names = inspector.get_table_names()

        tables: List[TableSchema] = []
        for table_name in table_names:
            if table_name == "query_history":
                continue # Skip internal table from business schema

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
        """
        Creates a clean, human-readable schema text representation for LLM prompting.
        """
        schema_data = cls.get_schema()
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
