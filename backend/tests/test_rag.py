import pytest
from unittest.mock import MagicMock, patch
from app.core.config import settings
from app.services.rag.knowledge_base import SQL_EXAMPLES
from app.services.rag.rag_service import RAGService, tokenize, stem_token
from app.services.sql_generator import SQLGeneratorService
from app.services.llm_provider import GroqProvider
from app.schemas.responses import GenerateSQLResponse


def test_knowledge_base_size_and_structure():
    """Verify the initial knowledge base contains at least 30-50 verified examples with all required keys."""
    assert len(SQL_EXAMPLES) >= 30, f"Expected at least 30 examples, found {len(SQL_EXAMPLES)}"
    for ex in SQL_EXAMPLES:
        assert "id" in ex
        assert "question" in ex and len(ex["question"]) > 5
        assert "sql_query" in ex and "SELECT" in ex["sql_query"].upper()
        assert "category" in ex


def test_bm25_tokenization_and_stemming():
    """Verify lowercase normalization, stop-word removal, and morphological stemming."""
    text = "Show students who scored more than 80 marks in products"
    tokens = tokenize(text)
    # Stop words like 'who', 'than', 'in' should be filtered out
    assert "who" not in tokens
    assert "than" not in tokens
    assert "in" not in tokens

    # Content tokens and stemmed variations should be present
    assert "students" in tokens
    assert "student" in tokens
    assert "scored" in tokens
    assert "80" in tokens
    assert "marks" in tokens
    assert "products" in tokens
    assert "product" in tokens

    # Verify stem_token directly
    assert stem_token("customers") == "customer"
    assert stem_token("departments") == "department"
    assert stem_token("pricing") == "pric"
    assert stem_token("pass") == "pass"


def test_rag_retrieval_university_marks():
    """Verify 'Show students who scored more than 80 marks' retrieves the university marks example."""
    question = "Show students who scored more than 80 marks"
    results = RAGService.retrieve_relevant_examples(question, top_k=3)
    assert len(results) > 0

    top_match = results[0]
    # Required response structure
    assert "id" in top_match
    assert "question" in top_match
    assert "sql_query" in top_match
    assert "category" in top_match
    assert "dialect" in top_match
    assert "similarity" in top_match
    assert "score" in top_match

    # Verify it maps to the verified university marks example (ex_40)
    assert top_match["id"] == "ex_40"
    assert "marks" in top_match["sql_query"].lower()
    assert "80" in top_match["sql_query"]
    assert top_match["score"] > 5.0
    assert top_match["similarity"] > 5.0


def test_rag_retrieval_product_examples():
    """Verify product-related questions retrieve relevant product examples."""
    question = "Find products priced higher than 100 dollars"
    results = RAGService.retrieve_relevant_examples(question, top_k=3)
    assert len(results) > 0

    top_match = results[0]
    assert top_match["id"] == "ex_04"
    assert "products" in top_match["sql_query"].lower()
    assert "100" in top_match["sql_query"]

    # Also test generic product lookup
    gen_results = RAGService.retrieve_relevant_examples("List all products in inventory", top_k=3)
    assert len(gen_results) > 0
    assert any("product" in r["question"].lower() for r in gen_results)


def test_rag_retrieval_aggregation_group_by():
    """Verify aggregation questions retrieve GROUP BY examples."""
    question = "Calculate average score for each course"
    results = RAGService.retrieve_relevant_examples(question, top_k=3)
    assert len(results) > 0

    # Verify top matches contain GROUP BY queries
    assert any("GROUP BY" in r["sql_query"].upper() for r in results)
    top_categories = [r.get("category", "") for r in results]
    assert any("group_by" in c or "avg" in c for c in top_categories)


def test_rag_threshold_and_empty_retrieval():
    """Verify unrelated queries or empty terms return an empty list without error."""
    # Completely unrelated query with no term overlap
    results = RAGService.retrieve_relevant_examples("Quantum physics entanglement observation data")
    assert results == []

    # Empty string or whitespace
    assert RAGService.retrieve_relevant_examples("") == []
    assert RAGService.retrieve_relevant_examples("   ") == []

    # Only stop words
    assert RAGService.retrieve_relevant_examples("what is that then there") == []

    # Very high threshold filter
    high_threshold_results = RAGService.retrieve_relevant_examples(
        "List all customers",
        threshold=999.0
    )
    assert len(high_threshold_results) == 0


def test_rag_disabled_fallback():
    """Verify that when RAG_ENABLED is false, retrieve_relevant_examples returns empty list without error."""
    original_setting = settings.RAG_ENABLED
    try:
        settings.RAG_ENABLED = False
        results = RAGService.retrieve_relevant_examples("List all customers")
        assert results == []
    finally:
        settings.RAG_ENABLED = original_setting


def test_rag_enabled_augments_groq_prompt():
    """Verify RAG_ENABLED=true retrieves examples and augments the Groq system prompt."""
    provider = GroqProvider(api_key="mock_key")
    provider._client = MagicMock()

    # Mock chat completion response
    mock_choice = MagicMock()
    mock_choice.message.content = "SELECT * FROM students;"
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    provider._client.chat.completions.create.return_value = mock_completion

    sample_examples = [
        {
            "id": "ex_40",
            "question": "List students who scored more than 80 marks in any exam",
            "sql_query": "SELECT * FROM marks WHERE score > 80;",
            "category": "domain_university_marks",
            "similarity": 21.8
        }
    ]

    provider.generate_sql(
        question="Show students who scored more than 80 marks",
        schema_context="",
        dialect="sqlite",
        retrieved_examples=sample_examples
    )

    # Inspect the system prompt passed to Groq client
    call_args = provider._client.chat.completions.create.call_args
    assert call_args is not None
    messages = call_args.kwargs["messages"]
    system_msg = next(m["content"] for m in messages if m["role"] == "system")

    assert "RELEVANT REFERENCE SQL PATTERNS (RETRIEVED VIA RAG):" in system_msg
    assert "List students who scored more than 80 marks in any exam" in system_msg
    assert "SELECT * FROM marks WHERE score > 80;" in system_msg


def test_rag_failures_do_not_prevent_sql_generation():
    """Verify that if RAG retrieval fails or raises an error, SQL generation continues safely."""
    with patch.object(RAGService, "retrieve_relevant_examples", side_effect=RuntimeError("Simulated RAG failure")):
        res = SQLGeneratorService.generate("Show all customers")
        assert isinstance(res, GenerateSQLResponse)
        assert res.sql != ""
        assert "SELECT" in res.sql.upper()
        assert res.is_safe is True
        assert res.rag_applied is False
        assert res.retrieved_examples is None


def test_format_examples_for_prompt():
    """Verify prompt formatting of retrieved examples includes guidance notes and query details."""
    examples = [
        {
            "id": "ex_01",
            "question": "Show all students with high GPA",
            "sql_query": "SELECT id, name, gpa FROM students WHERE gpa >= 3.8;",
            "category": "where_comparison",
            "similarity": 12.34
        }
    ]
    formatted = RAGService.format_examples_for_prompt(examples)
    assert "RELEVANT REFERENCE SQL PATTERNS" in formatted
    assert "Show all students with high GPA" in formatted
    assert "SELECT id, name, gpa FROM students WHERE gpa >= 3.8;" in formatted
    assert "12.34" in formatted


def test_sql_generator_integration_with_rag():
    """Verify SQLGeneratorService includes RAG metadata in response without breaking generation."""
    res = SQLGeneratorService.generate("Show students who scored more than 80 marks")
    assert isinstance(res, GenerateSQLResponse)
    assert res.sql != ""
    assert "SELECT" in res.sql.upper()
    assert res.is_safe is True
    assert hasattr(res, "rag_applied")
    assert hasattr(res, "retrieved_examples")
    if res.rag_applied:
        assert isinstance(res.retrieved_examples, list)
        assert len(res.retrieved_examples) > 0
        top = res.retrieved_examples[0]
        assert "id" in top
        assert "sql_query" in top
        assert "similarity" in top
