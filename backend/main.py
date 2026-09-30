import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.base import Base
from backend.database.session import engine, SessionLocal
from backend.utils.middleware import ObservabilityMiddleware
from backend.utils.seed import seed_sample_data
from backend.utils.logger import logger
from backend.routes import (
    invoice_router,
    payment_router,
    webhook_router,
    reconciliation_router,
    system_router
)

# 1. Initialize Database Tables on Startup
Base.metadata.create_all(bind=engine)

# 2. Instantiate FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade Healthcare Billing, Payments & Reconciliation Backend Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 3. Add Custom Observability Middleware (Request Latency & Tracing)
app.add_middleware(ObservabilityMiddleware)

# 4. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Include API Routers
app.include_router(invoice_router)
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(reconciliation_router)
app.include_router(system_router)

@app.on_event("startup")
def startup_event():
    logger.info("PulsePay Healthcare Reconciliation Engine starting up...")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
