"""
FastAPI Application Factory for RescueAI Operations Console
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

from rescueai.database import init_db
from rescueai.services import ModelService, DataService
from rescueai.api.routes import meta, messages, predict, models, terms, ops


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes SQLite database and preloads ML models and test datasets once at startup."""
    print("[RescueAI] Initializing database...")
    init_db()
    
    print("[RescueAI] Loading Scikit-Learn models and vectorizers...")
    models_svc = ModelService(models_dir="models", reports_dir="reports")
    app.state.models_service = models_svc
    
    print("[RescueAI] Loading CrisisMMD datasets and precomputing test set cache...")
    data_svc = DataService(data_dir="data/processed", models_service=models_svc)
    app.state.data_service = data_svc
    
    print("[RescueAI] Initialization complete. Operations API ready.")
    yield
    print("[RescueAI] Shutting down Operations API.")


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    app = FastAPI(
        title="RescueAI Operations API",
        description="High-performance backend API for the RescueAI Disaster Relief Operations Console.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Enable CORS for Vite frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API Routers under /api prefix
    app.include_router(meta.router, prefix="/api")
    app.include_router(messages.router, prefix="/api")
    app.include_router(predict.router, prefix="/api")
    app.include_router(models.router, prefix="/api")
    app.include_router(terms.router, prefix="/api")
    app.include_router(ops.router, prefix="/api")
    
    # Static build mounting for single-port serving
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir) and os.path.exists(os.path.join(static_dir, "index.html")):
        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # If path starts with api/ or docs, let it 404 or pass
            if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
                return None
            target = os.path.join(static_dir, full_path)
            if os.path.exists(target) and os.path.isfile(target):
                return FileResponse(target)
            return FileResponse(os.path.join(static_dir, "index.html"))
    else:
        @app.get("/")
        async def root():
            return RedirectResponse(url="/docs")
            
    return app


app = create_app()
