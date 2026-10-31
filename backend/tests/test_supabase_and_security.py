import io
import json
import pytest
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.database.models import User, UploadedDataset
from app.services.dataset_service import DatasetService
from app.services.supabase_service import SupabaseService

client = TestClient(app)

def get_auth_token_and_user(email: str, name: str, password: str = "Password123!"):
    # Attempt login first if user already registered in Supabase
    res_login = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    if res_login.status_code == 200 and "access_token" in res_login.json():
        data = res_login.json()
        return data["access_token"], data["user"]

    # Otherwise sign up
    res = client.post("/api/auth/signup", json={
        "full_name": name,
        "email": email,
        "password": password
    })
    if res.status_code == 200 and "access_token" in res.json():
        data = res.json()
        return data["access_token"], data["user"]

    # Or retry login
    res_login2 = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert res_login2.status_code == 200
    data = res_login2.json()
    return data["access_token"], data["user"]

def test_user_cross_isolation():
    token_a, user_a = get_auth_token_and_user("alice_iso@example.com", "Alice Iso")
    token_b, user_b = get_auth_token_and_user("bob_iso@example.com", "Bob Iso")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Alice uploads a CSV
    csv_data = b"product_id,product_name,price\n1,Widget,25.50\n2,Gadget,49.99\n"
    files = {"file": ("products.csv", io.BytesIO(csv_data), "text/csv")}
    upload_res = client.post("/api/data/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 200
    dataset_a_id = upload_res.json()["id"]

    # Bob lists files - Alice's dataset should NOT be in Bob's list
    bob_files_res = client.get("/api/data/files", headers=headers_b)
    assert bob_files_res.status_code == 200
    bob_file_ids = [f["id"] for f in bob_files_res.json()]
    assert dataset_a_id not in bob_file_ids

    # Bob tries to preview Alice's dataset - must be 404 / access denied
    bob_prev_res = client.get(f"/api/data/files/{dataset_a_id}/preview", headers=headers_b)
    assert bob_prev_res.status_code == 404

    # Bob tries to delete Alice's dataset - must be 404 / access denied
    bob_del_res = client.delete(f"/api/data/files/{dataset_a_id}", headers=headers_b)
    assert bob_del_res.status_code == 404

    # Bob tries to generate SQL using Alice's dataset ID - must be 404
    bob_gen_res = client.post("/api/generate-sql", json={
        "question": "Show all products",
        "dataset_id": dataset_a_id
    }, headers=headers_b)
    assert bob_gen_res.status_code == 404

    # Alice renames her dataset
    rename_res = client.patch(f"/api/data/files/{dataset_a_id}/rename", json={"new_name": "inventory_products.csv"}, headers=headers_a)
    assert rename_res.status_code == 200
    assert rename_res.json()["new_name"] == "inventory_products.csv"

    # Alice can delete her own dataset
    alice_del_res = client.delete(f"/api/data/files/{dataset_a_id}", headers=headers_a)
    assert alice_del_res.status_code == 200

def test_excel_upload_with_worksheet_selection():
    token, user = get_auth_token_and_user("excel_user@example.com", "Excel User")
    headers = {"Authorization": f"Bearer {token}"}

    # Create multi-sheet Excel file in memory using openpyxl / pandas
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_sheet1 = pd.DataFrame({"dept": ["HR", "IT"], "headcount": [5, 20]})
        df_sheet2 = pd.DataFrame({"region": ["North", "South"], "revenue": [100000, 150000]})
        df_sheet1.to_excel(writer, sheet_name="Departments", index=False)
        df_sheet2.to_excel(writer, sheet_name="RegionalSales", index=False)
    
    excel_buffer.seek(0)
    files = {"file": ("report.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    data = {"sheet_name": "RegionalSales"}

    upload_res = client.post("/api/data/upload", headers=headers, files=files, data=data)
    assert upload_res.status_code == 200
    dataset = upload_res.json()
    assert dataset["sheet_name"] == "RegionalSales"
    assert dataset["row_count"] == 2
    col_names = [c["name"] for c in dataset["columns"]]
    assert "region" in col_names
    assert "revenue" in col_names

    # Clean up
    client.delete(f"/api/data/files/{dataset['id']}", headers=headers)

def test_profile_update_endpoint():
    token, user = get_auth_token_and_user("profile_user@example.com", "Initial Name")
    headers = {"Authorization": f"Bearer {token}"}

    # Update profile
    res = client.put("/api/auth/profile", json={"full_name": "Updated Name"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["full_name"] == "Updated Name"

    # Verify via /api/auth/me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Updated Name"

def test_unauthenticated_protected_endpoints_rejected():
    # Fresh unauthenticated client without cookie session
    unauth_client = TestClient(app)

    # Attempt to upload without auth
    files = {"file": ("test.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
    upload_res = unauth_client.post("/api/data/upload", files=files)
    assert upload_res.status_code == 401

    # Attempt to access /api/auth/me without auth
    me_res = unauth_client.get("/api/auth/me")
    assert me_res.status_code == 401

    # Attempt to update profile without auth
    prof_res = unauth_client.put("/api/auth/profile", json={"full_name": "Hacker"})
    assert prof_res.status_code == 401

def test_supabase_service_graceful_handling():
    # When Supabase is not configured, is_configured should safely return False
    assert isinstance(SupabaseService.is_configured(), bool)
    client_inst = SupabaseService.get_client()
    # verify_token with invalid token returns None without raising unhandled exception
    assert SupabaseService.verify_token("invalid_token") is None
    # download or upload gracefully handles unconfigured state
    assert SupabaseService.download_private_file("dummy/path") is None
