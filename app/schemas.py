from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TransactionBase(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    timestamp: datetime
    merchant: str
    location: str

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    is_flagged: bool
    fraud_type: Optional[str] = None

    class Config:
        from_attributes = True

class FlaggedTransactionBase(BaseModel):
    transaction_id: str
    user_id: str
    fraud_type: str
    amount: float
    location: str
    timestamp: datetime

class FlaggedTransaction(FlaggedTransactionBase):
    id: int

    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    message: str
    processed_count: int
    flagged_count: int

class FraudStats(BaseModel):
    total_flagged: int
    high_frequency: int
    high_amount: int
    rapid_location: int