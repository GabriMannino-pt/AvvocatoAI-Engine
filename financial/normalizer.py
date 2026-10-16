"""
Financial Field Normalizer.
Standardizes dates, amounts, transaction types, and fee descriptions.
"""
import re
from typing import Optional, Tuple, Dict, Any
from core.models import TransactionType
from ocr.reconciler import OCRReconciler

class FinancialNormalizer:
    def __init__(self):
        self.reconciler = OCRReconciler()

    def normalize_date(self, raw_date: str) -> Optional[str]:
        """
        Normalizes various Italian date notations into DD/MM/YYYY.
        e.g. 15.02.16 -> 15/02/2016
             15/02/2016 -> 15/02/2016
        """
        s = raw_date.strip().replace("-", "/").replace(".", "/")
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', s)
        if not match:
            return None
        
        day, month, year = match.groups()
        day = f"{int(day):02d}"
        month = f"{int(month):02d}"
        if len(year) == 2:
            if year in ["75", "76"]:
                year = f"201{year[1]}"
            else:
                year = f"20{year}"
        elif len(year) == 4 and year.startswith("207"):
            year = f"201{year[3]}"
        
        return f"{day}/{month}/{year}"

    def normalize_amount(self, raw_amount: str) -> Optional[float]:
        """
        Normalizes a string amount to a float value.
        Preserves negative signs if present.
        """
        is_negative = "-" in raw_amount
        val = self.reconciler.parse_numeric_amount(raw_amount)
        if val is None:
            return None
        if is_negative and val > 0:
            val = -val
        return val

    def classify_transaction_type(self, description: str, debit: Optional[float], credit: Optional[float]) -> TransactionType:
        """
        Classifies transaction type based on description keywords and amount sign.
        """
        upper = description.upper()
        
        # Pension detection (INPS / Pensione)
        if any(w in upper for w in ["PENSIONE", "INPS", "ACCREDITO PENSIONE", "PENS."]):
            return TransactionType.PENSION_CREDIT
        
        # Salary detection
        if any(w in upper for w in ["STIPENDIO", "EMOLUMENTI", "RETRIBUZIONE"]):
            return TransactionType.SALARY_CREDIT
        
        # Cash withdrawal (Prelievo)
        if any(w in upper for w in ["PRELIEVO", "POSTAMAT", "PREL.", "EROGAZIONE CONTANTE"]):
            return TransactionType.CASH_WITHDRAWAL

        # Bank/service fees
        if any(w in upper for w in ["COMMISSIONE", "COMMISSIONI", "SPESE TENUTA", "IMPOSTA DI BOLLO", "CANONE"]):
            return TransactionType.BANK_FEE

        # POS payment
        if any(w in upper for w in ["PAGAMENTO POS", "PAGOBANCOMAT", "ACQUISTO CARTA"]):
            return TransactionType.POS_PAYMENT

        # Transfers
        if any(w in upper for w in ["BONIFICO", "POSTAGIRO", "GIROCONTO"]):
            if credit and credit > 0:
                return TransactionType.TRANSFER_IN
            return TransactionType.TRANSFER_OUT

        # General cash deposit
        if any(w in upper for w in ["VERSAMENTO", "DEPOSITO CONTANTE"]):
            return TransactionType.DEPOSIT

        if credit and credit > 0:
            return TransactionType.TRANSFER_IN
        if debit and debit > 0:
            return TransactionType.TRANSFER_OUT

        return TransactionType.OTHER
