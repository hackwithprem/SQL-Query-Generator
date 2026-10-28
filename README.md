# SQL Query Generator from Plain English

An AI-powered full-stack web application that translates natural language questions into safe, optimized, read-only SQL queries, executes them against a relational database, provides plain-English query explanations, and auto-corrects failing queries.

---

## Key Features

- **Natural Language to SQL**: Converts questions like *"Show all students who scored more than 80 marks"* into valid, schema-aware SQL.
- **Strict Read-Only Security Guardrails**: Enforces single-statement, read-only `SELECT` queries with AST parsing. Blocks all destructive statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `SELECT INTO`, etc.) and multi-statement injection attempts.
- **Editable SQL Editor**: Review, copy, format, and freely edit the SQL before execution. Generation and execution are decoupled.
- **Interactive Results Table**: Displays returned records with column formatting, execution time in milliseconds, row counts, and CSV export.
- **Plain English SQL Explanation**: Explains what the generated query does, including tables queried, joins used, filters applied, and aggregations.
- **AI Error Auto-Correction**: When a query fails, the AI analyzes the error, repairs the SQL according to the schema, and provides a fix for one-click application into the editor.
- **Live Database Schema Explorer**: Inspect connected tables, column definitions, data types, primary keys, and foreign-key relationships.
- **Query History**: Tracks past queries, execution statuses, and timestamps, allowing one-click reloading of previous queries.
- **Dark & Light Mode**: Modern developer-tool aesthetic with persistent theme toggle.
- **Multi-Provider AI Architecture**: Modular provider layer supporting **Groq** (`llama-3.3-70b-versatile`), **Gemini** (`gemini-1.5-flash`), and an **Intelligent Offline Fallback** that functions without any external API keys.

---

## Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons, Axios |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0 |
| **SQL Parser & Security** | `sqlparse` dialect-aware AST validation |
| **Database** | SQLite 3 (`data/sample.db`) with academic schema and realistic seed data |
| **AI Providers** | Groq (`llama-3.3-70b-versatile`), Google Gemini, and Local Fallback |

---

## Project Structure

```
SQL_Query_Generator/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST API endpoints (generate, execute, explain, correct, schema, history, health)
│   │   ├── core/                # Configuration and environment settings
│   │   ├── database/            # Connection, models, and seed script
│   │   ├── schemas/             # Pydantic request and response schemas
│   │   ├── services/            # SQL generator, validator, executor, explainer, corrector, history
│   │   └── main.py              # FastAPI application entry point
│   ├── tests/                   # Pytest automated test suite (validator, executor, API endpoints)
│   ├── requirements.txt         # Backend Python dependencies
│   └── .env.example             # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios HTTP client
│   │   ├── components/          # Sidebar, Header, PromptInput, SqlEditor, ResultsTable, Modals
│   │   ├── App.jsx              # Application state and coordination
│   │   └── main.jsx             # React entry point
│   ├── package.json             # Frontend Node dependencies
│   └── vite.config.js           # Vite dev configuration and API proxy
├── data/
│   └── sample.db                # SQLite database with academic seed records
├── docs/
│   └── architecture.md          # Architecture and security specifications
├── .gitignore
└── README.md
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

---

### 2. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - On Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - On Linux/macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional)**:
   ```bash
   cp .env.example .env
   ```
   *Note: If no API key is provided, the application automatically uses the built-in Local Pattern Engine so you can immediately explore and test the entire application offline!*

   To use Groq with LLaMA 3.3:
   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_your_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

5. **Seed the demonstration database**:
   ```bash
   python -m app.database.seed
   ```

6. **Start the FastAPI backend server**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be available at `http://127.0.0.1:8000` (Interactive Swagger docs at `http://127.0.0.1:8000/docs`).

---

### 3. Frontend Setup

1. **In a new terminal, navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   Open your browser at `http://127.0.0.1:5173`.

---

## Running Automated Tests

Run the full backend test suite covering SQL validation, safe execution, destructive query rejection, and all API routes:

```powershell
cd backend
.\.venv\Scripts\pytest -v tests
```

Expected output:
```
tests/test_api.py::test_health_endpoint PASSED
tests/test_api.py::test_schema_endpoint PASSED
tests/test_api.py::test_generate_sql_endpoint PASSED
tests/test_api.py::test_execute_sql_endpoint PASSED
tests/test_api.py::test_execute_sql_endpoint_rejects_delete PASSED
tests/test_api.py::test_explain_sql_endpoint PASSED
tests/test_api.py::test_correct_sql_endpoint PASSED
tests/test_api.py::test_history_endpoints PASSED
tests/test_executor.py::test_execute_simple_select PASSED
tests/test_executor.py::test_execute_join_query PASSED
tests/test_executor.py::test_execute_empty_result PASSED
tests/test_executor.py::test_execute_blocks_destructive_query PASSED
tests/test_executor.py::test_execute_invalid_syntax PASSED
tests/test_validator.py::test_valid_select_query PASSED
tests/test_validator.py::test_valid_cte_query PASSED
tests/test_validator.py::test_reject_insert PASSED
tests/test_validator.py::test_reject_drop_table PASSED
tests/test_validator.py::test_reject_delete PASSED
tests/test_validator.py::test_reject_update PASSED
tests/test_validator.py::test_reject_truncate PASSED
tests/test_validator.py::test_reject_multiple_statements PASSED
tests/test_validator.py::test_reject_empty_query PASSED
tests/test_validator.py::test_reject_select_into PASSED
======================== 23 passed in 1.00s ========================
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status of backend, database, and AI provider |
| `GET` | `/api/schema` | Introspected database tables, columns, data types, and foreign keys |
| `POST` | `/api/generate-sql` | Translates natural language question into validated SQL |
| `POST` | `/api/execute-sql` | Safely validates and executes a read-only query against the database |
| `POST` | `/api/explain-sql` | Produces a plain-English explanation and breakdown of an SQL query |
| `POST` | `/api/correct-sql` | Uses schema and database error context to repair failing SQL |
| `GET` | `/api/history` | Fetches recent query history and execution results |
| `POST` | `/api/history/clear` | Clears recent query history |

---

## Sample Questions to Try

1. *"Show all students who scored more than 80 marks."*
2. *"Find the top 5 students by GPA."*
3. *"Show the average marks for each course."*
4. *"Count the total number of students."*
5. *"List courses with no enrolled students."*
6. *"Find students enrolled in more than one course."*
7. *"Show all courses in the Computer Science department."*
8. *"Show highest scoring student in any exam."*

---

## License

MIT License. Designed for education, development, and productivity.
