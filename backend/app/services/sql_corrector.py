from app.services.llm_provider import get_llm_provider
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLValidator, SQLValidationError
from app.schemas.responses import CorrectSQLResponse

class SQLCorrectorService:
    @classmethod
    def correct(cls, original_question: str, failed_sql: str, error_message: str) -> CorrectSQLResponse:
        schema_context = SchemaService.get_schema_prompt_context()
        provider = get_llm_provider()

        corrected_raw, explanation_of_fix = provider.correct_sql(
            question=original_question,
            failed_sql=failed_sql,
            error_msg=error_message,
            schema_context=schema_context
        )

        try:
            validated_sql = SQLValidator.validate(corrected_raw)
            is_safe = True
        except SQLValidationError as e:
            validated_sql = corrected_raw
            is_safe = False
            explanation_of_fix += f" (Note: Safety warning: {e.message})"

        return CorrectSQLResponse(
            original_sql=failed_sql,
            corrected_sql=validated_sql,
            explanation_of_fix=explanation_of_fix,
            is_safe=is_safe
        )
