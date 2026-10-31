from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.seed import seed_database
from app.api.routes import (
    auth,
    data,
    connections,
    generate,
    execute,
    explain,
    correct,
    schema,
    history,
    health
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database exists, tables created, and seeded
    try:
        seed_database()
    except Exception as e:
        print(f"Warning: Startup database seeding encountered an issue: {e}")
    yield
    # Shutdown logic if any

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack AI-powered SQL Query Generator from Plain English with multi-database support, file uploads, safe query validation, and cloud connectivity.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(connections.router)
app.include_router(generate.router)
app.include_router(execute.router)
app.include_router(explain.router)
app.include_router(correct.router)
app.include_router(schema.router)
app.include_router(history.router)

@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
