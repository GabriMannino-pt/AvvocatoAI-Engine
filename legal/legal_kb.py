"""
Italian Banking & Penal Legal Knowledge Base with Temporal Versioning.
Contains normative profiles for:
- Codice Penale (Art. 493-ter, 640, 643, 646 c.p.)
- Codice Civile (Art. 1176 comma 2, 1710, 1834, 1852 c.c.)
- Testo Unico Bancario (Art. 117, 119 D.Lgs. 385/1993)
- Servizi di Pagamento (D.Lgs. 11/2010 - PSD2)
- Decisioni e Orientamenti Consolidati ABF (Arbitro Bancario Finanziario).
"""
from typing import Dict, Any, List

LEGAL_KB: Dict[str, Dict[str, Any]] = {
    "ART_493_TER_CP": {
        "norm_title": "Codice Penale",
        "article": "Art. 493-ter c.p.",
        "rubrica": "Indebito utilizzo e falsificazione di strumenti di pagamento diversi dai contanti",
        "temporal_version": "Modificato da D.Lgs. 21/2018 (in vigore dal 6 aprile 2018, precedentemente art. 55 comma 9 D.Lgs. 231/2007)",
        "required_elements": [
            "Possesso o utilizzo indebito di carta di debito/credito/postamat",
            "Assenza di autorizzazione del titolare del conto/dispositivo",
            "Fine di trarne profitto per sé o per altri",
            "Materiale esecuzione del prelievo o della transazione"
        ],
        "penal_level": "Reato contro il patrimonio (Procedibilità d'ufficio)",
        "evidence_needed": [
            "Log informatico dell'operazione con numero carta e codice terminale ATM",
            "Disconoscimento sottoscritto dal titolare dell'operazione",
            "Riprese della videosorveglianza ATM attestanti l'identità dell'esecutore materiale"
        ]
    },
    "ART_646_CP": {
        "norm_title": "Codice Penale",
        "article": "Art. 646 c.p.",
        "rubrica": "Appropriazione indebita",
        "temporal_version": "Art. 646 c.p. (Procedibilità a querela salvo aggravante di abuso di relazioni domestiche ex art. 61 n. 11 c.p.)",
        "required_elements": [
            "Disponibilità materiale o giuridica delle somme (es. delega a operare sul conto)",
            "Trattenimento o destinazione del denaro per scopi estranei all'interesse del titolare",
            "Interversione del possesso uti dominus",
            "Danno patrimoniale cagionato alla vittima"
        ],
        "penal_level": "Reato contro il patrimonio",
        "evidence_needed": [
            "Contratto di delega o procura sul conto corrente",
            "Mancata rendicontazione o mancata consegna delle somme prelevate al titolare",
            "Quietanza di prelievo o estratto conto comprovante l'uscita finanziaria"
        ]
    },
    "ART_643_CP": {
        "norm_title": "Codice Penale",
        "article": "Art. 643 c.p.",
        "rubrica": "Circonvenzione di persone incapaci",
        "temporal_version": "Art. 643 c.p. (Procedibile d'ufficio)",
        "required_elements": [
            "Stato di vulnerabilità, senilità, decadimento cognitivo o deficienza psichica della vittima",
            "Condotta induttiva posta in essere dall'agente per convincere a compiere atti dannosi",
            "Compimento dell'atto dispositivo dannoso (es. rilascio delega, prelievi sistematici, conferimento PIN)",
            "Ingiusto profitto dell'agente con correlato nocumento della vittima"
        ],
        "penal_level": "Reato contro il patrimonio",
        "evidence_needed": [
            "Documentazione sanitaria e perizia medico-legale sullo stato cognitivo all'epoca dei fatti",
            "Serie storica dei prelievi (pattern di drenaggio progressivo del patrimonio)",
            "Prova della coabitazione o della frequentazione esclusiva tra l'agente e la persona fragile"
        ]
    },
    "ART_119_TUB": {
        "norm_title": "Testo Unico Bancario (D.Lgs. 385/1993)",
        "article": "Art. 119, comma 4, T.U.B.",
        "rubrica": "Comunicazioni periodiche alla clientela e diritto di accesso alla documentazione",
        "temporal_version": "Testo vigente",
        "required_elements": [
            "Richiesta formale inoltrata dal cliente, erede, amministratore di sostegno o avente causa",
            "Oggetto: copia della documentazione inerente a singole operazioni poste in essere negli ultimi dieci anni",
            "Obbligo di consegna entro congruo termine e comunque non oltre novanta giorni"
        ],
        "penal_level": "Diritto civile/bancario coercibile anche con ricorso ABF o ricorso per decreto ingiuntivo ex art. 633 c.p.c.",
        "evidence_needed": [
            "Lettera di diffida e messa in mora con prova di ricezione (PEC o raccomandata A/R)",
            "Mancata risposta o diniego dell'intermediario bancario/postale entro 90 giorni"
        ]
    },
    "DLGS_11_2010_PSD2": {
        "norm_title": "Decreto Legislativo n. 11/2010 (Attuazione PSD/PSD2)",
        "article": "Art. 10 e Art. 11 D.Lgs. 11/2010",
        "rubrica": "Prova dell'autenticazione ed esecuzione delle operazioni e responsabilità del prestatore",
        "temporal_version": "Aggiornato al D.Lgs. 218/2017 (PSD2)",
        "required_elements": [
            "Qualora l'utente neghi di aver autorizzato un'operazione, è onere del prestatore provare che l'operazione è stata autenticata, registrata e contabilizzata correttamente",
            "L'uso dello strumento di pagamento registrato non è di per sé necessariamente sufficiente a dimostrare che l'operazione sia stata autorizzata dall'utente",
            "Obbligo di rimborso immediato in favore dell'utente delle somme non autorizzate (entro la fine del giorno lavorativo successivo alla notifica)"
        ],
        "penal_level": "Normativa speciale di derivazione europea sulla ripartizione dell'onere probatorio bancario",
        "evidence_needed": [
            "Comunicazione formale di disconoscimento inviata alla banca/Poste",
            "Mancata fornitura da parte dell'intermediario della prova tecnica della Strong Customer Authentication (SCA)"
        ]
    },
    "ART_1176_CC": {
        "norm_title": "Codice Civile",
        "article": "Art. 1176, comma 2, c.c.",
        "rubrica": "Diligenza nell'adempimento delle obbligazioni professionali",
        "temporal_version": "Testo vigente",
        "required_elements": [
            "Natura dell'attività professionale esercitata dall'intermediario (diligenza qualificata del bonus argentarius)",
            "Dovere di monitoraggio e blocco preventivo di operazioni con palesi anomalie temporali o dimensionali",
            "Responsabilità contrattuale per negligente o omessa vigilanza sui sistemi di erogazione fondi"
        ],
        "penal_level": "Responsabilità civile contrattuale",
        "evidence_needed": [
            "Estratto conto che evidenzia la palese anomalia rispetto al normale tenore di vita dell'intestatario",
            "Assenza di alert antifrode o richieste di conferma da parte della banca al titolare"
        ]
    },
    "ART_1298_CC": {
        "norm_title": "Codice Civile",
        "article": "Art. 1298, comma 2, c.c.",
        "rubrica": "Rapporti interni tra condebitori o concreditori solidali (Cointestazione di conto)",
        "temporal_version": "Testo vigente (Conforme a Cass. Civ. Sez. II n. 21963/2019 e n. 4838/2021)",
        "required_elements": [
            "Conto corrente o libretto postale formalmente cointestato con facoltà di firma disgiunta",
            "Presunzione legale 'iuris tantum' di parità delle quote al 50% nei soli rapporti interni tra i cointestatari",
            "Superamento della presunzione in caso di prova contraria attestante l'esclusiva provenienza delle provviste da uno solo dei cointestatari (es. accrediti pensionistici o retributivi personali)",
            "Diritto del cointestatario titolare delle provviste (o dei suoi eredi) di pretendere la restituzione dell'intero importo prelevato dall'altro contitolare in eccedenza"
        ],
        "penal_level": "Diritto civile delle obbligazioni e diritti reali / Indebito oggettivo (Art. 2033 c.c.)",
        "evidence_needed": [
            "Estratti conto storici integrali che attestino che la totalità o quasi delle entrate deriva dalla pensione/reddito di un solo soggetto",
            "Certificato di pensione INPS / Modello Obis-M indicante il codice fiscale del reale beneficiario dell'assegno",
            "Tracciato dei prelievi eseguiti con la carta intestata/in uso all'altro cointestatario o a terzi"
        ]
    },
    "ART_1713_CC": {
        "norm_title": "Codice Civile",
        "article": "Art. 1713 c.c. (in combinato con Art. 1710 c.c.)",
        "rubrica": "Obbligo di rendiconto del mandatario / possessore fiduciario di carta di pagamento",
        "temporal_version": "Testo vigente (Conforme a Cass. Civ. Sez. II n. 7254/2013 e n. 11283/2018)",
        "required_elements": [
            "Consegna materiale della carta di pagamento (o delega a operare) a un terzo/familiare/badante a titolo di mandato fiduciario (gestione spese)",
            "Esecuzione di prelievi contanti a valere sulla provvista dell'assistito",
            "Dovere incondizionato del mandatario di rendere il conto del proprio operato e di rimettere al mandante tutto ciò che ha ricevuto",
            "Incapacità o rifiuto del mandatario di esibire idonea documentazione giustificativa (scontrini, fatture, quietanze sanitarie o alimentari) corrispondente alle somme prelevate",
            "Condanna alla restituzione integrale delle somme non giustificate"
        ],
        "penal_level": "Azione civile di rendiconto (Art. 263 c.p.c.) e ripetizione somme indebite (con risvolti penali ex art. 646 c.p.)",
        "evidence_needed": [
            "Estratto conto con evidenziazione del totale dei prelievi contanti eseguiti",
            "Mancanza o incongruenza dei giustificativi di spesa prodotti dal gestore della carta",
            "Stima del fabbisogno economico mensile reale dell'anziano titolare del conto"
        ]
    },
    "ART_737_CC": {
        "norm_title": "Codice Civile",
        "article": "Art. 737 c.c. e Art. 553 e ss. c.c.",
        "rubrica": "Collazione ereditaria e lesione della quota di legittima",
        "temporal_version": "Testo vigente",
        "required_elements": [
            "Decesso del titolare del conto e apertura della successione ereditaria",
            "Prelievi bancari o postali eseguiti in vita dal cointestatario, figlio o terzo senza controprestazione o titolo oneroso",
            "Qualificazione dei prelievi come donazioni indirette o distrazione di beni ereditari",
            "Obbligo per i figli e discendenti di conferire nella massa ereditaria tutto ciò che hanno ricevuto dal defunto per donazione diretta o indiretta (salvo espressa dispensa nei limiti della disponibile)",
            "Reintegrazione della quota di legittima spettante agli altri coeredi lesi"
        ],
        "penal_level": "Diritto successorio / Tutela dei legittimari",
        "evidence_needed": [
            "Dichiarazione di successione o atto di notorietà attestante la qualifica di eredi",
            "Perizia contabile-forense attestante l'ammontare cumulativo delle somme prelevate con indicazione del terminale e della carta utilizzata",
            "Assenza di prova della destinazione delle somme a esclusivo vantaggio del de cuius"
        ]
    },
    "DLGS_231_2007_AML": {
        "norm_title": "Decreto Legislativo n. 231/2007 (Disciplina Antiriciclaggio)",
        "article": "Art. 35 e Art. 49 D.Lgs. 231/2007 (e successive modifiche)",
        "rubrica": "Obbligo di segnalazione delle operazioni sospette e divieto di frazionamento artificioso",
        "temporal_version": "Applicabile ratione temporis (Soglia contante nel 2016: € 3.000,00 ex D.L. 201/2011 e L. 208/2015)",
        "required_elements": [
            "Operatività su contante caratterizzata da prelievi reiterati e frazionati a cadenza ravvicinata (entro 7 giorni)",
            "Superamento del profilo di rischio ordinario del cliente (inadeguatezza rispetto al profilo di un pensionato a basso reddito)",
            "Omissione da parte dell'intermediario delle misure di monitoraggio costante e adeguata verifica rafforzata",
            "Presupposto per l'accertamento della corresponsabilità dell'istituto per omessa prevenzione di condotte predatorie su soggetti deboli"
        ],
        "penal_level": "Normativa speciale antiriciclaggio e sanzioni amministrative pecuniarie",
        "evidence_needed": [
            "Prospetto dei prelievi aggregati per finestre temporali di 7 e 30 giorni",
            "Mancata attivazione da parte dell'ufficio postale dei questionari di adeguata verifica o degli alert automatici antifrode"
        ]
    }
}

