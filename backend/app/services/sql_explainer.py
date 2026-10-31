from typing import Optional
from app.services.llm_provider import get_llm_provider
from app.services.schema_service import SchemaService
from app.schemas.responses import ExplainSQLResponse
from app.database.models import UploadedDataset
from app.services.cloud_db_service import BaseCloudConnector

class SQLExplainerService:
    @classmethod
    def explain(
        cls, 
        sql: str, 
        question: Optional[str] = None,
        dataset: Optional[UploadedDataset] = None,
        connector: Optional[BaseCloudConnector] = None
    ) -> ExplainSQLResponse:
        if dataset:
            schema_context = SchemaService.get_dataset_prompt_context(dataset)
        elif connector:
            conn_schema = connector.get_schema()
            schema_context = SchemaService.get_connection_prompt_context(conn_schema)
        else:
            schema_context = SchemaService.get_schema_prompt_context()

        provider = get_llm_provider()
        res = provider.explain_sql(sql, schema_context, question)
        
        explanation = res.get("explanation", "Could not generate explanation.")
        return ExplainSQLResponse(
            sql=sql,
            explanation=explanation,
            breakdown=None
        )
