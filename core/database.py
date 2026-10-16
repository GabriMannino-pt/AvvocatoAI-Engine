"""
SQLite database repository for storing forensic cases, documents, transactions,
and immutable audit trails with WAL mode.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.config import settings
from core.models import Transaction, Anomaly, LegalHypothesis, DocumentRequest, StatementSummary

class ForensicDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                metadata_json TEXT
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                filename TEXT,
                file_path TEXT,
                page_count INTEGER,
                ingested_at TEXT,
                metadata_json TEXT
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                document_name TEXT,
                page INTEGER,
                row_id TEXT,
                date_accounting TEXT,
                date_value TEXT,
                time_str TEXT,
                description TEXT,
                amount_debit REAL,
                amount_credit REAL,
                balance REAL,
                channel TEXT,
                channel_detail TEXT,
                transaction_type TEXT,
                raw_ocr_text TEXT,
                confidence_score REAL,
                status TEXT,
                bbox_json TEXT,
                image_crop_path TEXT,
                warnings_json TEXT,
                field_confidences_json TEXT,
                human_correction_json TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                user_id TEXT,
                reason TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS anomalies (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                category TEXT,
                severity TEXT,
                title TEXT,
                description TEXT,
                discrepancy_amount REAL,
                data_json TEXT
            );

            CREATE TABLE IF NOT EXISTS legal_hypotheses (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                norm_reference TEXT,
                norm_title TEXT,
                article TEXT,
                confidence_degree TEXT,
                data_json TEXT
            );

            CREATE TABLE IF NOT EXISTS document_requests (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                document_name TEXT,
                subject_holder TEXT,
                priority TEXT,
                data_json TEXT
            );
            """)

    def save_transactions(self, case_id: str, transactions: List[Transaction]):
        with self._get_conn() as conn:
            for tx in transactions:
                conn.execute("""
                INSERT OR REPLACE INTO transactions (
                    id, case_id, document_name, page, row_id, date_accounting,
                    date_value, time_str, description, amount_debit, amount_credit,
                    balance, channel, channel_detail, transaction_type, raw_ocr_text,
                    confidence_score, status, bbox_json, image_crop_path, warnings_json,
                    field_confidences_json, human_correction_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx.id, case_id, tx.document_name, tx.page, tx.row_id,
                    tx.date_accounting, tx.date_value, tx.time_str, tx.description,
                    tx.amount_debit, tx.amount_credit, tx.balance,
                    tx.channel.value if hasattr(tx.channel, "value") else str(tx.channel),
                    tx.channel_detail,
                    tx.transaction_type.value if hasattr(tx.transaction_type, "value") else str(tx.transaction_type),
                    tx.raw_ocr_text, tx.confidence_score,
                    tx.status.value if hasattr(tx.status, "value") else str(tx.status),
                    tx.bounding_box.model_dump_json(),
                    tx.image_crop_path,
                    json.dumps(tx.warnings),
                    json.dumps(tx.field_confidences),
                    json.dumps(tx.human_correction) if tx.human_correction else None
                ))

    def record_correction(self, tx_id: str, field_name: str, old_val: Any, new_val: Any, user_id: str, reason: str, timestamp: str):
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO audit_trail (transaction_id, field_name, old_value, new_value, user_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, field_name, str(old_val), str(new_val), user_id, reason, timestamp))
            
            # Update transaction status
            conn.execute("UPDATE transactions SET status = 'CORRECTED' WHERE id = ?", (tx_id,))

    def get_transactions(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            query = "SELECT * FROM transactions"
            params = []
            if case_id:
                query += " WHERE case_id = ?"
                params.append(case_id)
            query += " ORDER BY page ASC, row_id ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_audit_trail(self, tx_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM audit_trail WHERE transaction_id = ? ORDER BY timestamp DESC", (tx_id,)).fetchall()
            return [dict(r) for r in rows]
