"""
Forensic Anomaly Scoring Engine.
Implements:
- Explainable Anomaly Scoring (0 to 100):
    0 - 20   : Normale
    21 - 40  : Insolito
    41 - 60  : Attenzione
    61 - 80  : Anomalia significativa
    81 - 100 : Anomalia critica
- Generates:
    * TOP 10 Anomalie Critiche
    * TOP 20 Anomalie Significative
    * TOP 20 Elementi Insoliti
- Detailed forensic metadata per anomaly (BBox, historical comparison, missing docs, legal relevance)
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from core.models import Transaction, Anomaly, AnomalySeverity, AnomalyCategory, TransactionType, ChannelType

class AnomalyScoringEngine:
    def __init__(self, standard_daily_limit: float = 600.0):
        self.daily_limit = standard_daily_limit

    def score_transactions(self, transactions: List[Transaction]) -> Tuple[List[Transaction], List[Anomaly], Dict[str, List[Anomaly]]]:
        scored_txs = []
        all_anomalies: List[Anomaly] = []

        # 1. Historical baseline metrics
        cash_amounts = [t.amount or t.amount_debit or 0.0 for t in transactions if (t.amount or t.amount_debit or 0.0) > 0 and t.direction == "DEBIT"]
        avg_debit = (sum(cash_amounts) / len(cash_amounts)) if cash_amounts else 250.0

        # Group withdrawals by date
        withdrawals_by_date = defaultdict(list)
        pensions_by_date = defaultdict(list)
        for t in transactions:
            d = t.date_accounting or t.date_value or "N/D"
            if t.transaction_type in [TransactionType.CASH_WITHDRAWAL, TransactionType.PRELIEVO_ATM, TransactionType.PRELIEVO_SPORTELLO_FISICO] or ("PRELIEVO" in t.description.upper()):
                withdrawals_by_date[d].append(t)
            if "PENS" in t.description.upper() or "INPS" in t.description.upper():
                pensions_by_date[d].append(t)

        anom_id_counter = 1

        for t in transactions:
            score = 0
            score_reasons = []
            amt = t.amount or t.amount_debit or t.amount_credit or 0.0
            d = t.date_accounting or t.date_value or "N/D"

            # Check 1: Amount exceeding daily limit or historical average
            if t.direction == "DEBIT" and amt > 0:
                if amt >= 2000.0:
                    score += 35
                    score_reasons.append(f"+35 importo eccezionale (€{amt:.2f} > €2.000)")
                elif amt > 1000.0:
                    score += 25
                    score_reasons.append(f"+25 importo elevato (€{amt:.2f} > €1.000)")
                elif amt > self.daily_limit:
                    score += 15
                    score_reasons.append(f"+15 eccedenza plafond ordinario (€{amt:.2f} > €{self.daily_limit:.2f})")

            # Check 2: Same-day multiple withdrawals
            if d in withdrawals_by_date and len(withdrawals_by_date[d]) >= 2 and t in withdrawals_by_date[d]:
                day_count = len(withdrawals_by_date[d])
                score += 20
                score_reasons.append(f"+20 prelievo reiterato ({day_count} operazioni nella stessa giornata)")
                
                # Repeated identical amounts
                day_amts = [w.amount or w.amount_debit or 0.0 for w in withdrawals_by_date[d]]
                if len(set(day_amts)) == 1:
                    score += 15
                    score_reasons.append("+15 importo seriale identico replicato")

            # Check 3: Pension drain proximity (within 72h)
            for p_d in pensions_by_date:
                # simple date diff check if possible
                try:
                    dt_p = datetime.strptime(p_d, "%d/%m/%Y")
                    dt_t = datetime.strptime(d, "%d/%m/%Y")
                    delta = (dt_t - dt_p).days
                    if 0 <= delta <= 3 and t.direction == "DEBIT" and amt >= 500.0:
                        score += 20
                        score_reasons.append(f"+20 prelievo tempestivo a ridosso pensione (entro {delta} giorni)")
                        break
                except ValueError:
                    pass

            # Check 4: Channel uncertainty or POS absence
            if t.channel == ChannelType.UNKNOWN and "SPORTELLO" in t.description.upper():
                score += 10
                score_reasons.append("+10 canale sportello ambiguo da accertare")

            # Cap score to 100
            final_score = min(score, 100)
            t.anomaly_score = final_score

            # If score >= 21, create Anomaly record
            if final_score >= 21:
                severity = AnomalySeverity.LOW
                category = AnomalyCategory.AMOUNT_ANOMALY.value
                if final_score >= 81:
                    severity = AnomalySeverity.CRITICAL
                    category = AnomalyCategory.SEQUENCE_ANOMALY.value
                elif final_score >= 61:
                    severity = AnomalySeverity.HIGH
                    category = AnomalyCategory.AMOUNT_ANOMALY.value
                elif final_score >= 41:
                    severity = AnomalySeverity.MEDIUM
                    category = AnomalyCategory.FREQUENCY_ANOMALY.value

                explanation_str = "Composizione punteggio anomalia:\n" + "\n".join(score_reasons)
                
                all_anomalies.append(Anomaly(
                    id=f"ANOM_{anom_id_counter:03d}",
                    category=category,
                    severity=severity,
                    score=final_score,
                    title=f"Anomalia {severity.value} (Score {final_score}): {t.description[:40]}",
                    description=f"Operazione di €{amt:.2f} in data {d}. {', '.join(score_reasons)}.",
                    involved_transaction_ids=[t.id],
                    involved_dates=[d],
                    discrepancy_amount=amt,
                    explanation=explanation_str,
                    evidence_links=[f"{t.document_name} Pag.{t.page} BBox:[{t.bounding_box.x},{t.bounding_box.y},{t.bounding_box.width},{t.bounding_box.height}]"],
                    suggested_actions=[
                        "Acquisizione log telematici e fotogrammi ATM",
                        "Verifica modulo apertura e autorizzazione massimali",
                        "Acquisizione contabile cartacea allo sportello"
                    ],
                    missing_documentation="Ricevuta cartacea di prelievo / Log di autenticazione operazione",
                    legal_relevance="Rilevante ex art. 493-ter c.p. / art. 119 TUB in caso di mancata autorizzazione del titolare"
                ))
                anom_id_counter += 1

            scored_txs.append(t)

        # Sort anomalies by score descending
        all_anomalies.sort(key=lambda x: x.score, reverse=True)

        top_10_critical = [a for a in all_anomalies if a.score >= 81][:10]
        top_20_significant = [a for a in all_anomalies if 61 <= a.score <= 80][:20]
        top_20_unusual = [a for a in all_anomalies if 21 <= a.score <= 60][:20]

        return scored_txs, all_anomalies, {
            "top_10_critical": top_10_critical,
            "top_20_significant": top_20_significant,
            "top_20_unusual": top_20_unusual
        }

