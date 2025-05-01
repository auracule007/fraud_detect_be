from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
from sqlalchemy.orm import Session
from . import models  # Add this import

class FraudDetector:
    def __init__(self, db: Session):
        self.user_transactions: Dict[str, List[Dict]] = defaultdict(list)
        self.user_daily_amount: Dict[str, float] = defaultdict(float)
        self.db = db
        self.current_date = None

    def process_transaction(self, transaction_data: Dict):
        # Convert timestamp if needed
        if isinstance(transaction_data['timestamp'], str):
            transaction_data['timestamp'] = datetime.fromisoformat(transaction_data['timestamp'])
        
        # Store transaction
        transaction = self._store_transaction(transaction_data)
        
        # Check for fraud patterns
        self._check_high_frequency(transaction)
        self._check_high_amount(transaction)
        self._check_rapid_location_change(transaction)
        
        return transaction

    def _check_high_frequency(self, transaction):
        user_id = transaction.user_id
        current_time = transaction.timestamp
        
        # Filter transactions within last minute
        self.user_transactions[user_id] = [
            t for t in self.user_transactions[user_id] 
            if (current_time - t['timestamp']) < timedelta(minutes=1)
        ]
        
        # Add current transaction
        self.user_transactions[user_id].append({
            'transaction_id': transaction.transaction_id,
            'timestamp': current_time
        })
        
        # Check if more than 5 transactions in 1 minute
        if len(self.user_transactions[user_id]) > 5:
            self._flag_transaction(
                transaction,
                "High frequency (more than 5 transactions in 1 minute)"
            )

    def _check_high_amount(self, transaction):
        user_id = transaction.user_id
        transaction_date = transaction.timestamp.date()
        
        # Reset daily amounts if date changed
        if self.current_date != transaction_date:
            self.user_daily_amount = defaultdict(float)
            self.current_date = transaction_date
        
        # Update daily amount
        self.user_daily_amount[user_id] += transaction.amount
        
        # Check if exceeds $10,000
        if self.user_daily_amount[user_id] > 10000:
            self._flag_transaction(
                transaction,
                "High amount (over $10,000 in a day)"
            )

    def _check_rapid_location_change(self, transaction):
        user_id = transaction.user_id
        current_time = transaction.timestamp
        
        # Get transactions within last 2 minutes
        recent_transactions = self.db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.timestamp >= current_time - timedelta(minutes=2)
        ).all()
        
        if recent_transactions:
            unique_locations = {t.location for t in recent_transactions}
            if transaction.location not in unique_locations:
                unique_locations.add(transaction.location)
                if len(unique_locations) > 1:
                    self._flag_transaction(
                        transaction,
                        "Rapid location change (different locations within 2 minutes)"
                    )

    def _flag_transaction(self, transaction, fraud_type: str):
        # Check if already flagged for this fraud type
        existing = self.db.query(models.FlaggedTransaction).filter(
            models.FlaggedTransaction.transaction_id == transaction.transaction_id,
            models.FlaggedTransaction.fraud_type == fraud_type
        ).first()
        
        if not existing:
            # Update transaction record
            transaction.is_flagged = True
            transaction.fraud_type = fraud_type
            self.db.commit()
            
            # Create flagged transaction record
            flagged = models.FlaggedTransaction(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                fraud_type=fraud_type,
                amount=transaction.amount,
                location=transaction.location,
                timestamp=transaction.timestamp
            )
            self.db.add(flagged)
            self.db.commit()

    def _store_transaction(self, transaction_data: Dict):
        # Check if transaction exists
        db_transaction = self.db.query(models.Transaction).filter(
            models.Transaction.transaction_id == transaction_data['transaction_id']
        ).first()
        
        if not db_transaction:
            db_transaction = models.Transaction(
                transaction_id=transaction_data['transaction_id'],
                user_id=transaction_data['user_id'],
                amount=transaction_data['amount'],
                timestamp=transaction_data['timestamp'],
                merchant=transaction_data['merchant'],
                location=transaction_data['location']
            )
            self.db.add(db_transaction)
            self.db.commit()
            self.db.refresh(db_transaction)
        
        return db_transaction