# API Contracts & Integration Guide

**Document Version**: 1.0.0  
**Backend Framework**: FastAPI (Python 3.10+)  
**Target Consumer**: Pam (Frontend Development Agent)  
**Base URL**: `http://localhost:8000` (or relative `/api` via Vite proxy)  

---

## 1. Overview & Architectural Principles

1. **Authentication State**:
   - Authentication is performed via `POST /api/auth/signup` or `POST /api/auth/login`.
   - On success, the backend returns `{ "access_token": "<jwt>", "token_type": "bearer", "user": { ... } }` and also sets an HTTP-only `access_token` session cookie.
   - For all authenticated endpoints, the frontend MUST send the JWT token in the `Authorization` header:  
     `Authorization: Bearer <access_token>`
   - The public landing page allows visitors to type natural-language questions **without logging in**. When the user clicks **Generate SQL**, open the Auth Modal. **Preserve the entered question** and restore it once sign-in/sign-up completes.

2. **Decoupled SQL Generation & Execution**:
   - The backend strictly separates SQL generation (`POST /api/generate-sql`) from execution (`POST /api/execute-sql`).
   - The UI **must never automatically execute** generated SQL. The user must review, optionally edit, and explicitly trigger execution.

3. **Error Response Format**:
   - Standard FastAPI error envelope:
     ```json
     {
       "detail": "Error description or validation message"
     }
     ```
   - Common status codes:
     - `400 Bad Request`: Validation failure, unsafe SQL statement, or file parsing error.
     - `401 Unauthorized`: Missing, expired, or invalid authentication token.
     - `404 Not Found`: Dataset, file, or resource not found.
     - `500 Internal Server Error`: Server or unhandled execution failure.

---

## 2. Authentication Endpoints (`/api/auth`)

### 2.1 Sign Up
- **Method**: `POST`
- **Path**: `/api/auth/signup`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "full_name": "Alex Morgan",
    "email": "alex@example.com",
    "password": "Password123!"
  }
  ```
  *Requirements*: Valid email format; password minimum 8 characters.
- **Success Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "full_name": "Alex Morgan",
      "email": "alex@example.com",
      "created_at": "2026-10-29T11:00:00Z"
    }
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: `{ "detail": "An account with this email address already exists." }`

---

### 2.2 Sign In (Login)
- **Method**: `POST`
- **Path**: `/api/auth/login`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "email": "alex@example.com",
    "password": "Password123!"
  }
  ```
- **Success Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "full_name": "Alex Morgan",
      "email": "alex@example.com",
      "created_at": "2026-10-29T11:00:00Z"
    }
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: `{ "detail": "Invalid email or password." }`

---

### 2.3 Get Current User Profile
- **Method**: `GET`
- **Path**: `/api/auth/me`
- **Auth Required**: Yes (`Authorization: Bearer <token>`)
- **Success Response** (`200 OK`):
  ```json
  {
    "id": 1,
    "full_name": "Alex Morgan",
    "email": "alex@example.com",
    "created_at": "2026-10-29T11:00:00Z"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: `{ "detail": "Authentication required. Please sign in." }`

---

### 2.4 Sign Out (Logout)
- **Method**: `POST`
- **Path**: `/api/auth/logout`
- **Auth Required**: No
- **Success Response** (`200 OK`):
  ```json
  {
    "message": "Signed out successfully"
  }
  ```

---

## 3. Query Workspace Endpoints

### 3.1 Generate SQL from Natural Language
- **Method**: `POST`
- **Path**: `/api/generate-sql`
- **Auth Required**: Optional (Supports authenticated sessions and guest demos)
- **Request Body**:
  ```json
  {
    "question": "Show top 5 students by GPA in Computer Science",
    "dialect": "sqlite",
    "dataset_id": null
  }
  ```
  *Note*: When querying an uploaded dataset, pass the uploaded dataset's UUID in `dataset_id`.
- **Success Response** (`200 OK`):
  ```json
  {
    "sql": "SELECT s.id, s.first_name, s.last_name, s.gpa FROM students s JOIN departments d ON s.department_id = d.id WHERE d.code = 'CS' ORDER BY s.gpa DESC LIMIT 5;",
    "is_safe": true,
    "explanation": "Translates the user query to select students sorted by GPA restricted to the Computer Science department."
  }
  ```

---

### 3.2 Execute SQL Query
- **Method**: `POST`
- **Path**: `/api/execute-sql`
- **Auth Required**: Optional
- **Request Body**:
  ```json
  {
    "sql": "SELECT id, first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;",
    "limit": 500,
    "dataset_id": null
  }
  ```
  *Note*: Pass `dataset_id` if executing against an uploaded CSV/Excel dataset.
- **Success Response** (`200 OK`):
  ```json
  {
    "columns": ["id", "first_name", "last_name", "gpa"],
    "rows": [
      { "id": 4, "first_name": "Diana", "last_name": "Prince", "gpa": 3.95 },
      { "id": 12, "first_name": "Laura", "last_name": "Croft", "gpa": 3.90 },
      { "id": 1, "first_name": "Alice", "last_name": "Johnson", "gpa": 3.85 },
      { "id": 8, "first_name": "Hannah", "last_name": "Abbott", "gpa": 3.75 },
      { "id": 3, "first_name": "Charlie", "last_name": "Brown", "gpa": 3.65 }
    ],
    "row_count": 5,
    "duration_ms": 1.25,
    "truncated": false,
    "sql": "SELECT id, first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;"
  }
  ```
- **Error Responses**:
  - `400 Bad Request`:
    - Security violation: `{ "detail": "Security/Validation Violation: Only read-only SELECT queries are permitted." }`
    - Execution syntax error: `{ "detail": "near \"FROMM\": syntax error" }`

---

### 3.3 Explain SQL Query
- **Method**: `POST`
- **Path**: `/api/explain-sql`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "sql": "SELECT s.first_name, m.score FROM students s JOIN enrollments e ON s.id = e.student_id JOIN marks m ON e.id = m.enrollment_id WHERE m.score > 80;",
    "question": "Show students with score over 80"
  }
  ```
- **Success Response** (`200 OK`):
  ```json
  {
    "explanation": "This query retrieves data from `students, enrollments, marks`.\n\n• **Tables Accessed**: Reads information from `students`, `enrollments`, `marks`.\n• **Joins**: Connects records across tables using relational foreign keys.\n• **Filtering**: Applies criteria in the WHERE clause (`score > 80`)."
  }
  ```

---

### 3.4 Correct SQL Query
- **Method**: `POST`
- **Path**: `/api/correct-sql`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "original_question": "Show student names",
    "failed_sql": "SELECT name FROM students",
    "error_message": "no such column: name"
  }
  ```
- **Success Response** (`200 OK`):
  ```json
  {
    "corrected_sql": "SELECT first_name, last_name FROM students;",
    "explanation_of_fix": "Replaced invalid column reference `name` with `first_name, last_name`."
  }
  ```

---

## 4. Database Schema Endpoint (`/api/schema`)

### 4.1 Get Schema
- **Method**: `GET`
- **Path**: `/api/schema`
- **Auth Required**: No
- **Success Response** (`200 OK`):
  ```json
  {
    "dialect": "sqlite",
    "tables": [
      {
        "table_name": "departments",
        "columns": [
          { "name": "id", "type": "INTEGER", "nullable": false, "primary_key": true },
          { "name": "name", "type": "VARCHAR(100)", "nullable": false, "primary_key": false },
          { "name": "code", "type": "VARCHAR(10)", "nullable": false, "primary_key": false },
          { "name": "budget", "type": "FLOAT", "nullable": true, "primary_key": false }
        ],
        "foreign_keys": []
      },
      {
        "table_name": "students",
        "columns": [
          { "name": "id", "type": "INTEGER", "nullable": false, "primary_key": true },
          { "name": "first_name", "type": "VARCHAR(50)", "nullable": false, "primary_key": false },
          { "name": "last_name", "type": "VARCHAR(50)", "nullable": false, "primary_key": false },
          { "name": "email", "type": "VARCHAR(100)", "nullable": false, "primary_key": false },
          { "name": "age", "type": "INTEGER", "nullable": false, "primary_key": false },
          { "name": "gender", "type": "VARCHAR(10)", "nullable": true, "primary_key": false },
          { "name": "enrollment_year", "type": "INTEGER", "nullable": false, "primary_key": false },
          { "name": "gpa", "type": "FLOAT", "nullable": true, "primary_key": false },
          { "name": "department_id", "type": "INTEGER", "nullable": true, "primary_key": false }
        ],
        "foreign_keys": [
          { "constrained_columns": ["department_id"], "referred_table": "departments", "referred_columns": ["id"] }
        ]
      }
    ]
  }
  ```

---

## 5. Query History Endpoints (`/api/history`)

### 5.1 Fetch User Query History
- **Method**: `GET`
- **Path**: `/api/history?limit=50`
- **Auth Required**: Optional (filters by current user when authenticated)
- **Success Response** (`200 OK`):
  ```json
  [
    {
      "id": 10,
      "natural_query": "Show top 5 students by GPA",
      "generated_sql": "SELECT id, first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;",
      "executed": 1,
      "status": "executed",
      "execution_time_ms": 1.25,
      "row_count": 5,
      "error_message": null,
      "created_at": "2026-10-29T11:05:00Z"
    }
  ]
  ```

---

### 5.2 Clear User Query History
- **Method**: `POST`
- **Path**: `/api/history/clear`
- **Auth Required**: Optional
- **Success Response** (`200 OK`):
  ```json
  {
    "status": "success",
    "cleared_count": 5
  }
  ```

---

## 6. Upload Data Endpoints (`/api/data`)

### 6.1 Upload CSV or Excel Dataset
- **Method**: `POST`
- **Path**: `/api/data/upload`
- **Auth Required**: Yes (`Authorization: Bearer <token>`)
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `file`: File upload (`.csv`, `.xlsx`, or `.xls`)
  - `sheet_name`: (Optional, string) Target worksheet name for Excel files
- **Success Response** (`200 OK`):
  ```json
  {
    "id": "e429188a-a4ea-42b7-a36c-2f9f8c1f9b5b",
    "original_filename": "employees.csv",
    "file_size_bytes": 1024,
    "file_type": "csv",
    "sheet_name": null,
    "table_name": "employees",
    "row_count": 150,
    "column_count": 4,
    "columns": [
      { "name": "employee_id", "display_name": "employee_id", "type": "INTEGER", "nullable": false },
      { "name": "employee_name", "display_name": "employee_name", "type": "TEXT", "nullable": false },
      { "name": "department", "display_name": "department", "type": "TEXT", "nullable": true },
      { "name": "salary", "display_name": "salary", "type": "REAL", "nullable": false }
    ],
    "status": "ready",
    "created_at": "2026-10-29T11:06:00Z"
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: `{ "detail": "File size exceeds maximum allowed limit of 15MB." }`

---

### 6.2 List User's Uploaded Datasets
- **Method**: `GET`
- **Path**: `/api/data/datasets` *(alias `/api/data/files` is also supported)*
- **Auth Required**: Yes (`Authorization: Bearer <token>`)
- **Success Response** (`200 OK`):
  ```json
  [
    {
      "id": "e429188a-a4ea-42b7-a36c-2f9f8c1f9b5b",
      "original_filename": "employees.csv",
      "file_size_bytes": 1024,
      "file_type": "csv",
      "sheet_name": null,
      "table_name": "employees",
      "row_count": 150,
      "column_count": 4,
      "columns": [...],
      "status": "ready",
      "created_at": "2026-10-29T11:06:00Z"
    }
  ]
  ```

---

### 6.3 Preview Dataset Rows
- **Method**: `GET`
- **Path**: `/api/data/preview/{id}` *(aliases `/api/data/datasets/{id}/preview` and `/api/data/files/{id}/preview` are also supported)*
- **Auth Required**: Yes (`Authorization: Bearer <token>`)
- **Success Response** (`200 OK`):
  ```json
  {
    "dataset": {
      "id": "e429188a-a4ea-42b7-a36c-2f9f8c1f9b5b",
      "original_filename": "employees.csv",
      "table_name": "employees",
      "row_count": 150,
      "column_count": 4,
      "columns": [...]
    },
    "sample_rows": [
      { "employee_id": 101, "employee_name": "John Doe", "department": "Engineering", "salary": 85000 },
      { "employee_id": 102, "employee_name": "Jane Smith", "department": "Design", "salary": 92000 }
    ]
  }
  ```

---

### 6.4 Delete Uploaded Dataset
- **Method**: `DELETE`
- **Path**: `/api/data/datasets/{id}` *(alias `/api/data/files/{id}` is also supported)*
- **Auth Required**: Yes (`Authorization: Bearer <token>`)
- **Success Response** (`200 OK`):
  ```json
  {
    "message": "Dataset deleted successfully",
    "id": "e429188a-a4ea-42b7-a36c-2f9f8c1f9b5b"
  }
  ```

---

## 7. System Health Endpoint (`/api/health`)

- **Method**: `GET`
- **Path**: `/api/health`
- **Auth Required**: No
- **Success Response** (`200 OK`):
  ```json
  {
    "status": "healthy",
    "database": {
      "connected": true,
      "dialect": "sqlite",
      "read_only_enforced": true
    },
    "ai_provider": {
      "provider": "Groq (openai/gpt-oss-120b)",
      "is_configured": true,
      "configured_provider": "groq"
    },
    "version": "1.0.0"
  }
  ```

---

## 8. Frontend Navigation & Sidebar Guidelines

Per project requirements, the authenticated sidebar MUST contain **exactly these six items**:
1. **New Query** (Workspace with NL question input, Generate SQL, SQL Editor, Execute Query, Results Table, Explain, and Correct buttons)
2. **Query History** (List of user's past queries, status, execution duration, and reopen query)
3. **Upload Data** (Upload CSV/Excel, sheet selection, column preview, sample table preview, and ask questions about the uploaded dataset)
4. **Profile** (Display user full name and email)
5. **Logout** (Clear auth state and session cookie)
6. **Light/Dark Mode** (Theme switch persisted in localStorage)

**DO NOT** display API key configuration, database connection managers, AI engine connection settings, or server configuration in the end-user interface.
