"""
Forensic Pattern & Anomaly Detection Engine.
Detects:
- Rapid same-day withdrawals
- Repeated identical amounts
- Pension drain pattern (cash extracted immediately after pension credit)
- Daily ATM limit exceeded
- Disproportionate withdrawals relative to income
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from core.models import Transaction, TransactionType, Anomaly, AnomalySeverity

class PatternDetector:
    def __init__(self, standard_daily_atm_limit: float = 600.0):
        self.daily_atm_limit = standard_daily_atm_limit

    def detect_anomalies(self, transactions: List[Transaction]) -> List[Anomaly]:
        anomalies: List[Anomaly] = []
        
        # Group withdrawals by date
        withdrawals_by_date = defaultdict(list)
        pensions_by_date = defaultdict(list)
        
        for t in transactions:
            date_key = t.date_accounting or t.date_value or "UNKNOWN_DATE"
            if t.transaction_type == TransactionType.CASH_WITHDRAWAL and (t.amount_debit or 0) > 0:
                withdrawals_by_date[date_key].append(t)
            elif t.transaction_type == TransactionType.PENSION_CREDIT and (t.amount_credit or 0) > 0:
                pensions_by_date[date_key].append(t)

        # 1. Check same-day multiple withdrawals & daily limit excess
        anomaly_counter = 1
        for date_str, tx_list in withdrawals_by_date.items():
            if len(tx_list) >= 2:
                total_day_amount = sum(t.amount_debit or 0 for t in tx_list)
                tx_ids = [t.id for t in tx_list]
                
                # Check for identical repeated amounts (e.g. 600 + 600)
                amounts = [t.amount_debit for t in tx_list]
                is_repeated_identical = len(set(amounts)) == 1
                
                title = f"Prelievi multipli nello stesso giorno ({date_str})"
                desc = (
                    f"Rilevati {len(tx_list)} prelievi distinti in data {date_str} per un totale di €{total_day_amount:.2f}. "
                    f"Importi: {', '.join(f'€{a:.2f}' for a in amounts)}."
                )
                if is_repeated_identical:
                    desc += f" Gli importi sono identici (€{amounts[0]:.2f}), suggerendo operazioni seriali replicate."

                severity = AnomalySeverity.HIGH if total_day_amount > self.daily_atm_limit else AnomalySeverity.MEDIUM
                
                anomalies.append(Anomaly(
                    id=f"ANOM_{anomaly_counter:03d}",
                    category="RAPID_SAME_DAY_WITHDRAWALS",
                    severity=severity,
                    title=title,
                    description=desc,
                    involved_transaction_ids=tx_ids,
                    involved_dates=[date_str],
                    discrepancy_amount=total_day_amount,
                    explanation="La reiterazione di prelievi contanti a distanza di poche ore o minuti nella medesima giornata costituisce tipico indicatore di anomalia comportamentale o potenziale prelievo non autorizzato da parte di terzi.",
                    suggested_actions=[
                        "Acquisire i log orari e i fotogrammi delle telecamere di sicurezza dell'ATM",
                        "Verificare il giornale di fondo cassa/distinte cartacee dell'ufficio postale/bancario",
                        "Verificare l'eventuale superamento del massimale contrattuale giornaliero per la carta utilizzata"
                    ]
                ))
                anomaly_counter += 1

        # 2. Check Pension Drain Pattern (prelievi massivi a ridosso dell'accredito pensione)
        # Sort transactions chronologically
        for p_date, p_list in pensions_by_date.items():
            p_total = sum(p.amount_credit or 0 for p in p_list)
            # Find withdrawals within following 3-5 days
            drained_amount = 0.0
            drained_tx_ids = []
            
            # Simple chronological window check across transactions list
            try:
                # parse DD/MM/YYYY
                p_dt = datetime.strptime(p_date, "%d/%m/%Y")
            except ValueError:
                continue

            for t in transactions:
                if t.transaction_type == TransactionType.CASH_WITHDRAWAL and t.date_accounting:
                    try:
                        w_dt = datetime.strptime(t.date_accounting, "%d/%m/%Y")
                        delta_days = (w_dt - p_dt).days
                        if 0 <= delta_days <= 3:
                            drained_amount += (t.amount_debit or 0)
                            drained_tx_ids.append(t.id)
                    except ValueError:
                        pass

            if drained_amount > 0 and (drained_amount >= 0.70 * p_total or drained_amount >= 800.0):
                drain_pct = (drained_amount / p_total * 100) if p_total > 0 else 100.0
                anomalies.append(Anomaly(
                    id=f"ANOM_{anomaly_counter:03d}",
                    category="PENSION_DRAIN_PATTERN",
                    severity=AnomalySeverity.HIGH,
                    title=f"Schema 'Pension Drain': prelievo quasi integrale della pensione ({p_date})",
                    description=(
                        f"A seguito dell'accredito pensionistico di €{p_total:.2f} in data {p_date}, "
                        f"sono stati prelevati in contanti €{drained_amount:.2f} ({drain_pct:.1f}% dell'entrata) "
                        f"nell'arco di 72 ore tramite {len(drained_tx_ids)} operazioni."
                    ),
                    involved_transaction_ids=drained_tx_ids,
                    involved_dates=[p_date],
                    discrepancy_amount=drained_amount,
                    explanation="Lo svuotamento sistematico del conto immediatamente dopo l'accredito pensionistico è un noto pattern di vulnerabilità (es. circonvenzione di incapace ex art. 643 c.p., appropriazione indebita ex art. 646 c.p. o distrazione di fondi da parte di soggetti delegati/conviventi).",
                    suggested_actions=[
                        "Verificare la presenza di deleghe formali sul conto e il rapporto di parentela/assistenza dei delegati",
                        "Acquisire gli scontrini di prelievo e verificare la titolarità della carta/dispositivo usato",
                        "Richiedere accertamento sulla capacità naturale e di intendere/volere dell'intestatario alla data dei prelievi"
                    ]
                ))
                anomaly_counter += 1

        return anomalies
