from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.services.audit_service import AuditService
from backend.utils.seed import seed_sample_data

router = APIRouter(tags=["System Observability & Auditing"])

@router.get("/metrics")
def get_system_metrics(db: Session = Depends(get_db)):
    """Retrieve financial, operational, and webhook observability metrics."""
    return AuditService.get_system_metrics(db)

@router.get("/audit-logs")
def get_audit_logs(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Retrieve system audit logs."""
    logs = AuditService.get_recent_logs(db, limit=limit)
    return [log.to_dict() for log in logs]

@router.post("/seed")
def seed_database(force: bool = False, db: Session = Depends(get_db)):
    """Seed sample healthcare billing dataset and test mismatch scenarios."""
    return seed_sample_data(db, force=force)
