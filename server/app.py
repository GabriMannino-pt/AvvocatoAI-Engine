"""
FastAPI REST and Static Server for AVVOCATO_AI Forensic Dashboard.
Provides interactive endpoints for document ingestion, transaction review,
bounding box overlay, human correction audit trail, and forensic report generation.
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime

from core.config import settings
from core.models import Transaction, ReviewStatus
from core.database import ForensicDatabase
from core.forensic_pipeline import ForensicPipeline

app = FastAPI(title="AVVOCATO_AI - Forensic Banking & Legal Intelligence", version="1.0.0")

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = ForensicPipeline()
db = ForensicDatabase()

# Mount static and output folders
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = settings.base_dir / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Store current in-memory case for quick UI access
CURRENT_CASE: Dict[str, Any] = {}

class CorrectionRequest(BaseModel):
    transaction_id: str
    field_name: str
    new_value: Any
    user_id: str = "PERITO_FORENSE"
    reason: str

@app.get("/")
def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    initial_balance: Optional[float] = Form(None),
    authorized_spending: Optional[float] = Form(None)
):
    upload_path = OUTPUT_DIR / file.filename
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    case = pipeline.process_pdf(
        str(upload_path),
        initial_balance=initial_balance,
        authorized_spending=authorized_spending
    )
    CURRENT_CASE["active"] = case
    return case.model_dump()

@app.get("/api/current_case")
def get_current_case():
    if "active" not in CURRENT_CASE:
        return {"status": "NO_ACTIVE_CASE", "transactions": []}
    return CURRENT_CASE["active"].model_dump()

@app.post("/api/correct")
def correct_transaction(req: CorrectionRequest):
    if "active" not in CURRENT_CASE:
        raise HTTPException(status_code=400, detail="Nessun fascicolo attivo.")
    
    case = CURRENT_CASE["active"]
    target_tx = next((t for t in case.transactions if t.id == req.transaction_id), None)
    if not target_tx:
        raise HTTPException(status_code=404, detail="Transazione non trovata.")

    old_val = getattr(target_tx, req.field_name, None)
    
    # Update field on transaction model
    if hasattr(target_tx, req.field_name):
        setattr(target_tx, req.field_name, req.new_value)
    
    target_tx.status = ReviewStatus.CORRECTED
    now_str = datetime.datetime.now().isoformat()
    
    # Audit log
    db.record_correction(
        tx_id=req.transaction_id,
        field_name=req.field_name,
        old_val=old_val,
        new_val=req.new_value,
        user_id=req.user_id,
        reason=req.reason,
        timestamp=now_str
    )
    
    target_tx.audit_history.append({
        "field": req.field_name,
        "old_value": old_val,
        "new_value": req.new_value,
        "user_id": req.user_id,
        "reason": req.reason,
        "timestamp": now_str
    })
    
    return {"status": "SUCCESS", "transaction": target_tx.model_dump()}

@app.get("/api/audit/{tx_id}")
def get_audit(tx_id: str):
    return db.get_audit_trail(tx_id)

@app.get("/api/report/markdown")
def get_report_markdown():
    if "active" not in CURRENT_CASE:
        raise HTTPException(status_code=400, detail="Nessun caso attivo.")
    case = CURRENT_CASE["active"]
    md = pipeline.report_generator.generate_markdown_report(
        case_title=case.title,
        doc_name=case.documents[0] if case.documents else "DOCUMENTO",
        transactions=case.transactions,
        summary=case.summary,
        anomalies=case.anomalies,
        hypotheses=case.legal_hypotheses,
        requests=case.document_requests
    )
    return {"markdown": md}
