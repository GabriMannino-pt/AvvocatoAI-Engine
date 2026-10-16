"""
Document Request Engine.
Generates structured legal document requisition requests to acquire indispensable evidentiary records
from Banks, Poste Italiane, INPS, delegates, or judicial authorities.
"""
from typing import List, Dict, Any
from core.models import Transaction, Anomaly, DocumentRequest

class DocumentRequestEngine:
    def generate_requests(self, transactions: List[Transaction], anomalies: List[Anomaly]) -> List[DocumentRequest]:
        requests: List[DocumentRequest] = []
        req_counter = 1
        
        has_atm = any(t.channel.value == "ATM" for t in transactions if hasattr(t.channel, "value"))
        has_anomalies = len(anomalies) > 0
        
        # 1. Art. 119 TUB: Copia integrale distinte e giornale di cassa
        requests.append(DocumentRequest(
            id=f"REQ_{req_counter:03d}",
            document_name="Copia integrale contrattuale, deleghe e distinte contabili delle operazioni",
            subject_holder="Poste Italiane S.p.A. / Istituto di Credito emittente",
            purpose="Verificare l'esistenza di deleghe formali a favore di terzi, limitazioni di firma e condizioni contrattuali applicabili",
            fact_to_prove="Verificare se le operazioni siano state disposte personalmente dal titolare o da procuratore/delegato",
            priority="CRITICAL",
            legal_basis="Art. 119, comma 4, D.Lgs. 385/1993 (Testo Unico Bancario)"
        ))
        req_counter += 1

        # 2. Log ATM e videoriprese di sicurezza
        if has_atm and has_anomalies:
            requests.append(DocumentRequest(
                id=f"REQ_{req_counter:03d}",
                document_name="Log di audit del terminale ATM e registrazioni video delle telecamere di sorveglianza",
                subject_holder="Ufficio Sicurezza e Antifrode Poste Italiane / Banca",
                purpose="Identificare con certezza visiva l'esecutore materiale dell'inserimento della carta e della digitazione del PIN",
                fact_to_prove="Dimostrare l'estraneità fisica del titolare del conto rispetto ai prelievi contestati",
                priority="URGENT (Rischio sovrascrittura registrazioni)",
                legal_basis="Art. 391-quater c.p.p. (Indagini difensive) e Provvedimento Garante Privacy 8 aprile 2010"
            ))
            req_counter += 1

        # 3. Certificazione e prospetto analitico liquidazione pensione (Modello ObisM)
        has_pension = any(a.category == "PENSION_DRAIN_PATTERN" for a in anomalies)
        if has_pension:
            requests.append(DocumentRequest(
                id=f"REQ_{req_counter:03d}",
                document_name="Prospetto analitico liquidazione pensione (Modello ObisM) e storico accrediti con indicazione del codice fiscale beneficiario",
                subject_holder="INPS - Direzione Provinciale competente",
                purpose="Riscontrare la perfetta corrispondenza tra l'importo netto spettante e gli accrediti registrati sull'estratto conto, certificando la titolarità esclusiva della provvista ex art. 1298 c.c.",
                fact_to_prove="Attestare la natura strettamente previdenziale, alimentare ed esclusiva delle somme accreditate e sottratte",
                priority="HIGH",
                legal_basis="D.P.R. 445/2000 e Legge 241/1990 (Accesso agli atti amministrativi)"
            ))
            req_counter += 1

        # 4. Modulo richiesta, emissione e ricevuta di consegna della Carta Postamat ..6525 e della carta aggiuntiva
        requests.append(DocumentRequest(
            id=f"REQ_{req_counter:03d}",
            document_name="Moduli di emissione, attivazione e verbali di consegna della Carta Postamat n. ...6525 e della seconda carta aggiuntiva",
            subject_holder="Poste Italiane S.p.A. - Archivio Contratti",
            purpose="Identificare con certezza documentale a quale dei cointestatari o delegati sia stata formalmente assegnata e consegnata la carta utilizzata per i prelievi",
            fact_to_prove="Dimostrare l'affidamento fiduciario e la materiale detenzione dello strumento di pagamento in capo a un soggetto determinato",
            priority="CRITICAL",
            legal_basis="Art. 119, comma 4, D.Lgs. 385/1993 (TUB)"
        ))
        req_counter += 1

        # 5. Rendiconto analitico delle spese e pezze d'appoggio ex art. 1713 c.c.
        if has_atm:
            requests.append(DocumentRequest(
                id=f"REQ_{req_counter:03d}",
                document_name="Rendiconto dettagliato delle spese sostenute e allegazione delle pezze giustificative (scontrini parlanti, fatture, ricevute)",
                subject_holder="Detentore fiduciario della carta / Delegato all'operatività",
                purpose="Verificare se le somme prelevate in contanti siano state effettivamente impiegate nell'esclusivo interesse dei titolari del conto",
                fact_to_prove="Accertare l'ammontare delle somme distratte o ingiustificate ai fini dell'azione di restituzione ex art. 1713 e 2033 c.c.",
                priority="HIGH",
                legal_basis="Art. 1713 c.c., Art. 263 c.p.c. (Procedimento di rendiconto)"
            ))
            req_counter += 1

        return requests

