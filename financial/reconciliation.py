"""
Comprehensive Multi-Year Financial Reconciliation Engine (2016 - 2026).
Implements the core mathematical verification:
    Saldo_iniziale + Entrate - Uscite = Saldo_teorico vs Saldo_documentato
Computes:
- Yearly Ledger (2016 - 2026)
- Quarterly Rollups (Q1 2016 - Q4 2026)
- "Quanto avrebbe dovuto avere?" (Saldo Reale vs Saldo Ricostruito vs Saldo Atteso)
- Scomposizione dell'incremento/decremento patrimoniale
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from core.models import Transaction, PeriodicReconciliation, TransactionType

class MultiYearReconciliationEngine:
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def _parse_date(self, d_str: Optional[str]) -> Optional[datetime]:
        if not d_str:
            return None
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(d_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def reconcile_multi_year(
        self,
        transactions: List[Transaction],
        initial_balance: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes complete multi-year and quarterly reconciliation.
        """
        # 1. Sort transactions strictly by accounting date
        valid_txs = []
        for t in transactions:
            dt = self._parse_date(t.date_accounting) or self._parse_date(t.date_value)
            valid_txs.append((dt or datetime(1970, 1, 1), t))
        
        valid_txs.sort(key=lambda x: x[0])
        sorted_txs = [x[1] for x in valid_txs]

        # 2. Group by Year and Quarter
        by_year: Dict[int, List[Transaction]] = defaultdict(list)
        by_quarter: Dict[Tuple[int, int], List[Transaction]] = defaultdict(list)

        for dt, t in valid_txs:
            if dt.year >= 2000:
                y = dt.year
                q = (dt.month - 1) // 3 + 1
                by_year[y].append(t)
                by_quarter[(y, q)].append(t)

        all_years = sorted(by_year.keys())
        all_quarters = sorted(by_quarter.keys())

        # 3. Process Quarterly Reconciliations
        quarterly_records: List[PeriodicReconciliation] = []
        running_bal = initial_balance

        for (y, q) in all_quarters:
            q_txs = by_quarter[(y, q)]
            q_credits = sum(t.amount_credit or 0.0 for t in q_txs)
            q_debits = sum(t.amount_debit or 0.0 for t in q_txs)
            q_cash = sum(t.amount_debit or 0.0 for t in q_txs if t.transaction_type in [TransactionType.CASH_WITHDRAWAL, TransactionType.PRELIEVO_ATM, TransactionType.PRELIEVO_SPORTELLO_FISICO])
            q_transfers = sum(t.amount_debit or 0.0 for t in q_txs if t.transaction_type in [TransactionType.TRANSFER_OUT, TransactionType.BONIFICO_OUT])
            q_fees = sum(t.amount_debit or 0.0 for t in q_txs if t.transaction_type in [TransactionType.BANK_FEE, TransactionType.COMMISSIONE, TransactionType.IMPOSTE, TransactionType.SPESE])
            
            q_open = running_bal if running_bal is not None else (q_txs[0].balance if q_txs and q_txs[0].balance is not None else 0.0)
            q_theo = round(q_open + q_credits - q_debits, 2)
            
            # Find reported closing balance if available
            q_actual = q_theo
            for t in reversed(q_txs):
                if t.balance is not None:
                    q_actual = round(t.balance, 2)
                    break
            
            diff = round(abs(q_actual - q_theo), 2)
            is_rec = (diff <= self.tolerance)
            
            quarterly_records.append(PeriodicReconciliation(
                period_id=f"Q_{y}_{q}",
                period_type="QUARTERLY",
                period_name=f"Q{q} {y}",
                year=y,
                quarter=q,
                opening_balance=round(q_open, 2),
                total_credits=round(q_credits, 2),
                total_debits=round(q_debits, 2),
                total_cash_withdrawals=round(q_cash, 2),
                total_transfers=round(q_transfers, 2),
                total_fees=round(q_fees, 2),
                theoretical_balance=q_theo,
                actual_balance=q_actual,
                difference=diff,
                is_reconciled=is_rec,
                transaction_count=len(q_txs),
                unreconciled_reason=f"Divergenza contabile di €{diff:.2f} nel trimestre Q{q} {y}" if not is_rec else None
            ))
            running_bal = q_actual

        # 4. Process Yearly Reconciliations
        yearly_records: List[PeriodicReconciliation] = []
        running_bal_yr = initial_balance

        for y in all_years:
            y_txs = by_year[y]
            y_credits = sum(t.amount_credit or 0.0 for t in y_txs)
            y_debits = sum(t.amount_debit or 0.0 for t in y_txs)
            y_cash = sum(t.amount_debit or 0.0 for t in y_txs if t.transaction_type in [TransactionType.CASH_WITHDRAWAL, TransactionType.PRELIEVO_ATM, TransactionType.PRELIEVO_SPORTELLO_FISICO])
            y_transfers = sum(t.amount_debit or 0.0 for t in y_txs if t.transaction_type in [TransactionType.TRANSFER_OUT, TransactionType.BONIFICO_OUT])
            y_fees = sum(t.amount_debit or 0.0 for t in y_txs if t.transaction_type in [TransactionType.BANK_FEE, TransactionType.COMMISSIONE, TransactionType.IMPOSTE, TransactionType.SPESE])
            
            y_open = running_bal_yr if running_bal_yr is not None else (y_txs[0].balance if y_txs and y_txs[0].balance is not None else 0.0)
            y_theo = round(y_open + y_credits - y_debits, 2)
            
            y_actual = y_theo
            for t in reversed(y_txs):
                if t.balance is not None:
                    y_actual = round(t.balance, 2)
                    break
            
            diff_y = round(abs(y_actual - y_theo), 2)
            is_rec_y = (diff_y <= self.tolerance)

            yearly_records.append(PeriodicReconciliation(
                period_id=f"YEAR_{y}",
                period_type="YEARLY",
                period_name=f"Anno {y}",
                year=y,
                quarter=None,
                opening_balance=round(y_open, 2),
                total_credits=round(y_credits, 2),
                total_debits=round(y_debits, 2),
                total_cash_withdrawals=round(y_cash, 2),
                total_transfers=round(y_transfers, 2),
                total_fees=round(y_fees, 2),
                theoretical_balance=y_theo,
                actual_balance=y_actual,
                difference=diff_y,
                is_reconciled=is_rec_y,
                transaction_count=len(y_txs),
                unreconciled_reason=f"Divergenza contabile annua di €{diff_y:.2f} per l'anno {y}" if not is_rec_y else None
            ))
            running_bal_yr = y_actual

        # 5. Global Wealth Trajectory & "Quanto avrebbe dovuto avere?"
        first_open = yearly_records[0].opening_balance if yearly_records else (initial_balance or 0.0)
        final_actual = yearly_records[-1].actual_balance if yearly_records else 0.0
        tot_all_credits = sum(r.total_credits for r in yearly_records)
        tot_all_debits = sum(r.total_debits for r in yearly_records)
        tot_all_cash = sum(r.total_cash_withdrawals for r in yearly_records)
        tot_all_transfers = sum(r.total_transfers for r in yearly_records)
        tot_all_fees = sum(r.total_fees for r in yearly_records)
        global_theo = round(first_open + tot_all_credits - tot_all_debits, 2)
        global_diff = round(abs(final_actual - global_theo), 2)

        wealth_decomposition = {
            "initial_balance": first_open,
            "final_actual_balance": final_actual,
            "final_reconstructed_balance": global_theo,
            "discrepancy": global_diff,
            "is_globally_reconciled": (global_diff <= self.tolerance),
            "total_income": tot_all_credits,
            "total_expenses": tot_all_debits,
            "total_cash_withdrawn": tot_all_cash,
            "total_wire_transfers": tot_all_transfers,
            "total_fees_and_taxes": tot_all_fees,
            "net_growth": round(final_actual - first_open, 2),
            "explanation": (
                f"Il patrimonio è passato da €{first_open:,.2f} a €{final_actual:,.2f} "
                f"(variazione netta €{final_actual - first_open:+,.2f}). "
                f"Scomposizione dei flussi: Entrate complessive €{tot_all_credits:,.2f}, "
                f"Uscite totali €{tot_all_debits:,.2f} (di cui Prelievi contanti €{tot_all_cash:,.2f}, "
                f"Bonifici/Giroconti €{tot_all_transfers:,.2f}, Spese/Oneri €{tot_all_fees:,.2f})."
            )
        }

        return {
            "yearly_records": yearly_records,
            "quarterly_records": quarterly_records,
            "wealth_decomposition": wealth_decomposition
        }
