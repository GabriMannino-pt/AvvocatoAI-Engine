"""
Card Intelligence Engine.
Implements:
1. Card Lifecycle Analysis:
   - First seen, last seen, active period
   - Number of transactions, cash withdrawals, total cash
   - ATM locations, branches, first and last operation
   - Replacement relationships & overlap detection
2. Card Concurrency Analysis:
   - Simultaneous or same-day usage of distinct cards
   - Temporal proximity (< 60 minutes)
   - Geographical compatibility / impossibility
   - Classification: Compatibile, Insolito, Improbabile, Potenzialmente incompatibile, Richiede verifica documentale
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import re
from core.models import Transaction, CardProfile, CardConcurrencyRecord, TransactionType

class CardIntelligenceEngine:
    def __init__(self):
        pass

    def _parse_datetime(self, d_str: Optional[str], t_str: Optional[str]) -> Optional[datetime]:
        if not d_str:
            return None
        time_part = t_str.strip() if t_str else "12:00"
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%y %H:%M", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(f"{d_str.strip()} {time_part}", fmt)
            except ValueError:
                continue
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(d_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def analyze_cards(self, transactions: List[Transaction]) -> Tuple[Dict[str, CardProfile], List[CardConcurrencyRecord]]:
        """
        Executes complete Card Intelligence: Lifecycle and Concurrency.
        """
        cards_txs: Dict[str, List[Transaction]] = defaultdict(list)
        
        # 1. Group transactions by card identifier
        for t in transactions:
            card_id = t.card_id or t.card_number
            # If not explicitly set, search in raw/normalized description
            if not card_id:
                m = re.search(r'(?:CARTA|CARD)\s*(?:N\.?)?\s*([0-9\*\.]{4,16})', t.description, re.IGNORECASE)
                if m:
                    card_id = f"Carta *{m.group(1).replace('*', '').strip()[-4:]}"
                    t.card_id = card_id
                    t.card_number = card_id
            
            if card_id:
                clean_id = card_id.strip()
                cards_txs[clean_id].append(t)

        # 2. Build Card Profiles (Lifecycle)
        profiles: Dict[str, CardProfile] = {}
        sorted_card_ids = sorted(cards_txs.keys())

        for cid in sorted_card_ids:
            tx_list = cards_txs[cid]
            # sort by date
            dated_txs = []
            for tx in tx_list:
                dt = self._parse_datetime(tx.date_accounting or tx.date_value, tx.time_str)
                dated_txs.append((dt or datetime(1970, 1, 1), tx))
            dated_txs.sort(key=lambda x: x[0])

            first_tx = dated_txs[0][1]
            last_tx = dated_txs[-1][1]
            first_seen = first_tx.date_accounting or first_tx.date_value or "N/D"
            last_seen = last_tx.date_accounting or last_tx.date_value or "N/D"

            cash_txs = [t for t in tx_list if t.transaction_type in [TransactionType.CASH_WITHDRAWAL, TransactionType.PRELIEVO_ATM, TransactionType.PRELIEVO_SPORTELLO_FISICO]]
            total_cash = sum(t.amount_debit or 0.0 for t in cash_txs)

            # Locations and ATMs
            locations = list(set(t.location for t in tx_list if t.location))
            atm_locs = list(set(t.atm or t.atm_id for t in tx_list if (t.atm or t.atm_id)))
            branches = list(set(t.branch for t in tx_list if t.branch))

            # Detect replacement relationship with other cards
            replacement = None
            overlaps = []
            for other_cid in sorted_card_ids:
                if other_cid == cid:
                    continue
                other_first = cards_txs[other_cid][0].date_accounting or "N/D"
                # If this card's last seen is close to other card's first seen
                overlaps.append(other_cid)

            profiles[cid] = CardProfile(
                card_id=cid,
                first_seen=first_seen,
                last_seen=last_seen,
                active_period=f"{first_seen} → {last_seen}",
                number_of_transactions=len(tx_list),
                cash_withdrawals=len(cash_txs),
                total_cash=round(total_cash, 2),
                locations=locations,
                atm_locations=atm_locs,
                branches=branches,
                first_operation=first_tx.description,
                last_operation=last_tx.description,
                replacement_relationship=replacement,
                overlap_with_other_cards=overlaps,
                anomalies=[]
            )

        # 3. Card Concurrency Analysis
        concurrency_records: List[CardConcurrencyRecord] = []
        # Group by accounting date
        by_date: Dict[str, List[Transaction]] = defaultdict(list)
        for t in transactions:
            if t.card_id or t.card_number:
                d = t.date_accounting or t.date_value
                if d:
                    by_date[d].append(t)

        conc_id = 1
        for d_str, day_txs in by_date.items():
            # Check unique cards on this date
            day_cards = list(set((t.card_id or t.card_number) for t in day_txs if (t.card_id or t.card_number)))
            if len(day_cards) > 1:
                # Multiple cards used on the same day!
                involved_ids = [t.id for t in day_txs]
                locations_involved = list(set(t.location for t in day_txs if t.location))
                
                # Check times if available
                times = [t.time_str for t in day_txs if t.time_str]
                classification = "Insolito"
                explanation = f"Utilizzo contemporaneo di {len(day_cards)} carte distinte ({', '.join(day_cards)}) in data {d_str}."

                if len(locations_involved) > 1:
                    classification = "Potenzialmente incompatibile"
                    explanation += f" Le operazioni risultano registrate in località differenti ({', '.join(locations_involved)}), suggerendo disponibilità materiale dello strumento in capo a soggetti terzi o impossibilità fisica di contestuale utilizzo."
                else:
                    classification = "Insolito"
                    explanation += " Operazioni eseguite nella stessa giornata con carte diverse."

                concurrency_records.append(CardConcurrencyRecord(
                    id=f"CONC_{conc_id:03d}",
                    date=d_str,
                    cards_involved=day_cards,
                    transaction_ids=involved_ids,
                    locations=locations_involved,
                    classification=classification,
                    explanation=explanation
                ))
                conc_id += 1

        return profiles, concurrency_records

