import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.models import User, UploadedDataset, DatabaseConnectionModel
from app.database.connection import SessionLocal

client = TestClient(app)

def test_auth_signup_and_login():
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    # 1. Signup new user
    signup_payload = {
        "full_name": "Test User",
        "email": unique_email,
        "password": "Password123!"
    }

    res = client.post("/api/auth/signup", json=signup_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    token = data["access_token"]

    # 2. Duplicate signup should be rejected
    res_dup = client.post("/api/auth/signup", json=signup_payload)
    assert res_dup.status_code == 400

    # 3. Test /api/auth/me with Bearer token
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == unique_email

    # 4. Login with wrong password should fail
    res_bad_pw = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "WrongPassword999!"
    })
    assert res_bad_pw.status_code == 401

    # 5. Login with correct password should succeed
    res_login = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "Password123!"
    })
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()

def test_csv_upload_preview_and_query():
    unique_email = f"csv_user_{uuid.uuid4().hex[:8]}@example.com"
    res_signup = client.post("/api/auth/signup", json={
        "full_name": "CSV User",
        "email": unique_email,
        "password": "Password123!"
    })
    assert res_signup.status_code == 200
    token = res_signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create in-memory CSV
    csv_content = b"employee_id,employee_name,department,salary\n101,John Doe,Engineering,85000\n102,Jane Smith,Design,92000\n103,Sam Wilson,Marketing,64000\n"
    files = {"file": ("employees.csv", io.BytesIO(csv_content), "text/csv")}

    upload_res = client.post("/api/data/upload", headers=headers, files=files)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    dataset_id = upload_data["id"]
    assert upload_data["table_name"] == "employees"
    assert upload_data["row_count"] == 3
    assert upload_data["column_count"] == 4

    # Test preview (both /files/.../preview and /preview/...)
    prev_res = client.get(f"/api/data/files/{dataset_id}/preview", headers=headers)
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert len(prev_data["sample_rows"]) == 3
    assert prev_data["sample_rows"][0]["department"] == "Engineering"

    # Test preview alias /api/data/preview/{id}
    prev_alias = client.get(f"/api/data/preview/{dataset_id}", headers=headers)
    assert prev_alias.status_code == 200

    # Test list (both /files and /datasets)
    list_res = client.get("/api/data/files", headers=headers)
    assert list_res.status_code == 200
    file_ids = [f["id"] for f in list_res.json()]
    assert dataset_id in file_ids

    list_datasets = client.get("/api/data/datasets", headers=headers)
    assert list_datasets.status_code == 200
    assert any(d["id"] == dataset_id for d in list_datasets.json())

    # Test Query generation against uploaded dataset
    gen_res = client.post("/api/generate-sql", json={
        "question": "Show all employees earning more than 70000",
        "dataset_id": dataset_id
    }, headers=headers)
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert "employees" in gen_data["sql"].lower()

    # Test Query execution against uploaded dataset
    exec_res = client.post("/api/execute-sql", json={
        "sql": f"SELECT employee_name, salary FROM {upload_data['table_name']} WHERE salary > 70000",
        "dataset_id": dataset_id
    }, headers=headers)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["row_count"] == 2
    assert "Jane Smith" in [r["employee_name"] for r in exec_data["rows"]]

    # Test Delete dataset
    del_res = client.delete(f"/api/data/files/{dataset_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify deleted
    prev_after_del = client.get(f"/api/data/files/{dataset_id}/preview", headers=headers)
    assert prev_after_del.status_code == 404

def test_database_connection_validation_and_crud():
    unique_email = f"conn_user_{uuid.uuid4().hex[:8]}@example.com"
    res_signup = client.post("/api/auth/signup", json={
        "full_name": "Conn User",
        "email": unique_email,
        "password": "Password123!"
    })
    assert res_signup.status_code == 200
    token = res_signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test connection test failure with invalid host
    test_res = client.post("/api/connections/test", json={
        "provider": "postgresql",
        "name": "Dev Postgres",
        "host": "invalid-host-9999.local",
        "port": 5432,
        "database_name": "app_db",
        "username": "postgres_user",
        "password": "test_password",
        "ssl_enabled": False
    }, headers=headers)
    assert test_res.status_code == 200
    assert test_res.json()["success"] is False

    # Test saving connection
    create_res = client.post("/api/connections", json={
        "provider": "postgresql",
        "name": "Production Analytics DB",
        "host": "db.cloud.example.com",
        "port": 5432,
        "database_name": "analytics",
        "username": "readonly_user",
        "password": "SuperSecretPassword123!",
        "ssl_enabled": True
    }, headers=headers)
    assert create_res.status_code == 200
    conn_data = create_res.json()
    conn_id = conn_data["id"]
    assert conn_data["name"] == "Production Analytics DB"
    assert "password" not in conn_data # Password is NOT exposed in response!

    # Test list connections
    list_res = client.get("/api/connections", headers=headers)
    assert list_res.status_code == 200
    assert any(c["id"] == conn_id for c in list_res.json())

    # Test delete connection
    del_res = client.delete(f"/api/connections/{conn_id}", headers=headers)
    assert del_res.status_code == 200
