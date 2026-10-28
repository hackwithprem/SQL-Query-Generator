import pytest
from app.services.sql_validator import SQLValidator, SQLValidationError

def test_valid_select_query():
    sql = "SELECT id, first_name, last_name FROM students WHERE age > 20"
    validated = SQLValidator.validate(sql)
    assert "SELECT" in validated
    assert "students" in validated

def test_valid_cte_query():
    sql = "WITH top_students AS (SELECT id, gpa FROM students WHERE gpa > 3.5) SELECT * FROM top_students"
    validated = SQLValidator.validate(sql)
    assert "WITH" in validated
    assert "SELECT" in validated

def test_reject_insert():
    sql = "INSERT INTO students (first_name, last_name, email, age, enrollment_year) VALUES ('Hacker', 'X', 'h@x.com', 25, 2024)"
    with pytest.raises(SQLValidationError) as exc:
        SQLValidator.validate(sql)
    assert "Only read-only" in str(exc.value) or "Prohibited" in str(exc.value)

def test_reject_drop_table():
    sql = "DROP TABLE students"
    with pytest.raises(SQLValidationError) as exc:
        SQLValidator.validate(sql)
    assert "Only read-only" in str(exc.value) or "Prohibited" in str(exc.value)

def test_reject_delete():
    sql = "DELETE FROM students WHERE id = 1"
    with pytest.raises(SQLValidationError) as exc:
        SQLValidator.validate(sql)
    assert "Only read-only" in str(exc.value) or "Prohibited" in str(exc.value)

def test_reject_update():
    sql = "UPDATE students SET gpa = 4.0 WHERE id = 1"
    with pytest.raises(SQLValidationError) as exc:
        SQLValidator.validate(sql)
    assert "Only read-only" in str(exc.value) or "Prohibited" in str(exc.value)

def test_reject_truncate():
    sql = "TRUNCATE TABLE students"
    with pytest.raises(SQLValidationError) as exc:
        SQLValidator.validate(sql)

def test_reject_multiple_statements():
    sql = "SELECT * FROM students; DROP TABLE students;"
    with pytest.raises(SQLValidationError) as exc:
        SQLValidator.validate(sql)
    assert "multiple" in str(exc.value).lower()

def test_reject_empty_query():
    with pytest.raises(SQLValidationError):
        SQLValidator.validate("")

def test_reject_select_into():
    sql = "SELECT * INTO backup_students FROM students"
    with pytest.raises(SQLValidationError) as exc:
        SQLValidator.validate(sql)
    assert "prohibited" in str(exc.value).lower()
