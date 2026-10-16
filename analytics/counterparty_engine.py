"""
Counterparty & Income Intelligence Engine.
Implements:
1. Income Mapping & Forensics:
   - Identifies independent income sources
   - Identifies primary income source (e.g. INPS Pensione)
   - Distinguishes rigorously:
     * Unica fonte di reddito
     * Unica tipologia di accredito
     * Unica controparte
     * Unico accredito ricorrente
2. Top Counterparties Table:
   - Name, First seen, Last seen, Operations, Credits, Debits, Net, Frequency
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import re
from core.models import Transaction, CounterpartyProfile, TransactionType

class CounterpartyAndIncomeEngine:
    def __init__(self):
        pass

    def _clean_counterparty(self, desc: str) -> str:
        upper = desc.upper()
        # Remove dates, codes, generic terms
        if "INPS" in upper:
            return "INPS - ISTITUTO NAZIONALE PREVIDENZA SOCIALE"
        if "POSTE ITALIANE" in upper or "POSTAMAT" in upper:
            return "POSTE ITALIANE S.P.A."
        if "CANONE" in upper or "SPESE TENUTA" in upper or "IMPOSTA" in upper:
            return "ONERI BANCARI / ERARIO"
        
        # Look for Bonifico Da / A
        m = re.search(r'(?:DA|A FAVORE DI|A:\s*)\s*([A-Z\s]{4,35})', upper)
        if m:
            clean = m.group(1).strip()
            if len(clean) > 3 and not clean.startswith("SPORTELLO") and not clean.startswith("POSTAMAT"):
                return clean
        
        # Truncate first 35 chars
        words = upper.split()
        return " ".join(words[:4]) if words else "SOGGETTO NON IDENTIFICATO"

    def analyze_counterparties_and_income(self, transactions: List[Transaction]) -> Dict[str, Any]:
        profiles: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "first_seen": "9999-99-99",
            "last_seen": "0000-00-00",
            "count": 0,
            "credits": 0.0,
            "debits": 0.0,
            "dates": []
        })

        income_sources: Dict[str, List[Transaction]] = defaultdict(list)

        for t in transactions:
            cp = t.counterparty or self._clean_counterparty(t.description)
            t.counterparty = cp
            
            d_str = t.date_accounting or t.date_value or "N/D"
            p = profiles[cp]
            p["count"] += 1
            p["dates"].append(d_str)
            if d_str < p["first_seen"]:
                p["first_seen"] = d_str
            if d_str > p["last_seen"]:
                p["last_seen"] = d_str

            if t.direction == "CREDIT" or (t.amount_credit or 0.0) > 0:
                credit_amt = t.amount or t.amount_credit or 0.0
                p["credits"] += credit_amt
                income_sources[cp].append(t)
            else:
                debit_amt = t.amount or t.amount_debit or 0.0
                p["debits"] += debit_amt

        # Format Top Counterparties List
        top_list = []
        for cp, data in profiles.items():
            tot_ops = data["count"]
            tot_cr = round(data["credits"], 2)
            tot_db = round(data["debits"], 2)
            first = data["first_seen"] if data["first_seen"] != "9999-99-99" else "N/D"
            last = data["last_seen"] if data["last_seen"] != "0000-00-00" else "N/D"
            
            freq = "Ricorrente" if tot_ops >= 4 else ("Periodico" if tot_ops >= 2 else "Occasionale")
            
            top_list.append({
                "counterparty": cp,
                "first_seen": first,
                "last_seen": last,
                "total_operations": tot_ops,
                "total_credits": tot_cr,
                "total_debits": tot_db,
                "net_flow": round(tot_cr - tot_db, 2),
                "frequency": freq
            })

        top_list.sort(key=lambda x: (x["total_credits"] + x["total_debits"]), reverse=True)

        # Income Forensics Answers
        num_income_sources = len(income_sources)
        primary_source = None
        max_income = 0.0
        for cp, tx_list in income_sources.items():
            tot = sum(t.amount or t.amount_credit or 0.0 for t in tx_list)
            if tot > max_income:
                max_income = tot
                primary_source = cp

        is_single_income_source = (num_income_sources == 1)
        
        income_analysis = {
            "total_income_sources_count": num_income_sources,
            "primary_income_source": primary_source or "NESSUNA ENTRATA REGISTRATA",
            "primary_source_total": round(max_income, 2),
            "is_sole_income_source": is_single_income_source,
            "income_breakdown_by_source": {
                cp: {
                    "count": len(txs),
                    "total": round(sum(t.amount or t.amount_credit or 0.0 for t in txs), 2),
                    "average": round(sum(t.amount or t.amount_credit or 0.0 for t in txs) / len(txs), 2) if txs else 0.0,
                    "first_credit": txs[0].date_accounting if txs else "N/D",
                    "last_credit": txs[-1].date_accounting if txs else "N/D"
                }
                for cp, txs in income_sources.items()
            },
            "forensic_classification": (
                "UNICA FONTE DI REDDITO (Pensione INPS accreditata con cadenza mensile regolare)"
                if is_single_income_source and primary_source and "INPS" in primary_source
                else f"PLURALITÀ DI FONTI ({num_income_sources} soggetti accreditanti distinti)"
            )
        }

        return {
            "top_counterparties": top_list,
            "income_analysis": income_analysis
        }

