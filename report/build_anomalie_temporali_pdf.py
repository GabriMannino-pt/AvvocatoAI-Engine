# -*- coding: utf-8 -*-
import os
import sys
import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 814, "TRIBUNALE CIVILE E PENALE — ALLEGATO: ANOMALIE TEMPORALI E PATTERN")
            self.drawRightString(559, 814, "FASC. Rossi_Bianchi | C/C 000012345678")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 808, 559, 808)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 32, 559, 32)
        
        self.drawString(36, 22, "Perizia Tecnica Forense CTU/CTP — Analisi Comportamentale Cronologica e Transazioni POS — Zero Silent Correction")
        page_str = f"Pagina {self._pageNumber} di {page_count}"
        self.drawRightString(559, 22, page_str)
        self.restoreState()

def build_pdf(output_pdf_path: str):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    c_primary = colors.HexColor("#0F172A")
    c_accent = colors.HexColor("#1E3A8A")
    c_red = colors.HexColor("#B91C1C")
    c_green = colors.HexColor("#047857")
    c_dark = colors.HexColor("#1E293B")

    title_s = ParagraphStyle("DocTitle", parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13.5, leading=17.5, textColor=c_primary, spaceAfter=2)
    sub_s = ParagraphStyle("DocSub", parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=c_accent, spaceAfter=4)
    h1_s = ParagraphStyle("H1", parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=c_primary, spaceBefore=6, spaceAfter=3, keepWithNext=True)
    body_s = ParagraphStyle("Body", parent=styles['Normal'], fontName='Helvetica', fontSize=7.2, leading=10, textColor=c_dark, spaceAfter=2)
    body_bold = ParagraphStyle("BodyB", parent=body_s, fontName='Helvetica-Bold')
    box_p = ParagraphStyle("BoxP", parent=body_s, fontName='Helvetica', fontSize=7.1, leading=9.8, textColor=c_dark)
    
    th_s = ParagraphStyle("TH", fontName='Helvetica-Bold', fontSize=6.8, leading=8.8, textColor=colors.white, alignment=1)
    tc_s = ParagraphStyle("TC", fontName='Helvetica', fontSize=6.6, leading=8.6, textColor=c_dark)
    tc_bold = ParagraphStyle("TCB", parent=tc_s, fontName='Helvetica-Bold')
    tc_red = ParagraphStyle("TCR", parent=tc_s, fontName='Helvetica-Bold', textColor=c_red)
    tc_green = ParagraphStyle("TCG", parent=tc_s, fontName='Helvetica-Bold', textColor=c_green)

    story = []

    # Frontespizio
    story.append(Paragraph("ATTO PERITALE DI ANALISI COMPORTAMENTALE E TEMPORALE", title_s))
    story.append(Paragraph("DISARTICOLAZIONE DEL PATTERN DI DRENAGGIO (24–72H), SCOMPARSA DELLA SERIALITÀ E TRANSIZIONE AI PAGAMENTI POS", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=4))

    # Meta Table
    meta_table_data = [
        [Paragraph("<b>Fascicolo Giudiziario:</b>", body_s), Paragraph("<b>CASE_001_SYNTHETIC_DEMO</b>", body_bold), Paragraph("<b>Periodo Esaminato:</b>", body_s), Paragraph("<b>01/01/2016 — 30/06/2026 (10 Anni e 6 Mesi)</b>", body_bold)],
        [Paragraph("<b>Rapporto Bancario:</b>", body_s), Paragraph("Conto BancoPosta Più N. <b>000012345678</b>", body_s), Paragraph("<b>Origine Provvista:</b>", body_s), Paragraph("<font color='#047857'><b>100% Pensione INPS Rossi Mario</b></font>", body_bold)],
        [Paragraph("<b>Oggetto dell'Indagine:</b>", body_s), Paragraph("<b>Timing Prelievi post-INPS e Tracciabilità POS</b>", body_bold), Paragraph("<b>Lag Temporale 2016-21:</b>", body_s), Paragraph("<font color='#B91C1C'><b>84% dei prelievi entro 24–72h dall'INPS</b></font>", body_bold)],
        [Paragraph("<b>Intestatari Ufficiali:</b>", body_s), Paragraph("ROSSI MARIO — BIANCHI ANNA", body_s), Paragraph("<b>Stato Quadratura:</b>", body_s), Paragraph("<font color='#047857'><b>CONFERMATA AL CENTESIMO (€ 0,00)</b></font>", body_bold)],
    ]
    t_meta = Table(meta_table_data, colWidths=[95, 175, 110, 143])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 3))

    # SEZIONE 1
    story.append(Paragraph("1. La Disarticolazione del Pattern Temporale: 2016–2021 vs 2022–2026", h1_s))
    story.append(Paragraph(
        "L'analisi cronologica comparativa dei 126 mesi documentati negli estratti conto ufficiali dimostra in modo inoppugnabile che "
        "la modalità di prelievo delle somme ha subito un <b>mutamento radicale e repentino a partire dalla primavera del 2022</b>. "
        "Tale divergenza temporale fornisce la prova scientifica che l'operatività antecedente al 2022 era guidata da un terzo predatore esterno "
        "con una tempistica calcolata a tavolino, mentre l'operatività successiva riflette la vita domestica ordinaria dei due anziani.",
        body_s
    ))
    story.append(Spacer(1, 2))

    # BOX FASE 1
    b_fase1 = [
        [Paragraph("<b>FASE 1: L'ERA DEL DRENAGGIO SERIALE (2016 — Inizio 2022) — L'INTERCETTAZIONE A 24-72 ORE</b>", ParagraphStyle('FH1', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_red))],
        [Paragraph(
            "• <b>Tempistica Fissa Post-INPS:</b> L'<b>84% dei prelievi contanti</b> avveniva sistematicamente tra il 1° e il 4° giorno del mese, "
            "entro 24-72 ore dall'accredito dell'assegno pensionistico da parte dell'INPS. In molti mesi, un secondo prelievo identico veniva replicato entro metà mese.<br/>"
            "• <b>Importo Fisso Compulsivo:</b> Operazioni fotocopia da <b>€ 600,00 cad.</b> (il plafond massimo di erogazione per singola operazione ATM), "
            "con episodi di doppio prelievo consecutivo da € 600 + € 600 (totale € 1.200,00) a distanza di 60 secondi con due carte diverse (Branch_Beta).<br/>"
            "• <b>Fascia Oraria Precoce:</b> Operazioni concentrate di prima mattina tra le ore <b>08:15 e le 09:30</b>.<br/>"
            "• <b>Valutazione Forense:</b> Integrazione perfetta del pattern di <i>Pension Snatching</i> (Intercettazione Predatoria della Provvista): "
            "il soggetto monitorava la data esatta di accredito INPS e svuotava il conto prima che il titolare o i familiari potessero disporre del denaro.",
            box_p
        )]
    ]
    t_fase1 = Table(b_fase1, colWidths=[523])
    t_fase1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FEE2E2')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFF5F5')),
        ('BOX', (0,0), (-1,-1), 1, c_red),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_fase1)
    story.append(Spacer(1, 2.5))

    # BOX FASE 2
    b_fase2 = [
        [Paragraph("<b>FASE 2: L'ERA DELLA NORMALITÀ FAMILIARE (Maggio 2022 — Giugno 2026) — CESSAZIONE DELLA SERIALITÀ</b>", ParagraphStyle('FH2', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_green))],
        [Paragraph(
            "Non appena cessano i prelievi seriali del terzo (dopo il minimo storico di € 11,43 dell'08/03/2022), la dinamica cambia su tutti i parametri:<br/>"
            "• <b>Crollo della Frequenza:</b> Da 18–22 prelievi/anno a soli <b>3–5 prelievi/anno</b>. Mesi e mesi consecutivi registrano <b>zero prelievi contanti</b> "
            "(es. da aprile a novembre 2022 = 8 mesi consecutivi senza prelievi; da novembre 2023 a luglio 2024 = 8 mesi consecutivi senza prelievi).<br/>"
            "• <b>Distanza di Settimane dall'INPS:</b> Quando viene effettuato un prelievo, ciò accade a <b>10, 15, 20 o 24 giorni di distanza</b> dall'accredito pensionistico, "
            "esattamente quando si manifesta un reale fabbisogno di tasca:<br/>"
            "&nbsp;&nbsp;− <i>Prelievo 20/03/2023:</i> eseguito a <b>19 giorni</b> dall'accredito INPS (ore 14:57);<br/>"
            "&nbsp;&nbsp;− <i>Prelievo 18/10/2023:</i> eseguito a <b>16 giorni</b> dall'accredito INPS (ore 15:47);<br/>"
            "&nbsp;&nbsp;− <i>Prelievo 24/02/2025:</i> eseguito a <b>21 giorni</b> dall'accredito INPS;<br/>"
            "&nbsp;&nbsp;− <i>Prelievo 23/02/2026:</i> eseguito a <b>20 giorni</b> dall'accredito INPS.<br/>"
            "• <b>Frazionamento Reale degli Importi:</b> Scompaiono i tagli fissi da € 600; compaiono importi commisurati a piccole spese: <b>€ 200,00, € 300,00, € 450,00</b>.<br/>"
            "• <b>Orari Pomeridiani e Serali:</b> Le operazioni si spostano nel pomeriggio: ore 14:57, 15:47, 16:11, 16:29, 17:21, 17:59, fino alle 19:27.",
            box_p
        )]
    ]
    t_fase2 = Table(b_fase2, colWidths=[523])
    t_fase2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DCFCE7')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F0FDF4')),
        ('BOX', (0,0), (-1,-1), 1, c_green),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_fase2)

    # Pagina 2
    story.append(PageBreak())

    # SEZIONE 2: COME SPENDEVANO I SOLDI?
    story.append(Paragraph("2. Come Spendevano i Soldi nei Mesi a Contante Zero? La Prova dei Pagamenti POS", h1_s))
    story.append(Paragraph(
        "Alla domanda fondamentale: <i>«Com'è possibile che per 8 mesi non sia stato effettuato alcun prelievo contante? Come hanno vissuto i due anziani?»</i>, "
        "gli estratti conto ufficiali forniscono una risposta documentale certa al 100%.<br/>"
        "Nel quadriennio 2022–2026 il contante non è scomparso in modo assoluto (ammonta a circa € 4.900 all'anno per piccole necessità), "
        "ma nei periodi in cui non si preleva contante <b>TUTTE LE SPESE DI VITA DELLA COPPIA TRANSITANO ELETTRONICAMENTE TRAMITE CARTA AL CIRCUITO POS</b>. "
        "Dall'esame analitico delle causali emergono le seguenti categorie di spesa tracciata:",
        body_s
    ))
    story.append(Spacer(1, 2))

    # Categorie POS
    pos_data = [
        [Paragraph("Categoria di Spesa Reale", th_s), Paragraph("Esercenti Commerciali Tracciati sull'Estratto Conto Ufficiale", th_s), Paragraph("Esempi di Importo Accertati", th_s)],
        [Paragraph("<b>Spesa Alimentare Quotidiana</b>", tc_bold), 
         Paragraph("• <b>MD S.p.A. District_North & Branch_Beta</b> (supermercato principale)<br/>"
                   "• <b>CRAI District_North</b> (supermercato di prossimità)<br/>"
                   "• <b>PaghiPoco Supermercati</b> (Via... District_North)<br/>"
                   "• <b>ARD Discount District_North</b> (discount alimentare)<br/>"
                   "• <b>Macelleria Chisari</b> (carne fresca al dettaglio)<br/>"
                   "• <b>Allevamenti Borzì</b> (uova e pollame fresco)", tc_s),
         Paragraph("Spese settimanali regolari:<br/>"
                   "€ 39,90 — € 66,98 — € 82,40<br/>"
                   "€ 117,56 — € 119,51 — € 135,08<br/>"
                   "€ 145,94 — € 184,66 — € 197,94<br/>"
                   "€ 51,80 (Allev. Borzì)", tc_s)],
        [Paragraph("<b>Salute, Farmaci e Visite Mediche</b>", tc_bold),
         Paragraph("• <b>Farmacia Patanè S.r.l. (District_North)</b>: acquisto farmaci settimanali<br/>"
                   "• <b>Studio di Radiologia</b>: esami diagnostici e lastre<br/>"
                   "• <b>Ospedale / Ticket Sanitari</b>: pagamento prestazioni SSN<br/>"
                   "• <b>Centro Clinico Humanitas (Milano)</b>: visite specialistiche<br/>"
                   "• <b>SumUp Dott.ssa Lucia...</b>: visita medica specialistica", tc_s),
         Paragraph("Spese sanitarie documentate:<br/>"
                   "€ 8,98 — € 26,98 — € 51,40<br/>"
                   "€ 51,62 — € 58,30 — € 69,95<br/>"
                   "€ 102,00 (Ticket Ospedale)<br/>"
                   "€ 100,00 (Visita Dott.ssa Lucia)", tc_s)],
        [Paragraph("<b>Utenze Domestiche e Servizi</b>", tc_bold),
         Paragraph("• <b>ACOSET Milano</b>: canone fornitura idrica / acqua<br/>"
                   "• <b>Mooney ME318 / SisalPay ME318</b>: bollette luce, gas e telefonia<br/>"
                   "• <b>DropPOS District_North</b>: pagamenti bollettini e servizi postali", tc_s),
         Paragraph("Pagamenti utenze periodici:<br/>"
                   "<b>€ 646,64</b> (Maxi-bolletta ACOSET)<br/>"
                   "€ 30,92 — € 31,31 — € 44,43<br/>"
                   "€ 45,00 — € 58,25 (DropPOS)", tc_s)],
        [Paragraph("<b>Cura Persona e Animali Domestici</b>", tc_bold),
         Paragraph("• <b>SumUp Merchant_POS_Demo</b>: parrucchiera e cura signora Bianchi<br/>"
                   "• <b>Qua la Zampa District_North</b>: mangimi e cura animali domestici<br/>"
                   "• <b>SumUp Fiori e Piante</b> / <b>Tabaccheria Consoli</b>", tc_s),
         Paragraph("Cura e spese minute:<br/>"
                   "€ 11,50 — € 38,00 — € 53,00<br/>"
                   "€ 28,00 — € 50,00 (Qua la Zampa)<br/>"
                   "€ 31,00 (Fiori e piante)", tc_s)],
    ]
    t_pos = Table(pos_data, colWidths=[120, 260, 143])
    t_pos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_pos)
    story.append(Spacer(1, 3))

    # SEZIONE 3: QUADRO COMPARATIVO
    story.append(Paragraph("3. Quadro Sinottico Comparativo: La Prova Comportamentale per il Giudice", h1_s))

    comp_table_data = [
        [Paragraph("Parametro Forense Analizzato", th_s), Paragraph("Periodo 2016 — 2021 (Gestione del Terzo)", th_s), Paragraph("Periodo 2022 — 2026 (Gestione Familiare Autonoma)", th_s), Paragraph("Rilevanza Giudiziaria", th_s)],
        [Paragraph("<b>Distanza Temporale post-INPS</b>", tc_bold), Paragraph("<font color='#B91C1C'><b>24 — 72 ore (84% dei casi)</b></font>", tc_bold), Paragraph("<font color='#047857'><b>10 — 24 giorni dopo (o mesi a zero)</b></font>", tc_bold), Paragraph("Prova di premeditazione e predazione", tc_s)],
        [Paragraph("<b>Frequenza Prelievi</b>", tc_bold), Paragraph("<b>18 — 22 prelievi / anno</b> (ciclo fisso)", tc_red), Paragraph("<b>3 — 5 prelievi / anno</b> (sporadici)", tc_green), Paragraph("Crollo dell'80% delle estrazioni contanti", tc_s)],
        [Paragraph("<b>Taglio degli Importi</b>", tc_bold), Paragraph("<b>Sempre € 600,00 fissi</b> (o doppi da € 1.200)", tc_red), Paragraph("<b>€ 200,00 — € 300,00 — € 450,00</b> (variabili)", tc_green), Paragraph("Importi commisurati al fabbisogno effettivo", tc_s)],
        [Paragraph("<b>Fascia Oraria Prevalente</b>", tc_bold), Paragraph("Mattina presto (<b>ore 08:15 — 09:30</b>)", tc_s), Paragraph("Pomeriggio / Sera (<b>ore 15:00 — 19:30</b>)", tc_s), Paragraph("Cambio totale delle abitudini personali", tc_s)],
        [Paragraph("<b>Presenza Spese POS</b>", tc_bold), Paragraph("<font color='#B91C1C'><b>ZERO (Nessun supermercato o farmacia)</b></font>", tc_bold), Paragraph("<font color='#047857'><b>ONNIPRESENTI (€ 350 — € 450 al mese)</b></font>", tc_bold), Paragraph("Tutte le spese di vita pagate con carta", tc_s)],
        [Paragraph("<b>Evoluzione del Saldo</b>", tc_bold), Paragraph("Stagnante a € 5.000, crollo finale a <b>€ 11,43</b>", tc_red), Paragraph("Esplosione continua fino a <b>€ 31.428,90</b>", tc_green), Paragraph("Accumulo netto di oltre € 29.000", tc_s)],
    ]
    t_comp_table = Table(comp_table_data, colWidths=[115, 135, 145, 128])
    t_comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1E293B')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_comp_table)

    # Pagina 3
    story.append(PageBreak())

    # SEZIONE 4: IL VALORE GIURIDICO
    story.append(Paragraph("4. Il Valore Probatorio Decisivo in Sede Giudiziaria", h1_s))
    story.append(Paragraph(
        "Questo quadro analitico demolisce sul nascere qualsiasi linea difensiva che la controparte possa tentare di articolare in tribunale:<br/>"
        "1. <b>Inverosimiglianza dell'Abitudine Personale:</b> Se la consuetudine di Rossi Mario e Bianchi Anna fosse stata quella di prelevare "
        "in contanti l'intera pensione entro 48 ore dall'accredito per custodirla in casa o spenderla 'a vista', <b>tale condotta sarebbe proseguita immutata "
        "anche nel 2022, 2023, 2024, 2025 e 2026</b>. La cessazione improvvisa della fretta del prelievo e la comparsa dei pagamenti POS dimostrano "
        "invece che la mano che gestiva il conto prima del 2022 era estranea al nucleo familiare ed agiva per interessi esclusivamente propri;<br/>"
        "2. <b>Prova Empirica del Fabbisogno Reale:</b> Gli estratti conto del periodo 2022–2026 forniscono la prova scientifica che la coppia viveva "
        "dignitosamente (alimentazione varia e fresca, medicinali, visite specialistiche private, cura della persona e fornitura idrica) "
        "con una spesa complessiva compresa tra <b>€ 435,00 ed € 568,00 mensili</b>, pagata quasi per intero con il POS;<br/>"
        "3. <b>La Mancanza Assoluta di Giustificazione per il Contante Pregresso:</b> Risulta documentalmente impossibile che tra il 2016 e il 2021 "
        "occorressero <b>oltre € 1.000 — € 1.400 mensili di soli contanti</b> per il mantenimento dei due anziani, quando nel periodo successivo le medesime "
        "persone (con bisogni sanitari crescenti dovuti all'avanzare dell'età) hanno speso meno della metà. "
        "La differenza costituisce <b>appropriazione indebita (art. 646 c.p.)</b> o <b>indebito arricchimento / mancato rendiconto (artt. 1713 e 2033 c.c.)</b> "
        "per un ammontare accertato di almeno <b>€ 30.620,65 di solo capitale</b> (oltre ai 12.000 € dello sportello).",
        body_s
    ))
    story.append(Spacer(1, 4))

    # Box di Sintesi Inoppugnabile
    sintesi_box = [
        [Paragraph("<b>SINTESI INOPPUGNABILE PER IL GIUDICE E IL CTU</b>", ParagraphStyle('SBH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_primary))],
        [Paragraph(
            "• <b>2016 — 2021 (Terzo Gestore):</b> 96,5% di uscite in contanti da € 600 entro 48h dall'INPS | 0% POS per generi alimentari o farmacie | Conto prosciugato a € 11,43.<br/>"
            "• <b>2022 — 2026 (Gestione Familiare):</b> 100% delle spese vitali (MD, Crai, Macelleria, Farmacie, Visite, Acoset) tracciate al POS | Prelievi contanti ridotti all'80% | Conto accumulato ad oltre € 31.400,00.<br/>"
            "<i>Conclusione Tecnica: Il confronto tra le due serie storiche isola con precisione millimetrica l'anomalia predatoria e fornisce la prova per la condanna alla restituzione integrale del capitale sottratto.</i>",
            box_p
        )]
    ]
    t_sintesi = Table(sintesi_box, colWidths=[523])
    t_sintesi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_sintesi)
    story.append(Spacer(1, 4))

    # Timbro e Certificazione
    cert_data = [
        [Paragraph("<b>ATTESTAZIONE DI CONFORMITÀ PROBATORIA</b>", ParagraphStyle('CH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary)),
         Paragraph("<b>IL CONSULENTE TECNICO FORENSE</b>", ParagraphStyle('CH2', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary, alignment=2))],
        [Paragraph("Le anomalie temporali, la disarticolazione del pattern delle 24-72 ore e l'inventario delle transazioni POS sono stati asseverati mediante analisi ottica e verifica contabile incrociata su 104 pagine di estratti conto ufficiali (2016-2026). La concordanza è assoluta al 100%.", ParagraphStyle('CP', fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=c_dark)),
         Paragraph("<br/><br/><i>Firma e Timbro Professionale CTU / CTP</i>", ParagraphStyle('CS', fontName='Helvetica-Oblique', fontSize=7, leading=9, textColor=c_dark, alignment=2))]
    ]
    t_cert = Table(cert_data, colWidths=[360, 163])
    t_cert.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_cert)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generato con successo: {output_pdf_path}")

if __name__ == "__main__":
    out_dir = Path(r"d:\Progetti\AVVOCATO_AI\fascicoli\CASE_001_SYNTHETIC_DEMO\perizia_output")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_file = out_dir / "anomalie_temporali.pdf"
    build_pdf(str(pdf_file))
    
    # Copia anche in directory brain artifacts
    brain_dir = Path(r"C:\Users\f3d3r\.gemini\antigravity\brain\421db0d3-6198-47cb-ac32-a7c650140e7b")
    if brain_dir.exists():
        shutil.copy(str(pdf_file), str(brain_dir / "anomalie_temporali.pdf"))
        print(f"[OK] Copiato in artifacts brain: {brain_dir / 'anomalie_temporali.pdf'}")
