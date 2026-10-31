import pytest
from app.core.config import settings
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.knowledge_base import SQL_EXAMPLES
from app.services.rag.rag_service import RAGService
from app.services.sql_generator import SQLGeneratorService
from app.schemas.responses import GenerateSQLResponse

def test_knowledge_base_size_and_structure():
    """Verify the initial knowledge base contains at least 30-50 verified examples with all required keys."""
    assert len(SQL_EXAMPLES) >= 30, f"Expected at least 30 examples, found {len(SQL_EXAMPLES)}"
    for ex in SQL_EXAMPLES:
        assert "id" in ex
        assert "question" in ex and len(ex["question"]) > 5
        assert "sql_query" in ex and "SELECT" in ex["sql_query"].upper()
        assert "category" in ex

def test_embedding_generation_dimension():
    """Verify sentence-transformers/all-MiniLM-L6-v2 produces 384-dimensional dense vectors."""
    text = "Show all employees with salary greater than 50000"
    embedding = EmbeddingService.get_embedding(text)
    assert embedding is not None
    assert len(embedding) == 384
    assert isinstance(embedding[0], float)

def test_batch_embeddings():
    """Verify batch embedding generation for multiple questions."""
    texts = [
        "List all customers from California",
        "Calculate total revenue from completed orders"
    ]
    batch = EmbeddingService.get_batch_embeddings(texts)
    assert len(batch) == 2
    for emb in batch:
        assert emb is not None
        assert len(emb) == 384

def test_rag_similarity_retrieval_relevance():
    """Verify that a question retrieves semantically relevant SQL query patterns."""
    question = "Find the average salary of employees in each department"
    results = RAGService.retrieve_relevant_examples(question, top_k=3, threshold=0.3)
    assert len(results) > 0
    assert len(results) <= 3
    
    # Check structure
    top_match = results[0]
    assert "question" in top_match
    assert "sql_query" in top_match
    assert "similarity" in top_match
    assert top_match["similarity"] >= 0.3
    
    # Verify similarity is in valid cosine range
    assert 0.0 <= top_match["similarity"] <= 1.0

def test_rag_threshold_filtering():
    """Verify that very high threshold excludes unrelated queries."""
    question = "Quantum physics entanglement observation data"
    # An unrelated query with high threshold should yield 0 results
    results = RAGService.retrieve_relevant_examples(question, top_k=3, threshold=0.85)
    assert len(results) == 0

def test_rag_disabled_fallback():
    """Verify that when RAG_ENABLED is false, retrieve_relevant_examples returns empty list without error."""
    original_setting = settings.RAG_ENABLED
    try:
        settings.RAG_ENABLED = False
        results = RAGService.retrieve_relevant_examples("List all customers")
        assert results == []
    finally:
        settings.RAG_ENABLED = original_setting

def test_format_examples_for_prompt():
    """Verify prompt formatting of retrieved examples includes guidance notes and query details."""
    examples = [
        {
            "id": "ex_01",
            "question": "Show all students with high GPA",
            "sql_query": "SELECT id, name, gpa FROM students WHERE gpa >= 3.8;",
            "category": "where_comparison",
            "similarity": 0.88
        }
    ]
    formatted = RAGService.format_examples_for_prompt(examples)
    assert "RELEVANT REFERENCE SQL PATTERNS" in formatted
    assert "Show all students with high GPA" in formatted
    assert "SELECT id, name, gpa FROM students WHERE gpa >= 3.8;" in formatted
    assert "0.88" in formatted

def test_sql_generator_integration_with_rag():
    """Verify SQLGeneratorService includes RAG metadata in response without breaking generation."""
    res = SQLGeneratorService.generate("Show average student marks by course")
    assert isinstance(res, GenerateSQLResponse)
    assert res.sql != ""
    assert "SELECT" in res.sql.upper()
    assert res.is_safe is True
    # RAG metadata fields should be present
    assert hasattr(res, "rag_applied")
    assert hasattr(res, "retrieved_examples")
    if res.rag_applied:
        assert isinstance(res.retrieved_examples, list)
        assert len(res.retrieved_examples) > 0

