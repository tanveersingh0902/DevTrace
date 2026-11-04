"""
DevTrace — Main FastAPI Application.

This is the entry point for the entire backend. It:
1. Creates the FastAPI application instance
2. Configures CORS (Cross-Origin Resource Sharing)
3. Registers API routers
4. Provides a health check endpoint

WHY CORS?
When the React frontend (running on localhost:5173) makes API calls to the
FastAPI backend (running on localhost:8000), the browser blocks this by default
because they're different "origins". CORS headers tell the browser it's OK.

HOW TO RUN:
    cd backend
    uvicorn app.main:app --reload

The --reload flag watches for file changes and auto-restarts the server.
Only use this in development, never in production.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.scan import router as scan_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Codebase Intelligence and Visualisation Platform. "
        "Analyse source code, detect dependencies, and generate interactive graphs."
    ),
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
)

# --- CORS Middleware ---
# This MUST be added before any routes. It tells the browser which origins
# (frontend URLs) are allowed to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(scan_router, prefix=settings.api_prefix)


# --- Health Check ---
# A simple endpoint that returns the application status.
# Used by monitoring tools, CI pipelines, and the frontend to verify
# the backend is running.
@app.get("/health", tags=["System"])
async def health_check():
    """Return the application health status."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


# --- Root Endpoint ---
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
