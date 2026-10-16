"""
Unit tests for financial normalization and mathematical balance reconciliation.
Verifies the Zero Silent Correction rule and digit confusion diagnostics.
"""
import pytest
from financial.normalizer import FinancialNormalizer
from financial.validator import FinancialValidator
from core.models import Transaction, BoundingBox, ChannelType, TransactionType, ReviewStatus

def test_financial_normalization():
    norm = FinancialNormalizer()
    assert norm.normalize_date("15/02/16") == "15/02/2016"
    assert norm.normalize_date("02-02-2016") == "02/02/2016"
    
    assert norm.normalize_amount("600,00") == 600.0
    assert norm.normalize_amount("2.143,20") == 2143.20
    assert norm.normalize_amount("-1.543,80") == -1543.80

def test_zero_silent_correction_balance_mismatch():
    validator = FinancialValidator()
    
    # Simulate statement sequence from prompt:
    # Initial balance: 2143.20
    # Movement: -600.00
    # Expected balance: 1543.20
    # OCR read: 1543.80 (typo between 2 and 8)
    tx = Transaction(
        id="TX_TEST_01",
        document_name="test.pdf",
        page=1,
        row_id="p1_r001",
        date_accounting="15/02/2016",
        description="PRELIEVO POSTAMAT",
        amount_debit=600.00,
        balance=1543.80,  # Intentional discrepancy
        channel=ChannelType.ATM,
        channel_detail="SPORTELLO_AUTOMATICO",
        transaction_type=TransactionType.CASH_WITHDRAWAL,
        bounding_box=BoundingBox(x=10, y=10, width=100, height=20),
        raw_ocr_text="15/02/2016 PRELIEVO POSTAMAT 600,00 1.543,80",
        confidence_score=90.0
    )
    
    summary, discrepancies = validator.validate_statement_sequence([tx], initial_balance=2143.20)
    
    assert len(discrepancies) == 1
    disc = discrepancies[0]
    assert disc["discrepancy"] == 0.60
    assert "2" in disc["possible_digit_confusion"] and "8" in disc["possible_digit_confusion"]
    assert tx.status == ReviewStatus.DATA_INTEGRITY_ERROR
    assert not summary.is_mathematically_reconciled
