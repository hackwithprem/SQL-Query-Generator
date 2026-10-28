from typing import Dict, Any
from app.services.llm_provider import get_llm_provider
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLValidator, SQLValidationError
from app.services.history_service import HistoryService
from app.schemas.responses import GenerateSQLResponse

class SQLGeneratorService:
    @classmethod
    def generate(cls, question: str, dialect: str = "sqlite") -> GenerateSQLResponse:
        # Step 1: Introspect dynamic schema
        schema_context = SchemaService.get_schema_prompt_context()

        # Step 2: Invoke provider
        provider = get_llm_provider()
        raw_sql = provider.generate_sql(question, schema_context, dialect)

        # Step 3: Validate generated SQL for security & read-only guarantee
        try:
            validated_sql = SQLValidator.validate(raw_sql)
            is_safe = True
            clarification = None
        except SQLValidationError as e:
            # LLM generated non-read-only or multi-statement SQL
            validated_sql = raw_sql
            is_safe = False
            clarification = f"Validation Warning: {e.message}"

        # Step 4: Record into history as generated
        HistoryService.record_query(
            natural_query=question,
            generated_sql=validated_sql,
            executed=False,
            status="generated" if is_safe else "validation_error",
            error_message=clarification
        )

        return GenerateSQLResponse(
            sql=validated_sql,
            question=question,
            explanation=None,
            clarification=clarification,
            is_safe=is_safe,
            provider=provider.provider_name
        )
