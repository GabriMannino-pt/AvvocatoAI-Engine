"""
Authorization vs Actual Execution Comparator.
Cross-references delegated or authorized spending limits against executed operations.
Enforces the forensic rule: NEVER unilaterally declare a crime, but flag POSSIBLE EXCESS / UNAUTHORIZED TRANSACTION
and output the exact evidentiary documents required to establish legal responsibility.
"""
from typing import List, Dict, Any, Optional
from core.models import Transaction, Anomaly, AnomalySeverity

class AuthorizationComparator:
    def compare_authorization(
        self,
        transactions: List[Transaction],
        authorized_amount_per_event: float,
        authorized_date: Optional[str] = None,
        authorized_subject: Optional[str] = None,
        delegation_scope: str = "PRELIEVO CONTANTE ORDINARIO"
    ) -> List[Anomaly]:
        """
        Compares authorized spending against transactions.
        e.g. Authorized €600.00, but executed €600.00 + €600.00 -> Excess flagged.
        """
        results: List[Anomaly] = []
        
        # Filter relevant transactions
        relevant_txs = [t for t in transactions if (t.amount_debit or 0) > 0]
        if authorized_date:
            relevant_txs = [t for t in relevant_txs if t.date_accounting == authorized_date or t.date_value == authorized_date]
        
        total_executed = sum(t.amount_debit or 0 for t in relevant_txs)
        
        if total_executed > authorized_amount_per_event:
            excess_amount = round(total_executed - authorized_amount_per_event, 2)
            tx_ids = [t.id for t in relevant_txs]
            
            anomaly = Anomaly(
                id="AUTH_EXCESS_001",
                category="POSSIBLE_EXCESS_OR_UNAUTHORIZED_TRANSACTION",
                severity=AnomalySeverity.CRITICAL,
                title=f"Possibile eccedenza rispetto all'autorizzazione nota (+€{excess_amount:.2f})",
                description=(
                    f"A fronte di una autorizzazione documentata o presunta di €{authorized_amount_per_event:.2f}, "
                    f"risultano eseguite operazioni di prelievo/addebito per complessivi €{total_executed:.2f} "
                    f"(eccedenza di €{excess_amount:.2f}). "
                    f"Operazioni coinvolte: {len(relevant_txs)} distinte transazioni."
                ),
                involved_transaction_ids=tx_ids,
                involved_dates=[t.date_accounting for t in relevant_txs if t.date_accounting],
                discrepancy_amount=excess_amount,
                explanation=(
                    "Il riscontro di uscite finanziarie eccedenti il plafond autorizzato integra un'ipotesi tecnica "
                    "di operazione non autorizzata o abuso di delega / mandato (art. 1710 c.c. e art. 646 c.p.). "
                    "Tuttavia, prima di formulare conclusioni definitive in sede giudiziaria, è indispensabile acquisire "
                    "la prova materiale dell'esecutore materiale dell'eccedenza."
                ),
                suggested_actions=[
                    "Acquisire il testo formale della procura/delega e le quietanze sottoscritte",
                    "Richiedere a Poste Italiane/Banca i log telematici e le registrazioni di videosorveglianza dell'orario del secondo prelievo",
                    "Diffidare l'istituto di credito ex art. 119 TUB per l'esibizione di copia integrale della distinta di cassa o log ATM",
                    "Disconoscere formalmente l'operazione eccedente ex D.Lgs. 11/2010 (PSD2)"
                ]
            )
            results.append(anomaly)
            
        return results
