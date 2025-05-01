from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import json
import io
from datetime import datetime
from typing import List
from app import models, schemas, utils, crud
from app.database import SessionLocal, engine
from app.config import settings


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def parse_txt_content(content: bytes) -> List[dict]:
    """Parse TXT file content where each line represents a transaction"""
    try:
        # Decode the content and split into lines
        lines = content.decode('utf-8').splitlines()
        
        # Skip header if exists
        if lines[0].startswith('transaction_id'):
            lines = lines[1:]
        
        transactions = []
        for line in lines:
            if not line.strip():
                continue
                
            # Split line by comma or tab (adjust as needed for your format)
            parts = [p.strip() for p in line.split(',') if p.strip()]
            
            if len(parts) < 6:
                continue
                
            transaction = {
                'transaction_id': parts[0],
                'user_id': parts[1],
                'amount': float(parts[2]),
                'timestamp': parts[3],
                'merchant': parts[4],
                'location': parts[5]
            }
            transactions.append(transaction)
            
        return transactions
    except Exception as e:
        raise ValueError(f"Error parsing TXT file: {str(e)}")

@app.post(f"{settings.API_PREFIX}/transactions/upload/", response_model=schemas.FileUploadResponse)
async def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Validate file type
        if not (file.filename.endswith('.csv') or 
                file.filename.endswith('.json') or 
                file.filename.endswith('.txt')):
            raise HTTPException(
                status_code=400, 
                detail="Only CSV, JSON, or TXT files are allowed"
            )

        content = await file.read()
        
        if file.filename.endswith('.json'):
            try:
                transactions = json.loads(content)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format")
        elif file.filename.endswith('.txt'):
            try:
                transactions = parse_txt_content(content)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:  # CSV
            try:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
                transactions = df.to_dict('records')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
        
        fraud_detector = utils.FraudDetector(db)
        processed_count = 0
        flagged_count = 0
        
        for t in transactions:
            try:
                # Validate required fields
                required_fields = ['transaction_id', 'user_id', 'amount', 'timestamp', 'merchant', 'location']
                if not all(field in t for field in required_fields):
                    continue
                    
                # Convert timestamp if needed
                if isinstance(t['timestamp'], str):
                    try:
                        t['timestamp'] = datetime.fromisoformat(t['timestamp'])
                    except ValueError:
                        continue
                
                # Convert amount to float if needed
                if isinstance(t['amount'], str):
                    try:
                        t['amount'] = float(t['amount'])
                    except ValueError:
                        continue
                
                # Process transaction
                transaction = fraud_detector.process_transaction(t)
                processed_count += 1
                
                if transaction.is_flagged:
                    flagged_count += 1
                    
            except Exception as e:
                print(f"Error processing transaction {t}: {str(e)}")
                continue
        
        return {
            "message": f"Successfully processed {processed_count} transactions",
            "processed_count": processed_count,
            "flagged_count": flagged_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{settings.API_PREFIX}/flagged/", response_model=List[schemas.FlaggedTransaction])
async def get_flagged_transactions(user_id: str = None, db: Session = Depends(get_db)):
    return crud.get_flagged_transactions(db, user_id)

@app.get(f"{settings.API_PREFIX}/stats/", response_model=schemas.FraudStats)
async def get_fraud_stats(db: Session = Depends(get_db)):
    return crud.get_fraud_stats(db)

@app.get("/")
async def root():
    return {"message": "Fraud Detection System API"}