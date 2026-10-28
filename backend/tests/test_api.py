from fastapi.testclient import TestClient
from app.main import app
from app.database.seed import seed_database

client = TestClient(app)

def setup_module():
    seed_database()

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert "ai_provider" in data

def test_schema_endpoint():
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["dialect"] == "sqlite"
    tables = [t["table_name"] for t in data["tables"]]
    assert "students" in tables
    assert "courses" in tables
    assert "departments" in tables

def test_generate_sql_endpoint():
    payload = {"question": "Show all students with marks greater than 80"}
    response = client.post("/api/generate-sql", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "SELECT" in data["sql"].upper()
    assert data["is_safe"] is True

def test_execute_sql_endpoint():
    payload = {"sql": "SELECT id, first_name, gpa FROM students LIMIT 3"}
    response = client.post("/api/execute-sql", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 3
    assert len(data["columns"]) == 3

def test_execute_sql_endpoint_rejects_delete():
    payload = {"sql": "DELETE FROM students WHERE id = 1"}
    response = client.post("/api/execute-sql", json=payload)
    assert response.status_code == 400
    assert "Violation" in response.json()["detail"] or "read-only" in response.json()["detail"]

def test_explain_sql_endpoint():
    payload = {
        "sql": "SELECT name, marks FROM students WHERE marks > 80",
        "question": "Show all students scoring more than 80"
    }
    response = client.post("/api/explain-sql", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert len(data["explanation"]) > 10

def test_correct_sql_endpoint():
    payload = {
        "original_question": "Show student names",
        "failed_sql": "SELECT name FROM students",
        "error_message": "no such column: name"
    }
    response = client.post("/api/correct-sql", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "corrected_sql" in data
    assert "explanation_of_fix" in data

def test_history_endpoints():
    # Fetch history
    res = client.get("/api/history")
    assert res.status_code == 200
    history_items = res.json()
    assert isinstance(history_items, list)

    # Clear history
    clear_res = client.post("/api/history/clear")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "success"
