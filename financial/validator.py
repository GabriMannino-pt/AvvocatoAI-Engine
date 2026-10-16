"""
Mathematical Balance Validator.
Verifies accounting continuity:
    Saldo_{t-1} + Accrediti - Addebiti - Commissioni = Saldo_t
Under the strict Zero Silent Correction rule:
Flags mathematical discrepancies, categorizes possible OCR digit confusions (e.g. 2 vs 8, 3 vs 8, 5 vs 6),
and records detailed forensic integrity warnings.
"""
from typing import List, Dict, Any, Tuple, Optional
from core.models import Transaction, StatementSummary, ReviewStatus
from core.config import settings

class FinancialValidator:
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def validate_statement_sequence(self, transactions: List[Transaction], initial_balance: Optional[float] = None) -> Tuple[StatementSummary, List[Dict[str, Any]]]:
        """
        Validates mathematical sequence across transactions.
        Returns:
            (StatementSummary, discrepancies: List[Dict])
        """
        discrepancies: List[Dict[str, Any]] = []
        total_debits = 0.0
        total_credits = 0.0
        
        running_balance = initial_balance
        
        for idx, tx in enumerate(transactions):
            debit = tx.amount_debit or 0.0
            credit = tx.amount_credit or 0.0
            total_debits += debit
            total_credits += credit
            
            if running_balance is not None:
                expected_balance = round(running_balance + credit - debit, 2)
                
                if tx.balance is not None:
                    actual_balance = round(tx.balance, 2)
                    diff = round(abs(expected_balance - actual_balance), 2)
                    
                    if diff > self.tolerance:
                        # Mathematical discrepancy detected!
                        tx.status = ReviewStatus.DATA_INTEGRITY_ERROR
                        warning = f"BALANCE_MISMATCH: Saldo calcolato €{expected_balance:.2f} != Saldo OCR €{actual_balance:.2f} (diff €{diff:.2f})"
                        tx.warnings.append(warning)
                        
                        # Diagnose possible OCR digit confusion
                        diagnosis = self.diagnose_ocr_discrepancy(expected_balance, actual_balance, diff)
                        
                        disc_record = {
                            "transaction_id": tx.id,
                            "row_id": tx.row_id,
                            "page": tx.page,
                            "previous_balance": running_balance,
                            "movement": credit - debit,
                            "expected_balance": expected_balance,
                            "ocr_reported_balance": actual_balance,
                            "discrepancy": diff,
                            "possible_digit_confusion": diagnosis,
                            "status": "POSSIBLE_OCR_ERROR"
                        }
                        discrepancies.append(disc_record)
                        
                        # Do NOT silently alter running balance!
                        # We track both expected and reported
                        running_balance = actual_balance
                    else:
                        running_balance = actual_balance
                else:
                    running_balance = expected_balance
            elif tx.balance is not None:
                running_balance = tx.balance

        is_reconciled = (len(discrepancies) == 0)
        final_balance_calc = None
        if initial_balance is not None:
            final_balance_calc = round(initial_balance + total_credits - total_debits, 2)

        doc_name = transactions[0].document_name if transactions else "UNKNOWN"
        page_count = max((t.page for t in transactions), default=1)
        final_reported = transactions[-1].balance if (transactions and transactions[-1].balance is not None) else None

        summary = StatementSummary(
            document_name=doc_name,
            page_count=page_count,
            initial_balance=initial_balance,
            total_debits=round(total_debits, 2),
            total_credits=round(total_credits, 2),
            final_balance_reported=final_reported,
            final_balance_calculated=final_balance_calc,
            discrepancy=round(abs((final_reported or 0.0) - (final_balance_calc or 0.0)), 2) if (final_reported and final_balance_calc) else 0.0,
            is_mathematically_reconciled=is_reconciled,
            transaction_count=len(transactions),
            warnings=[d["status"] + ": " + str(d["discrepancy"]) for d in discrepancies]
        )

        return summary, discrepancies

    def diagnose_ocr_discrepancy(self, expected: float, actual: float, diff: float) -> str:
        """
        Diagnoses typical OCR digit confusion patterns based on numerical delta.
        e.g. diff == 0.60: 8 vs 2 confusion (1543.80 vs 1543.20)
             diff == 2.00: 3 vs 5 or 6 vs 8 confusion
             diff == 10.00: 0 vs 1 tens position
        """
        # Format strings to compare digit-by-digit
        exp_str = f"{expected:.2f}"
        act_str = f"{actual:.2f}"
        
        if len(exp_str) == len(act_str):
            diff_positions = []
            for i, (c1, c2) in enumerate(zip(exp_str, act_str)):
                if c1 != c2:
                    diff_positions.append(f"Pos {i}: atteso '{c1}' vs OCR '{c2}'")
            if diff_positions:
                return f"Possibile scambio di cifra ({', '.join(diff_positions)})"
        
        if abs(diff - 0.60) < 0.01:
            return "Tipico scambio tra cifra '2' e cifra '8' sui decimali (differenza 0.60)"
        if abs(diff - 2.00) < 0.01:
            return "Tipico scambio tra '3'/'5' o '6'/'8' sulle unità (differenza 2.00)"
        if abs(diff - 100.00) < 0.01:
            return "Tipico scambio su centinaia (differenza 100.00)"
            
        return f"Discrepanza aritmetica di €{diff:.2f} non attribuibile a singola cifra nota"
