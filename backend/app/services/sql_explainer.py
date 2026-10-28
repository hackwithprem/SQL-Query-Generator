from typing import Optional
from app.services.llm_provider import get_llm_provider
from app.services.schema_service import SchemaService
from app.schemas.responses import ExplainSQLResponse

class SQLExplainerService:
    @classmethod
    def explain(cls, sql: str, question: Optional[str] = None) -> ExplainSQLResponse:
        schema_context = SchemaService.get_schema_prompt_context()
        provider = get_llm_provider()
        res = provider.explain_sql(sql, schema_context, question)
        
        explanation = res.get("explanation", "Could not generate explanation.")
        return ExplainSQLResponse(
            sql=sql,
            explanation=explanation,
            breakdown=None
        )
