import pytest
from app.services.sql_executor import SQLExecutor, SQLExecutionError
from app.services.sql_validator import SQLValidationError
from app.database.seed import seed_database

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()

def test_execute_simple_select():
    result = SQLExecutor.execute("SELECT id, first_name, email FROM students LIMIT 5")
    assert result.row_count > 0
    assert "first_name" in result.columns
    assert len(result.rows) <= 5
    assert result.duration_ms >= 0

def test_execute_join_query():
    sql = """
    SELECT s.first_name, s.last_name, d.name AS department_name
    FROM students s
    JOIN departments d ON s.department_id = d.id
    LIMIT 3
    """
    result = SQLExecutor.execute(sql)
    assert result.row_count > 0
    assert "department_name" in result.columns

def test_execute_empty_result():
    sql = "SELECT * FROM students WHERE age > 100"
    result = SQLExecutor.execute(sql)
    assert result.row_count == 0
    assert len(result.rows) == 0

def test_execute_blocks_destructive_query():
    sql = "DROP TABLE students"
    with pytest.raises(SQLValidationError):
        SQLExecutor.execute(sql)

def test_execute_invalid_syntax():
    sql = "SELECT FROM students WHERE"
    with pytest.raises((SQLExecutionError, SQLValidationError)):
        SQLExecutor.execute(sql)
