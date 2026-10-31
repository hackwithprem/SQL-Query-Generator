# SQL Query Generator from Plain English

An AI-powered full-stack web application that translates natural language questions into safe, optimized, read-only SQL queries, executes them against relational databases or uploaded datasets, provides plain-English query explanations, auto-corrects failing queries, and persists user queries and files securely via Supabase.

---

## Key Features

- **Public Landing Page & Authentication Gate**: Visitors can explore the interface and draft natural language questions immediately without an upfront login wall. When clicking **Generate SQL**, unauthenticated visitors are gracefully prompted with a Sign In / Sign Up modal while their typed question is preserved intact.
- **Natural Language to SQL**: Converts questions like *"Show all students who scored more than 80 marks"* or *"Find employees earning more than 70000"* into valid, schema-aware SQL.
- **Strict Read-Only Security Guardrails**: Enforces single-statement, read-only `SELECT` queries with AST parsing. Blocks all destructive statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `SELECT INTO`, etc.) and multi-statement injection attempts.
- **User-Uploaded Datasets (CSV & Excel)**: Drag-and-drop or browse CSV and Excel (`.xlsx`, `.xls`) spreadsheets. Automatically inspects worksheets, normalizes column names, infers data types, and generates an isolated queryable database for each user.
- **Durable Private Storage**: Uploaded files are stored in private Supabase Storage (`private-datasets` bucket), ensuring datasets persist across ephemeral container restarts (Google Cloud Run ready).
- **Exact 6-Item Authenticated Sidebar**:
  1. **New Query**: Opens a fresh query workspace.
  2. **Query History**: Shows the authenticated user's private query history with one-click reloading into the editor.
  3. **Upload Data**: Upload, preview, query, rename, and delete CSV/Excel files.
  4. **Profile**: Displays user details and provides display name updates.
  5. **Logout**: Safely destroys sessions and clears cached client data.
  6. **Light/Dark Mode**: Seamless persistent theme toggle throughout the interface.
- **AI Error Auto-Correction**: When a query fails, the AI analyzes the database error against the schema and generates a corrected query with an explanation.
- **Plain English SQL Explanation**: Explains what the generated query does, including tables queried, joins used, filters applied, and aggregations.
- **Multi-Provider AI Architecture**: Modular provider layer supporting **Groq** (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b`), **Gemini** (`gemini-1.5-flash`), and an **Intelligent Offline Fallback** that functions without external API keys.

---

## Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | React 18, Vite 5, Tailwind CSS 3, Lucide React, Axios |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0 |
| **SQL Parser & Security** | `sqlparse` dialect-aware AST validation |
| **File Processing** | `pandas`, `openpyxl`, isolated SQLite per-user storage |
| **Auth & Cloud Persistence** | **Supabase Auth**, **Supabase PostgreSQL** (RLS), **Supabase Storage** (`private-datasets`) |
| **AI Providers** | Groq, Google Gemini, and Local Fallback Engine |

---

## Repository Structure

```
SQL_Query_Generator/
├── backend/
│   ├── app/
│   │   ├── api/                 # REST API routes (auth, data, generate, execute, explain, correct, history, health)
│   │   ├── core/                # App configuration, security helpers
│   │   ├── database/            # SQLAlchemy models, SQLite seeds, supabase_schema.sql
│   │   ├── schemas/             # Pydantic request & response models
│   │   ├── services/            # Supabase service, LLM providers, SQL executor, validator, dataset service
│   │   └── main.py              # FastAPI application entry point
│   ├── tests/                   # Automated pytest suite (unit, integration, security isolation)
│   ├── requirements.txt         # Backend Python dependencies
│   └── .env.example             # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios client
│   │   ├── components/          # Sidebar, Header, PromptInput, SqlEditor, ResultsTable, Modals
│   │   ├── App.jsx              # Main application coordination and auth gate
│   │   └── main.jsx             # React entry point
│   ├── package.json             # Frontend Node dependencies
│   ├── tailwind.config.js       # Tailwind configuration with light/dark themes
│   └── vite.config.js           # Vite development server and API proxy
├── data/
│   └── sample.db                # SQLite academic database with realistic seed records
├── docs/
│   ├── architecture.md          # Architecture and security specifications
│   └── api_contracts.md         # API contract documentation
├── .gitignore
└── README.md
```

---

## Local Development Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

---

### 1. Backend Setup

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
   - On macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file inside `backend/` (or copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Configure your keys:
   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=llama-3.3-70b-versatile

   # Supabase Configuration (Auth, Database, Storage)
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   SUPABASE_STORAGE_BUCKET=private-datasets

   DATABASE_URL=sqlite:///./data/sample.db
   APP_ENV=development
   ```

5. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend API will be available at `http://127.0.0.1:8000` with interactive docs at `http://127.0.0.1:8000/docs`.

---

### 2. Frontend Setup

1. **Navigate to the frontend directory**:
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
   The frontend will be running at `http://localhost:5173`.

---

## Supabase Configuration & Migration Guide

The application is built to use Supabase for authentication, query history persistence, user profiles, and private storage for uploaded datasets.

### 1. Database Schema & RLS Setup
Run the SQL migration script located at [`backend/app/database/supabase_schema.sql`](file:///g:/Projects/SQL_Query_Generator/backend/app/database/supabase_schema.sql) in your **Supabase SQL Editor**:

1. **Profiles Table (`public.users`)**:
   - Mirrored from `auth.users` on signup via a database trigger.
   - Enforces RLS so users can only view and edit their own profiles.
2. **Query History (`public.query_history`)**:
   - Stores `natural_query`, `generated_sql`, `status`, `execution_time_ms`, and `created_at`.
   - Enforces RLS with `auth.uid() = user_id`.
3. **Uploaded Datasets (`public.uploaded_datasets`)**:
   - Stores file metadata, inferred column schema JSON, row counts, and storage paths.
   - Enforces RLS with `auth.uid() = user_id`.

### 2. Private Storage Bucket Setup
1. In the Supabase Dashboard, create a storage bucket named `private-datasets`.
2. Set the bucket to **Private** (public access disabled).
3. Apply the storage RLS policies in `supabase_schema.sql`:
   - Only authenticated users can upload files under their folder `user_id/filename`.
   - Only the owning user can read, download, or delete their stored files.

---

## Running Automated Tests

Run the backend test suite covering API contracts, SQL validation, read-only guardrails, multi-sheet Excel parsing, profile updates, and cross-user data isolation:

```powershell
backend\.venv\Scripts\pytest.exe backend/tests -v
```

Run the frontend production build test:
```bash
cd frontend
npm run build
```

---

## Google Cloud Deployment Readiness

The application is prepared for containerized deployment to **Google Cloud Run**:

1. **Stateless Backend Design**:
   - Uploaded files are uploaded to durable Supabase Storage (`private-datasets`).
   - If a container restarts or scales to a new instance, `DatasetService.ensure_sqlite_db_exists` reconstructs the isolated queryable SQLite database on-demand from Supabase Storage.
2. **Environment Variables**:
   - Never embed secrets in images or frontend builds.
   - Store `GROQ_API_KEY`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` in **Google Cloud Secret Manager** and inject them as environment variables into Cloud Run.
3. **CORS Configuration**:
   - Set `CORS_ORIGINS=["https://your-frontend-domain.web.app"]` in Cloud Run environment variables to restrict API access exclusively to your frontend.
4. **Health Check Endpoint**:
   - Cloud Run startup and liveness probes can monitor `/api/health`.

---

## Known Limitations

- Multi-statement queries (e.g. `SELECT 1; SELECT 2;`) are strictly blocked by the SQL validator to prevent SQL injection vulnerabilities.
- Destructive operations (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, `SELECT INTO`) are rejected by the read-only security filter.
- File uploads are capped at 15MB and 50,000 rows to ensure responsive performance in memory.
