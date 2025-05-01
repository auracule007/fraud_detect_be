from sqlalchemy.orm import Session
from . import models, schemas

def get_flagged_transactions(db: Session, user_id: str = None):
    query = db.query(models.FlaggedTransaction)
    if user_id:
        query = query.filter(models.FlaggedTransaction.user_id == user_id)
    return query.order_by(models.FlaggedTransaction.timestamp.desc()).all()

def get_fraud_stats(db: Session):
    flagged = db.query(models.FlaggedTransaction).all()
    return {
        "total_flagged": len(flagged),
        "high_frequency": len([t for t in flagged if "High frequency" in t.fraud_type]),
        "high_amount": len([t for t in flagged if "High amount" in t.fraud_type]),
        "rapid_location": len([t for t in flagged if "Rapid location" in t.fraud_type])
    }