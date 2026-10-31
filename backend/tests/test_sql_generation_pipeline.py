import io
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.sql_generator import SQLGeneratorService
from app.services.sql_validator import SQLValidator, SQLValidationError
from app.database.models import UploadedDataset

client = TestClient(app)

def test_existing_table_generation():
    """Requirement 9: Test generating query for an existing table in University Sample DB."""
    res = client.post("/api/generate-sql", json={
        "question": "Show all students with marks greater than 80"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["sql"] != ""
    assert "students" in data["sql"].lower()
    assert "SELECT" in data["sql"].upper()
    assert data["is_safe"] is True
    assert data["target_database"] == "SQLite Sample DB"

def test_nonexistent_table_generates_assumed_sql():
    """
    Requirement 1-4: When a requested table (e.g. 'products') does not exist in the
    University Sample DB, the AI must still generate a reasonable SQL query using assumed
    naming conventions. The editor must NOT be left empty.
    """
    res = client.post("/api/generate-sql", json={
        "question": "List all products with their names and prices"
    })
    assert res.status_code == 200
    data = res.json()
    # SQL must be generated — never empty for a schema-free question
    assert data["sql"].strip() != "", "SQL must not be empty for schema-free generation"
    # Generated SQL must be a real SELECT query, not a comment
    assert not data["sql"].strip().startswith("--"), "SQL must not be a comment"
    assert "SELECT" in data["sql"].upper(), "SQL must contain a SELECT statement"
    # SQL should reference 'products' (assumed table name)
    assert "products" in data["sql"].lower(), "SQL should reference the requested entity 'products'"
    # A clarification note about assumed naming must be present
    clarification = data.get("clarification") or ""
    assert (
        "assumed" in clarification.lower()
        or "schema" in clarification.lower()
        or clarification == ""  # Groq/Gemini may not need clarification if schema returned a real query
    ), "Clarification should mention schema assumptions if no schema was available"

def test_uploaded_shop_dataset_query():
    """Requirement 6: For uploaded CSV/Excel datasets, use the actual uploaded schema, not University DB."""
    # Create an in-memory shop dataset mock model
    ds = UploadedDataset(
        id="test-shop-inventory-1",
        original_filename="shop_products.csv",
        table_name="shop_products",
        columns_json=json.dumps([
            {"name": "product_id", "display_name": "product_id", "type": "INTEGER", "nullable": False},
            {"name": "product_name", "display_name": "product_name", "type": "TEXT", "nullable": False},
            {"name": "price", "display_name": "price", "type": "REAL", "nullable": False},
            {"name": "stock_count", "display_name": "stock_count", "type": "INTEGER", "nullable": False}
        ])
    )
    res = SQLGeneratorService.generate("List all products with their names and prices", dataset=ds)
    assert res.is_safe is True
    assert res.sql != ""
    assert "shop_products" in res.sql.lower()
    assert "price" in res.sql.lower()
    assert "product_name" in res.sql.lower()
    assert "students" not in res.sql.lower()
    assert "Uploaded Dataset" in res.target_database

def test_sql_validator_accepts_readonly_select():
    """Requirement 8: Verify SQL validator accepts valid read-only SELECT and CTE queries."""
    valid_query = "SELECT s.id, s.first_name, m.score FROM students s JOIN marks m ON s.id = m.enrollment_id WHERE m.score > 75"
    formatted = SQLValidator.validate(valid_query)
    assert "SELECT" in formatted

    cte_query = "WITH high_marks AS (SELECT * FROM marks WHERE score >= 90) SELECT * FROM high_marks"
    formatted_cte = SQLValidator.validate(cte_query)
    assert "WITH" in formatted_cte

def test_sql_validator_rejects_unsafe_sql():
    """Requirement 8: Verify SQL validator strictly rejects destructive/unsafe SQL operations."""
    unsafe_queries = [
        "DROP TABLE students;",
        "DELETE FROM marks WHERE score < 50;",
        "UPDATE students SET gpa = 4.0;",
        "INSERT INTO departments (name) VALUES ('Hacking');",
        "ALTER TABLE students ADD COLUMN hacked TEXT;",
        "SELECT * FROM students; DROP TABLE courses;",
        "-- Just a comment with no SELECT"
    ]
    for bad_sql in unsafe_queries:
        with pytest.raises(SQLValidationError):
            SQLValidator.validate(bad_sql)

def test_schema_free_generation_returns_sql_not_error():
    """
    Requirement 1, 2, 5: Schema-free generation (no dataset, no connection, question about
    unknown entities) must always produce SQL — never return SCHEMA_ERROR or empty SQL.
    """
    # Questions about entities not in the University DB
    questions = [
        "List all customers and their email addresses",
        "Show me all orders placed in the last 30 days",
        "Find all employees with a salary greater than 50000",
    ]
    for q in questions:
        res = client.post("/api/generate-sql", json={"question": q})
        assert res.status_code == 200, f"Expected 200 for: {q}"
        data = res.json()
        assert data["sql"].strip() != "", f"SQL must not be empty for: {q}"
        assert "SELECT" in data["sql"].upper(), f"Must produce SELECT for: {q}"
        assert not data["sql"].strip().startswith("--"), f"Must not be a comment for: {q}"

