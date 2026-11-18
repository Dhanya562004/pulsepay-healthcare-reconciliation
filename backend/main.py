import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.base import Base
from backend.database.session import engine, SessionLocal
from backend.utils.middleware import ObservabilityMiddleware, ApiKeyMiddleware
from backend.utils.seed import seed_sample_data
from backend.utils.logger import logger
from backend.routes import (
    invoice_router,
    payment_router,
    webhook_router,
    reconciliation_router,
    system_router
)

def create_app() -> FastAPI:
    # 1. Initialize Database Tables on Startup
    Base.metadata.create_all(bind=engine)

    # 2. Instantiate FastAPI App
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Healthcare Billing, Payments & Reconciliation Simulation Backend Engine",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 3. Add Custom Observability Middleware (Request Latency & Tracing)
    app.add_middleware(ObservabilityMiddleware)

    # 4. Add API Key Authentication Middleware
    app.add_middleware(ApiKeyMiddleware)

    # 5. Add CORS Middleware
    # Allow only origins listed in CORS_ALLOWED_ORIGINS (comma-separated).
    # Never use "*" together with credentials. Default to no cross-origin access if unset.
    raw_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", "") or ""
    cors_list = [o.strip() for o in raw_origins.split(",") if o.strip()]
    allow_credentials = True if ("*" not in cors_list and len(cors_list) > 0) else False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_list,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 6. Include API Routers
    app.include_router(invoice_router)
    app.include_router(payment_router)
    app.include_router(webhook_router)
    app.include_router(reconciliation_router)
    app.include_router(system_router)

    @app.on_event("startup")
    def startup_event():
        logger.info("PulsePay Healthcare Reconciliation Engine starting up...")
        
        # Enforce API_KEY presence in production mode
        if settings.ENVIRONMENT.lower() == "production" and not settings.API_KEY:
            error_msg = "CRITICAL: API_KEY environment variable is not set in production mode. Startup aborted."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        db = SessionLocal()
        try:
            seed_sample_data(db, force=False)
        finally:
            db.close()

    @app.get("/", tags=["Health"])
    def health_check():
        return {
            "status": "online",
            "system": settings.PROJECT_NAME,
            "database": settings.DATABASE_URL.split(":///")[0],
            "environment": settings.ENVIRONMENT,
            "docs": "/docs"
        }

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
