from typing import Dict, Any, Optional
from app.services.llm_provider import get_llm_provider
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLValidator, SQLValidationError
from app.services.history_service import HistoryService
from app.schemas.responses import GenerateSQLResponse
from app.database.models import UploadedDataset
from app.services.cloud_db_service import BaseCloudConnector

class SQLGeneratorService:
    @classmethod
    def generate(
        cls, 
        question: str, 
        dialect: str = "sqlite",
        dataset: Optional[UploadedDataset] = None,
        connector: Optional[BaseCloudConnector] = None,
        user_id: Optional[int] = None,
        supabase_user_id: Optional[str] = None
    ) -> GenerateSQLResponse:
        # Step 1: Introspect dynamic schema based on target (schema is optional)
        schema_assumed = False

        if dataset:
            effective_dialect = "sqlite"
            schema_context = SchemaService.get_dataset_prompt_context(dataset)
            target_desc = f"Uploaded Dataset ({dataset.original_filename})"
        elif connector:
            effective_dialect = connector.dialect_name
            conn_schema = connector.get_schema()
            schema_context = SchemaService.get_connection_prompt_context(conn_schema)
            target_desc = f"Cloud Database ({connector.dialect_name.upper()})"
        else:
            # No explicit dataset or connection selected.
            # Use schema-free generation: the LLM generates SQL using reasonable naming conventions
            # without being constrained by the University Sample DB schema. This allows answering
            # ANY question (e.g. about products, orders, customers) without a SCHEMA_ERROR block.
            # The sample DB schema is only relevant at execution time.
            effective_dialect = dialect or "sqlite"
            schema_context = ""
            schema_assumed = True
            target_desc = "SQLite Sample DB"

        # Step 2: Retrieve relevant SQL pattern examples via RAG (if enabled)
        retrieved_examples = []
        try:
            from app.services.rag.rag_service import RAGService
            retrieved_examples = RAGService.retrieve_relevant_examples(question)
        except Exception:
            # RAG failure should never block or fail query generation
            retrieved_examples = []

        # Step 3: Invoke provider — schema_context may be empty for schema-free generation
        provider = get_llm_provider()
        raw_sql = provider.generate_sql(
            question=question,
            schema_context=schema_context,
            dialect=effective_dialect,
            retrieved_examples=retrieved_examples
        )

        # Step 4: Check if provider returned a SCHEMA_ERROR despite our instructions.
        # This should only happen for real schema providers (Groq/Gemini) when a schema IS
        # provided but the requested entity genuinely does not exist in it.
        # For schema-free generation or MockOffline, we never return SCHEMA_ERROR anymore.
        is_schema_error = False
        schema_error_msg = None

        if raw_sql.startswith("SCHEMA_ERROR:"):
            is_schema_error = True
            schema_error_msg = raw_sql.replace("SCHEMA_ERROR:", "", 1).strip()
        elif raw_sql.strip().startswith("--") and any(
            phrase in raw_sql.lower() for phrase in [
                "does not exist", "doesn't exist", "not found", "no such table",
                "no table", "no products table", "cannot list", "cannot find"
            ]
        ):
            is_schema_error = True
            schema_error_msg = raw_sql.strip().lstrip("- ").strip()

        # Only block generation if a real schema WAS provided and the entity truly doesn't exist.
        # If schema_assumed is True (no schema context), never block — the LLM assumed names.
        if is_schema_error and not schema_assumed:
            HistoryService.record_query(
                natural_query=question,
                generated_sql="",
                executed=False,
                status="schema_error",
                error_message=schema_error_msg,
                user_id=user_id,
                supabase_user_id=supabase_user_id
            )
            return GenerateSQLResponse(
                sql="",
                question=question,
                explanation=schema_error_msg,
                clarification=schema_error_msg,
                is_safe=False,
                provider=provider.provider_name,
                target_database=target_desc,
                schema_assumed=False,
                rag_applied=bool(retrieved_examples),
                retrieved_examples=retrieved_examples if retrieved_examples else None
            )

        # Step 4: Validate generated SQL for security & read-only guarantee
        try:
            validated_sql = SQLValidator.validate(raw_sql)
            is_safe = True
            clarification = None
        except SQLValidationError as e:
            # If the raw output is an SQL comment, explain the missing data
            if raw_sql.strip().startswith("--"):
                comment_text = raw_sql.strip().lstrip("- ").strip()
                return GenerateSQLResponse(
                    sql="",
                    question=question,
                    explanation=comment_text,
                    clarification=comment_text,
                    is_safe=False,
                    provider=provider.provider_name,
                    target_database=target_desc,
                    schema_assumed=schema_assumed,
                    rag_applied=bool(retrieved_examples),
                    retrieved_examples=retrieved_examples if retrieved_examples else None
                )
            validated_sql = raw_sql
            is_safe = False
            clarification = f"Validation Warning: {e.message}"

        # Build clarification note if schema was assumed (schema-free generation)
        if schema_assumed and not clarification:
            clarification = (
                "⚠️ No database schema was available. Table and column names are assumed based on your question "
                "and standard naming conventions. Review the query before executing against your actual database."
            )

        # Step 5: Record into history as generated
        HistoryService.record_query(
            natural_query=question,
            generated_sql=validated_sql,
            executed=False,
            status="generated" if is_safe else "validation_error",
            error_message=clarification,
            user_id=user_id,
            supabase_user_id=supabase_user_id
        )

        return GenerateSQLResponse(
            sql=validated_sql,
            question=question,
            explanation=None,
            clarification=clarification,
            is_safe=is_safe,
            provider=provider.provider_name,
            target_database=target_desc,
            schema_assumed=schema_assumed,
            rag_applied=bool(retrieved_examples),
            retrieved_examples=retrieved_examples if retrieved_examples else None
        )
