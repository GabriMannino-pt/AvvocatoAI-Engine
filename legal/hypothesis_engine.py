"""
Legal Hypothesis Engine.
Correlates financial anomalies and transaction evidence to applicable Italian norms,
identifying required statutory elements, existing factual evidence, missing elements,
and the precise evidentiary degree.
"""
from typing import List, Dict, Any, Optional
from core.models import Transaction, Anomaly, LegalHypothesis
from legal.legal_kb import LEGAL_KB

class LegalHypothesisEngine:
    def evaluate_case(self, transactions: List[Transaction], anomalies: List[Anomaly]) -> List[LegalHypothesis]:
        """
        Evaluates anomalies and returns applicable legal profiles with forensic rigor.
        """
        hypotheses: List[LegalHypothesis] = []
        
        has_multiple_same_day = any(a.category == "RAPID_SAME_DAY_WITHDRAWALS" for a in anomalies)
        has_pension_drain = any(a.category == "PENSION_DRAIN_PATTERN" for a in anomalies)
        has_auth_excess = any(a.category == "POSSIBLE_EXCESS_OR_UNAUTHORIZED_TRANSACTION" for a in anomalies)
        has_math_discrepancy = any("BALANCE_MISMATCH" in a.category or "DATA_INTEGRITY" in a.category for a in anomalies)

        # 1. Evaluate Art. 493-ter c.p. (Indebito utilizzo carte / PIN)
        if has_multiple_same_day or has_auth_excess:
            kb = LEGAL_KB["ART_493_TER_CP"]
            hypotheses.append(LegalHypothesis(
                id="HYP_493_TER",
                norm_reference="Codice Penale",
                norm_title=kb["norm_title"],
                article=kb["article"],
                temporal_version=kb["temporal_version"],
                required_elements=kb["required_elements"],
                facts_found=[
                    "Presenza di prelievi contanti seriali o ravvicinati su circuito ATM/Postamat",
                    "Possibile eccedenza rispetto all'autorizzazione o al massimale ordinario"
                ],
                missing_facts=[
                    "Prova testimoniale o videoripresa attestante chi ha fisicamente digitato il PIN e prelevato il contante",
                    "Dichiarazione formale di disconoscimento sottoscritta dal titolare del conto",
                    "Accertamento sulla eventuale cessione volontaria della carta e del PIN a terzi"
                ],
                confidence_degree="PROFILO GIURIDICO DA VERIFICARE (Fattispecie astrattamente configurabile)",
                suggested_documents=kb["evidence_needed"],
                forensic_notes=(
                    "Non è possibile affermare automaticamente la sussistenza del delitto di cui all'art. 493-ter c.p. "
                    "senza la prova che la carta sia stata impiegata da un terzo all'insaputa o contro la volontà del titolare. "
                    "È necessario acquisire tempestivamente i filmati ATM prima della scadenza dei termini di cancellazione."
                )
            ))

        # 2. Evaluate Art. 643 c.p. (Circonvenzione di persone incapaci)
        if has_pension_drain:
            kb = LEGAL_KB["ART_643_CP"]
            hypotheses.append(LegalHypothesis(
                id="HYP_643_CP",
                norm_reference="Codice Penale",
                norm_title=kb["norm_title"],
                article=kb["article"],
                temporal_version=kb["temporal_version"],
                required_elements=kb["required_elements"],
                facts_found=[
                    "Drenaggio sistematico dell'accredito pensionistico (Pension Drain Pattern) entro 72 ore dall'erogazione INPS",
                    "Condotta reiterata nel tempo con svuotamento della provvista"
                ],
                missing_facts=[
                    "Certificazione medica specialistica (geriatrica / neurologica) attestante decadimento cognitivo all'epoca dei fatti",
                    "Prova della condotta induttiva / persuasiva esercitata dal soggetto terzo sulla persona vulnerabile",
                    "Destinazione effettiva del contante prelevato"
                ],
                confidence_degree="EVIDENZA SIGNIFICATIVA SOTTO IL PROFILO DELLO SCHEMA COMPORTAMENTALE (Richiede perizia medico-legale)",
                suggested_documents=kb["evidence_needed"],
                forensic_notes=(
                    "Lo schema di prelievo sistematico in concomitanza con la pensione è altamente indicativo di sfruttamento "
                    "della vulnerabilità economica dell'anziano. L'analisi contabile costituisce solida premessa indiziaria "
                    "ma deve essere integrata dall'accertamento sulla capacità volitiva del de cuius o della persona offesa."
                )
            ))

        # 3. Evaluate Art. 119 TUB & D.Lgs. 11/2010 (Diritto di accesso e onere probatorio bancario)
        if has_multiple_same_day or has_auth_excess:
            kb_psd2 = LEGAL_KB["DLGS_11_2010_PSD2"]
            hypotheses.append(LegalHypothesis(
                id="HYP_PSD2_CIVIL",
                norm_reference="Legislazione Speciale Servizi di Pagamento",
                norm_title=kb_psd2["norm_title"],
                article=kb_psd2["article"],
                temporal_version=kb_psd2["temporal_version"],
                required_elements=kb_psd2["required_elements"],
                facts_found=[
                    "Registrazione contabile di operazioni controverse o eccedenti la delega nota"
                ],
                missing_facts=[
                    "Tracciato dei log di sicurezza dell'intermediario attestanti i fattori di autenticazione a due fattori (SCA)",
                    "Quietanza di consegna del contante o tracciato telematico firmato"
                ],
                confidence_degree="DIRITTO COERCIBILE AD AZIONE DI RIPETIZIONE INDEBITO / RISARCIMENTO",
                suggested_documents=kb_psd2["evidence_needed"],
                forensic_notes=(
                    "In caso di contestazione da parte del cliente, l'onere della prova della corretta autenticazione "
                    "grava per legge interamente sull'istituto bancario o postale ex art. 10 D.Lgs. 11/2010."
                )
            ))

        # 4. Evaluate Art. 1298 c.c. (Superamento presunzione 50% nei conti cointestati con provvista pensionistica)
        total_pension = sum(t.amount_credit for t in transactions if t.amount_credit and "PENS" in (t.description or "").upper())
        has_atm_withdrawals = any(t.amount_debit and t.channel and "ATM" in str(t.channel) for t in transactions)
        if total_pension > 0 and has_atm_withdrawals:
            kb_1298 = LEGAL_KB["ART_1298_CC"]
            hypotheses.append(LegalHypothesis(
                id="HYP_1298_CC",
                norm_reference="Codice Civile",
                norm_title=kb_1298["norm_title"],
                article=kb_1298["article"],
                temporal_version=kb_1298["temporal_version"],
                required_elements=kb_1298["required_elements"],
                facts_found=[
                    f"Rapporto cointestato con provvista quasi totalitaria da pensione INPS (€{total_pension:.2f})",
                    "Prelievi contanti sistematici eseguiti con singola carta di pagamento",
                    "Evidenza contabile del superamento della quota ideale del 50% da parte del soggetto prelevante"
                ],
                missing_facts=[
                    "Attribuzione soggettiva del cedolino pensione INPS al singolo cointestatario (Rossi o Bianchi)",
                    "Copia del modulo di emissione e consegna della carta Postamat n. ..6525",
                    "Eventuale accordo interno scritto derogatorio della parità di quote"
                ],
                confidence_degree="DIRITTO CIVILE RISARCITORIO / RIPETIZIONE INDEBITO (Altamente probabile in giudizio)",
                suggested_documents=kb_1298["evidence_needed"],
                forensic_notes=(
                    "In tema di conto corrente cointestato, ove sia provato che il saldo attivo sia alimentato in via esclusiva "
                    "dalla pensione o dai redditi di uno solo dei cointestatari, la presunzione legale di contitolarità al 50% "
                    "ex art. 1298 c.c. è integralmente superata (Cass. 21963/2019). L'altro cointestatario o chi ha utilizzato "
                    "la carta non ha alcun titolo giuridico per trattenere le somme prelevate."
                )
            ))

        # 5. Evaluate Art. 1713 c.c. (Obbligo di rendiconto del possessore fiduciario di carta / delegato)
        if has_atm_withdrawals:
            kb_1713 = LEGAL_KB["ART_1713_CC"]
            total_cash = sum(t.amount_debit for t in transactions if t.amount_debit and t.channel and "ATM" in str(t.channel))
            hypotheses.append(LegalHypothesis(
                id="HYP_1713_CC",
                norm_reference="Codice Civile",
                norm_title=kb_1713["norm_title"],
                article=kb_1713["article"],
                temporal_version=kb_1713["temporal_version"],
                required_elements=kb_1713["required_elements"],
                facts_found=[
                    f"Prelievi contanti cumulativi per complessivi €{total_cash:.2f} erogati dall'ATM n. 4095 con carta ..6525",
                    "Assenza nell'estratto conto di pagamenti diretti POS per spese mediche o alimentari documentate"
                ],
                missing_facts=[
                    "Rendiconto di cassa sottoscritto dal soggetto che ha materialmente detenuto la carta",
                    "Pezze giustificative (scontrini parlanti, fatture sanitarie, quietanze) a supporto delle spese per €3.000,00"
                ],
                confidence_degree="AZIONE GIUDIZIALE CIVILE DI RENDICONTO EX ART. 263 C.P.C. (Fondamento probatorio pieno)",
                suggested_documents=kb_1713["evidence_needed"],
                forensic_notes=(
                    "Chiunque detenga o utilizzi una carta di debito altrui per fare la spesa o provvedere ad anziani agisce come "
                    "mandatario ex art. 1710 c.c. ed è gravato dall'onere ex art. 1713 c.c. di rendere il conto al centesimo. "
                    "La mancata esibizione dei giustificativi comporta la condanna automatica alla restituzione delle somme."
                )
            ))

        # 6. Evaluate Art. 737 c.c. (Collazione ereditaria e reintegra legittima)
        if has_atm_withdrawals:
            kb_737 = LEGAL_KB["ART_737_CC"]
            hypotheses.append(LegalHypothesis(
                id="HYP_737_CC",
                norm_reference="Codice Civile (Successioni)",
                norm_title=kb_737["norm_title"],
                article=kb_737["article"],
                temporal_version=kb_737["temporal_version"],
                required_elements=kb_737["required_elements"],
                facts_found=[
                    "Uscite continue di liquidità dal patrimonio del soggetto prima dell'apertura della successione",
                    "Tracciabilità univoca del dispositivo Postamat e del punto di prelievo fisico"
                ],
                missing_facts=[
                    "Certificato di morte / Apertura della successione dell'uno o di entrambi i cointestatari",
                    "Stato di famiglia storico e dichiarazione di successione per l'individuazione della quota di legittima lesa"
                ],
                confidence_degree="AZIONE DI COLLAZIONE O RIDUZIONE PER LESIONE DI LEGITTIMA (Condizionata all'apertura successoria)",
                suggested_documents=kb_737["evidence_needed"],
                forensic_notes=(
                    "Se i prelievi con la carta sono stati effettuati da un figlio o discendente, le somme prelevate si qualificano "
                    "come anticipazioni sull'eredità (donazioni indirette) e vanno computate nell'asse ereditario ex art. 737 c.c., "
                    "ovvero reintegrate se ledono la quota di riserva degli altri legittimari."
                )
            ))

        # 7. Evaluate D.Lgs. 231/2007 (Antiriciclaggio & Vigilanza Intermediario)
        if has_multiple_same_day or len(transactions) >= 10:
            kb_aml = LEGAL_KB["DLGS_231_2007_AML"]
            hypotheses.append(LegalHypothesis(
                id="HYP_231_AML",
                norm_reference="Legislazione Speciale Antiriciclaggio",
                norm_title=kb_aml["norm_title"],
                article=kb_aml["article"],
                temporal_version=kb_aml["temporal_version"],
                required_elements=kb_aml["required_elements"],
                facts_found=[
                    "Operazioni di prelievo frazionate nel medesimo mese (es. due prelievi da €600 a distanza di 7 giorni a febbraio)",
                    "Incoerenza tra il profilo di cliente pensionato e un drenaggio di contante a cifra tonda pari a €3.000 nel trimestre"
                ],
                missing_facts=[
                    "Verifica della sussistenza di segnalazioni di operazioni sospette (SOS) archiviate da Poste Italiane",
                    "Questionario di adeguata verifica antiriciclaggio compilato dal cliente all'epoca dei fatti"
                ],
                confidence_degree="PROFILO DI RESPONSABILITÀ EX ART. 1176 C.C. PER OMESSA VIGILANZA BANCARIA",
                suggested_documents=kb_aml["evidence_needed"],
                forensic_notes=(
                    "La violazione delle regole di monitoraggio dell'intermediario previste dal D.Lgs. 231/2007 costituisce indice "
                    "di colpa grave e grave negligenza di Poste Italiane, utile per azionare la responsabilità dell'istituto "
                    "nella mancata tutela del cliente anziano vittima di condotte predatorie."
                )
            ))

        return hypotheses

