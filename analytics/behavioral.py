"""
Behavioral Account Profiler.
Analyzes historical financial patterns to establish account baseline:
- Habitual withdrawal amounts and frequencies
- Typical pension credit calendar
- Usual ATM / branch locations
"""
from typing import List, Dict, Any, Optional
import statistics
from core.models import Transaction, TransactionType

class BehavioralProfiler:
    def analyze_account_profile(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """
        Computes baseline statistics and regularities across all transactions.
        """
        withdrawals = [t for t in transactions if t.transaction_type == TransactionType.CASH_WITHDRAWAL and (t.amount_debit or 0) > 0]
        pensions = [t for t in transactions if t.transaction_type == TransactionType.PENSION_CREDIT and (t.amount_credit or 0) > 0]
        
        withdrawal_amounts = [t.amount_debit for t in withdrawals if t.amount_debit is not None]
        
        profile = {
            "total_transactions": len(transactions),
            "total_withdrawals": len(withdrawals),
            "total_pension_credits": len(pensions),
            "withdrawal_stats": {},
            "pension_stats": {},
            "frequent_atms": {},
            "typical_withdrawal_days": []
        }
        
        if withdrawal_amounts:
            profile["withdrawal_stats"] = {
                "mean": round(statistics.mean(withdrawal_amounts), 2),
                "median": round(statistics.median(withdrawal_amounts), 2),
                "min": round(min(withdrawal_amounts), 2),
                "max": round(max(withdrawal_amounts), 2),
                "total": round(sum(withdrawal_amounts), 2)
            }
            
        pension_amounts = [t.amount_credit for t in pensions if t.amount_credit is not None]
        if pension_amounts:
            profile["pension_stats"] = {
                "mean": round(statistics.mean(pension_amounts), 2),
                "median": round(statistics.median(pension_amounts), 2),
                "total": round(sum(pension_amounts), 2)
            }

        # ATM terminal usage frequency
        atm_counts: Dict[str, int] = {}
        for t in withdrawals:
            if t.atm_id:
                atm_counts[t.atm_id] = atm_counts.get(t.atm_id, 0) + 1
        profile["frequent_atms"] = atm_counts

        return profile
