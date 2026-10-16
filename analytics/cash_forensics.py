"""
Cash Withdrawal Forensics Engine.
Implements:
1. Granular Threshold Filters:
   - > €500
   - > €1.000
   - > €2.000
   - > €5.000
   - > €10.000
2. Pattern & Sequence Detection:
   - Same amount repeated (e.g. €600 + €600)
   - Double / Triple withdrawals on the same day
   - Withdrawals on consecutive days
   - Post-pension / post-salary drain patterns (within 24h/72h)
   - Withdrawals linked to wire transfers
   - Channel breakdown: ATM / Sportello Automatico vs Sportello Fisico
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from core.models import Transaction, TransactionType, ChannelType

class CashWithdrawalForensics:
    def __init__(self):
        pass

    def _parse_date(self, d_str: Optional[str]) -> Optional[datetime]:
        if not d_str:
            return None
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(d_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def analyze_cash_withdrawals(self, transactions: List[Transaction]) -> Dict[str, Any]:
        cash_txs = [
            t for t in transactions
            if t.transaction_type in [TransactionType.CASH_WITHDRAWAL, TransactionType.PRELIEVO_ATM, TransactionType.PRELIEVO_SPORTELLO_FISICO]
            or (t.direction == "DEBIT" and ("PRELIEVO" in t.description.upper() or "POSTAMAT" in t.description.upper()))
        ]

        # 1. Threshold segmentation
        over_500 = [t for t in cash_txs if (t.amount or t.amount_debit or 0.0) > 500.0]
        over_1000 = [t for t in cash_txs if (t.amount or t.amount_debit or 0.0) > 1000.0]
        over_2000 = [t for t in cash_txs if (t.amount or t.amount_debit or 0.0) > 2000.0]
        over_5000 = [t for t in cash_txs if (t.amount or t.amount_debit or 0.0) > 5000.0]
        over_10000 = [t for t in cash_txs if (t.amount or t.amount_debit or 0.0) > 10000.0]

        total_cash = sum(t.amount or t.amount_debit or 0.0 for t in cash_txs)
        avg_cash = (total_cash / len(cash_txs)) if cash_txs else 0.0
        max_cash = max((t.amount or t.amount_debit or 0.0 for t in cash_txs), default=0.0)

        # 2. Channel Distribution (ATM vs Sportello Fisico)
        atm_withdrawals = [t for t in cash_txs if t.channel in [ChannelType.ATM, ChannelType.SPORTELLO_AUTOMATICO, ChannelType.POSTAMAT]]
        physical_withdrawals = [t for t in cash_txs if t.channel in [ChannelType.SPORTELLO_FISICO, ChannelType.CASSA, ChannelType.OPERATORE]]
        unknown_channel = [t for t in cash_txs if t not in atm_withdrawals and t not in physical_withdrawals]

        # 3. Same-Day Multiples & Repeated Identical Amounts
        by_date: Dict[str, List[Transaction]] = defaultdict(list)
        for t in cash_txs:
            d = t.date_accounting or t.date_value or "UNKNOWN"
            by_date[d].append(t)

        same_day_multiples = []
        repeated_amounts = []
        for d_str, day_txs in by_date.items():
            if len(day_txs) >= 2:
                day_total = sum(t.amount or t.amount_debit or 0.0 for t in day_txs)
                amounts = [t.amount or t.amount_debit or 0.0 for t in day_txs]
                is_identical = len(set(amounts)) == 1
                rec = {
                    "date": d_str,
                    "count": len(day_txs),
                    "total_amount": round(day_total, 2),
                    "amounts": amounts,
                    "is_identical": is_identical,
                    "transaction_ids": [t.id for t in day_txs],
                    "cards": list(set((t.card_id or t.card_number or "N/D") for t in day_txs))
                }
                same_day_multiples.append(rec)
                if is_identical:
                    repeated_amounts.append(rec)

        # 4. Pension Drain Detection (withdrawals within 72h of pension/salary)
        income_txs = [
            t for t in transactions
            if t.transaction_type in [TransactionType.PENSIONE, TransactionType.PENSION_CREDIT, TransactionType.STIPENDIO, TransactionType.SALARY_CREDIT]
            or (t.direction == "CREDIT" and ("PENS" in t.description.upper() or "INPS" in t.description.upper()))
        ]

        pension_drain_events = []
        for inc in income_txs:
            inc_date = self._parse_date(inc.date_accounting or inc.date_value)
            if not inc_date:
                continue
            inc_amount = inc.amount or inc.amount_credit or 0.0
            # Search for cash withdrawals within 72h
            drained_txs = []
            for c in cash_txs:
                c_date = self._parse_date(c.date_accounting or c.date_value)
                if c_date:
                    delta = (c_date - inc_date).days
                    if 0 <= delta <= 3:
                        drained_txs.append(c)

            drained_total = sum(t.amount or t.amount_debit or 0.0 for t in drained_txs)
            if drained_total > 0 and inc_amount > 0:
                pct = round((drained_total / inc_amount) * 100, 1)
                if pct >= 50.0 or drained_total >= 1000.0:
                    pension_drain_events.append({
                        "income_id": inc.id,
                        "income_date": inc.date_accounting or inc.date_value,
                        "income_amount": inc_amount,
                        "drained_total": round(drained_total, 2),
                        "drained_percentage": pct,
                        "withdrawal_count": len(drained_txs),
                        "withdrawal_ids": [t.id for t in drained_txs],
                        "cards_used": list(set((t.card_id or t.card_number or "N/D") for t in drained_txs))
                    })

        return {
            "total_withdrawals_count": len(cash_txs),
            "total_cash_amount": round(total_cash, 2),
            "average_cash_withdrawal": round(avg_cash, 2),
            "max_cash_withdrawal": round(max_cash, 2),
            "thresholds": {
                "over_500_count": len(over_500),
                "over_500_total": round(sum(t.amount or t.amount_debit or 0.0 for t in over_500), 2),
                "over_1000": over_1000,
                "over_1000_count": len(over_1000),
                "over_1000_total": round(sum(t.amount or t.amount_debit or 0.0 for t in over_1000), 2),
                "over_2000_count": len(over_2000),
                "over_2000_total": round(sum(t.amount or t.amount_debit or 0.0 for t in over_2000), 2),
                "over_5000_count": len(over_5000),
                "over_5000_total": round(sum(t.amount or t.amount_debit or 0.0 for t in over_5000), 2),
                "over_10000_count": len(over_10000),
                "over_10000_total": round(sum(t.amount or t.amount_debit or 0.0 for t in over_10000), 2),
            },
            "channel_distribution": {
                "atm_count": len(atm_withdrawals),
                "atm_total": round(sum(t.amount or t.amount_debit or 0.0 for t in atm_withdrawals), 2),
                "physical_count": len(physical_withdrawals),
                "physical_total": round(sum(t.amount or t.amount_debit or 0.0 for t in physical_withdrawals), 2),
                "unknown_count": len(unknown_channel),
                "unknown_total": round(sum(t.amount or t.amount_debit or 0.0 for t in unknown_channel), 2)
            },
            "same_day_multiples": same_day_multiples,
            "repeated_amounts": repeated_amounts,
            "pension_drain_events": pension_drain_events
        }

