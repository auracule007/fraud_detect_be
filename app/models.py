from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from .database import Base
from datetime import datetime

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime)
    merchant = Column(String)
    location = Column(String)
    is_flagged = Column(Boolean, default=False)
    fraud_type = Column(String, nullable=True)

class FlaggedTransaction(Base):
    __tablename__ = "flagged_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True)
    user_id = Column(String, index=True)
    fraud_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    amount = Column(Float)
    location = Column(String)