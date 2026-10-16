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
            self.drawString(36, 814, "TRIBUNALE CIVILE E PENALE — ALLEGATO PERITALE: CONTEGGIO CAPITALE DISTRATTO")
            self.drawRightString(559, 814, "FASC. CASE_001_SYNTHETIC_DEMO | C/C 000012345678")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 808, 559, 808)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 32, 559, 32)
        
        self.drawString(36, 22, "Perizia Tecnica Forense CTU/CTP — Quantificazione Danno Patrimoniale — Solo Capitale Escluso Interessi/Rivalutazione")
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
    c_amber = colors.HexColor("#B45309")

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

    # Intestazione
    story.append(Paragraph("ATTO PERITALE DI QUANTIFICAZIONE DEL DANNO PATRIMONIALE", title_s))
    story.append(Paragraph("CONTEGGIO DEL CAPITALE DISTRATTO (2016 — 2021) ED ANALISI FORENSI AVANZATE SUI MOVIMENTI BANCARI", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=4))

    # Meta Table
    meta_table_data = [
        [Paragraph("<b>Fascicolo Giudiziario:</b>", body_s), Paragraph("<b>CASE_001_SYNTHETIC_DEMO</b>", body_bold), Paragraph("<b>Periodo Contestato:</b>", body_s), Paragraph("<b>01/01/2016 — 31/12/2021 (72 Mesi)</b>", body_bold)],
        [Paragraph("<b>Rapporto Bancario:</b>", body_s), Paragraph("Conto BancoPosta Più N. <b>000012345678</b>", body_s), Paragraph("<b>Origine Provvista:</b>", body_s), Paragraph("<font color='#047857'><b>100% Pensione INPS Rossi Mario</b></font>", body_bold)],
        [Paragraph("<b>Oggetto della Quantificazione:</b>", body_s), Paragraph("<b>Solo Capitale Distratto</b> (No interessi / rivalutazione)", body_bold), Paragraph("<b>Prelievi Contanti 2016-21:</b>", body_s), Paragraph("<font color='#B91C1C'><b>€ 69.100,00 (96,6% del totale uscite)</b></font>", body_bold)],
        [Paragraph("<b>Intestatari Ufficiali:</b>", body_s), Paragraph("ROSSI MARIO — BIANCHI ANNA", body_s), Paragraph("<b>Stato Quadratura:</b>", body_s), Paragraph("<font color='#047857'><b>CERTIFICATA AL CENTESIMO (€ 0,00)</b></font>", body_bold)],
    ]
    t_meta = Table(meta_table_data, colWidths=[95, 175, 105, 148])
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

    # PARTE 1
    story.append(Paragraph("1. Premessa e Dati Certificati di Partenza (Periodo 2016 — 2021)", h1_s))
    story.append(Paragraph(
        "Al fine di quantificare con rigore matematico ed oggettività forense il <b>danno patrimoniale effettivo (solo capitale)</b> subito dal pensionato "
        "Rossi Mario e dalla moglie Bianchi Anna per effetto dei prelievi non autorizzati eseguiti da terzi tra il <b>01/01/2016 e il 31/12/2021 (72 mesi)</b>, "
        "si assumono come base contabile indiscutibile i dati certificati dagli estratti conto ufficiali di Poste Italiane:<br/>"
        "• <b>Pensione INPS complessivamente accreditata:</b> € 68.576,40<br/>"
        "• <b>Uscite Totali effettive dal conto:</b> € 71.518,09<br/>"
        "• <b>di cui Prelievi Contanti Totali:</b> <font color='#B91C1C'><b>€ 69.100,00</b></font> <b>(il 96,6% di tutte le uscite!)</b>:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;− <i>Maxi-prelievo a vista allo sportello (07/03/2020 Cassa 3 Branch_Alpha):</i> <b>€ 12.000,00</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;− <i>Prelievi seriali ordinari (quasi tutti da € 600 cad.):</i> <b>€ 57.100,00</b><br/>"
        "• <b>Canoni e oneri bancari ordinari:</b> € 2.418,09 (comprensivi di € 83,00 per canoni della seconda carta non necessaria).",
        body_s
    ))
    story.append(Spacer(1, 2))

    # SCENARIO A, B, C
    story.append(Paragraph("2. I Tre Scenari Giudiziari di Quantificazione del Capitale", h1_s))

    # SCENARIO A BOX
    scen_a_data = [
        [Paragraph("<b>SCENARIO A — Fabbisogno Reale Comprovato (€ 568,02 / mese) — [RACCOMANDATO IN GIUDIZIO]</b>", ParagraphStyle('SH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary))],
        [Paragraph(
            "<b>Criterio Tecnico:</b> È la quantificazione più solida e prudenziale. Si riconosce al convenuto che la coppia di anziani necessitasse comunque "
            "per il proprio sostentamento quotidiano della somma mensile realmente spesa negli anni successivi di gestione autonoma (media 2022-2026 pari a € 568,02/mese).<br/>"
            "• <i>Spese lecite di vita riconosciute alla coppia (72 mesi × € 568,02):</i> <b>€ 40.897,44</b><br/>"
            "• <i>Uscite totali effettive addebitate sul conto:</i> <b>€ 71.518,09</b><br/>"
            "• <b>CAPITALE NETTO DISTRATTO DA RESTITUIRE: € 71.518,09 − € 40.897,44 = </b> <font color='#B91C1C' size='8'><b>€ 30.620,65</b></font>",
            box_p
        )]
    ]
    t_scen_a = Table(scen_a_data, colWidths=[523])
    t_scen_a.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_scen_a)
    story.append(Spacer(1, 2))

    # Dettaglio Annuale Tabella Scenario A
    table_a_data = [
        [Paragraph("Anno", th_s), Paragraph("Uscite Effettive (€)", th_s), Paragraph("Fabbisogno Reale Stimato (€)", th_s), Paragraph("Capitale Puro Distratto (€)", th_s), Paragraph("Incidenza Prelievi Contanti (€)", th_s)],
        [Paragraph("<b>2016</b>", tc_s), Paragraph("€ 10.512,40", tc_s), Paragraph("€ 6.816,24", tc_s), Paragraph("<b>€ 3.696,16</b>", tc_red), Paragraph("€ 10.200,00 (97,0%)", tc_s)],
        [Paragraph("<b>2017</b>", tc_s), Paragraph("€ 10.850,00", tc_s), Paragraph("€ 6.816,24", tc_s), Paragraph("<b>€ 4.033,76</b>", tc_red), Paragraph("€ 10.400,00 (95,9%)", tc_s)],
        [Paragraph("<b>2018</b>", tc_s), Paragraph("€ 10.920,00", tc_s), Paragraph("€ 6.816,24", tc_s), Paragraph("<b>€ 4.103,76</b>", tc_red), Paragraph("€ 10.500,00 (96,2%)", tc_s)],
        [Paragraph("<b>2019</b>", tc_s), Paragraph("€ 11.200,00", tc_s), Paragraph("€ 6.816,24", tc_s), Paragraph("<b>€ 4.383,76</b>", tc_red), Paragraph("€ 10.700,00 (95,5%)", tc_s)],
        [Paragraph("<b>2020</b>", tc_s), Paragraph("€ 16.585,69", tc_s), Paragraph("€ 6.816,24", tc_s), Paragraph("<b>€ 9.769,45*</b>", tc_red), Paragraph("€ 16.200,00 (inc. 12k sportello)", tc_s)],
        [Paragraph("<b>2021</b>", tc_s), Paragraph("€ 11.450,00", tc_s), Paragraph("€ 6.816,24", tc_s), Paragraph("<b>€ 4.633,76</b>", tc_red), Paragraph("€ 11.100,00 (96,9%)", tc_s)],
        [Paragraph("<b>TOTALE</b>", tc_bold), Paragraph("<b>€ 71.518,09</b>", tc_bold), Paragraph("<b>€ 40.897,44</b>", tc_bold), Paragraph("<b>€ 30.620,65</b>", tc_red), Paragraph("<b>€ 69.100,00 (96,6%)</b>", tc_bold)],
    ]
    t_table_a = Table(table_a_data, colWidths=[50, 110, 120, 115, 128])
    t_table_a.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8FAFC')]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_table_a)
    story.append(Paragraph("<font size='5.8' color='#64748B'>* Nel 2020 il surplus include quota-parte del maxi-prelievo da € 12.000,00.</font>", body_s))
    story.append(Spacer(1, 2))

    # SCENARIO B & C BOXES
    scen_b_c_data = [
        [Paragraph("<b>SCENARIO B — Fabbisogno Minimo Documentato (€ 435,83 / mese)</b>", ParagraphStyle('SH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary))],
        [Paragraph(
            "<b>Criterio Tecnico:</b> Parametrato sull'anno 2024, in cui il costo reale sostenuto dalla coppia per alimentari, farmaci e utenze è stato di soli € 435,83/mese.<br/>"
            "• <i>Spese di vita minime stimate (72 mesi × € 435,83):</i> <b>€ 31.379,76</b> | <i>Uscite totali:</i> <b>€ 71.518,09</b><br/>"
            "• <b>CAPITALE NETTO DISTRATTO DA RESTITUIRE: € 71.518,09 − € 31.379,76 = </b> <font color='#B91C1C' size='8'><b>€ 40.138,33</b></font>",
            box_p
        )],
        [Paragraph("<b>SCENARIO C — Rigoroso Rendiconto Integrale ex Art. 1713 c.c. (Massima Pretesa Giudiziale)</b>", ParagraphStyle('SH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_red))],
        [Paragraph(
            "<b>Criterio Giuridico:</b> Chi riceve una carta bancaria con PIN per effettuare prelievi agisce quale mandatario di fatto ed è gravato per legge "
            "dall'obbligo di rendiconto analitico ex art. 1713 c.c. e di fedele esecuzione. L'onere della prova delle spese sostenute grava interamente sull'utilizzatore.<br/>"
            "• <i>Maxi-prelievo a vista allo sportello (07/03/2020):</i> <b>€ 12.000,00</b><br/>"
            "• <i>Prelievi ordinari contanti non documentati con fatture/scontrini:</i> <b>€ 57.100,00</b><br/>"
            "• <b>CAPITALE TOTALE DA GIUSTIFICARE O RESTITUIRE PER INTERO: </b> <font color='#B91C1C' size='8'><b>€ 69.100,00</b></font><br/>"
            "• <i>Danno accessorio canoni seconda carta non richiesta (100 mesi a € 0,83):</i> <b>€ 83,00</b>",
            box_p
        )]
    ]
    t_scen_b_c = Table(scen_b_c_data, colWidths=[523])
    t_scen_b_c.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#FEE2E2')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FFF5F5')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('BOX', (0,2), (-1,3), 1, c_red),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_scen_b_c)

    # Pagina 2
    story.append(PageBreak())

    story.append(Paragraph("3. Quadro Sinottico di Sintesi del Capitale Reclamabile", h1_s))
    
    syn_scen_data = [
        [Paragraph("Scenario Difensivo", th_s), Paragraph("Criterio di Calcolo Adottato", th_s), Paragraph("Spese Riconosciute", th_s), Paragraph("Capitale Puro Reclamabile", th_s), Paragraph("Grado di Rischio Processuale", th_s)],
        [Paragraph("<b>Scenario A</b>", tc_bold), Paragraph("Fabbisogno Reale Comprovato 2022-26 (€ 568/m)", tc_s), Paragraph("€ 40.897,44", tc_s), Paragraph("<font color='#B91C1C'><b>€ 30.620,65</b></font>", tc_bold), Paragraph("<font color='#047857'><b>Minimo (Inattaccabile)</b></font>", tc_bold)],
        [Paragraph("<b>Scenario B</b>", tc_bold), Paragraph("Fabbisogno Minimo Accertato 2024 (€ 435/m)", tc_s), Paragraph("€ 31.379,76", tc_s), Paragraph("<font color='#B91C1C'><b>€ 40.138,33</b></font>", tc_bold), Paragraph("Basso (Solido)", tc_bold)],
        [Paragraph("<b>Scenario C</b>", tc_bold), Paragraph("Totale Contanti ex art. 1713 c.c. (Mancato Rendiconto)", tc_s), Paragraph("€ 0,00 (Salvo ricevute)", tc_s), Paragraph("<font color='#B91C1C'><b>€ 69.100,00</b></font>", tc_bold), Paragraph("Subordinato a produzione scontrini", tc_s)],
        [Paragraph("<b>Oneri Seconda Carta</b>", tc_s), Paragraph("Canone € 0,83/mese per seconda Postamat (100 mesi)", tc_s), Paragraph("€ 0,00", tc_s), Paragraph("<b>€ 83,00</b>", tc_bold), Paragraph("<font color='#047857'><b>Zero Rischio (Documentato)</b></font>", tc_bold)],
    ]
    t_syn_scen = Table(syn_scen_data, colWidths=[80, 155, 90, 105, 93])
    t_syn_scen.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1E293B')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_syn_scen)
    story.append(Spacer(1, 4))

    # PARTE 2: LE 4 ANALISI FORENSI AVANZATE
    story.append(Paragraph("4. Le 4 Ulteriori Analisi Forensi Avanzate sugli Estratti Conto", h1_s))

    # Analisi 1
    an1_data = [
        [Paragraph("<b>ANALISI 1: IL 'LAG TEMPORALE' E L'INTERCETTAZIONE DELLA PENSIONE (La Finestra 24 — 72 Ore)</b>", ParagraphStyle('AH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary))],
        [Paragraph(
            "• <b>La Regolarità dell'INPS:</b> L'INPS accredita il trattamento pensionistico con esatta puntualità il primo giorno bancabile del mese.<br/>"
            "• <b>L'Evidenza Documentale del Prelievo:</b> Nel periodo 2016–2021, l'<b>84% di tutti i prelievi contanti da € 600,00</b> veniva effettuato tra il <b>1° e il 4° giorno del mese</b> "
            "(entro 24-72 ore dalla disponibilità della valuta). In numerosi mesi, un secondo prelievo identico da € 600 avveniva entro la metà del mese.<br/>"
            "• <b>Valore Probatorio per il Giudice:</b> Questa condotta non corrisponde ad un'amministrazione di cassa familiare di anziani (le cui spese sono distribuite nel corso delle 4 settimane), "
            "ma costituisce un sistematico <b>'Pension Snatching' (Intercettazione Predatoria della Provvista)</b>: chi deteneva la tessera monitorava il giorno esatto di accredito INPS "
            "e procedeva allo svuotamento istantaneo del conto prima che la provvista potesse consolidarsi.",
            box_p
        )]
    ]
    t_an1 = Table(an1_data, colWidths=[523])
    t_an1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_an1)
    story.append(Spacer(1, 2.5))

    # Analisi 2
    an2_data = [
        [Paragraph("<b>ANALISI 2: LA MAPPA GEOGRAFICA E LA 'MIGRAZIONE' DEGLI SPORTELLI UTILIZZATI</b>", ParagraphStyle('AH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary))],
        [Paragraph(
            "Dalla geolocalizzazione dei codici identificativi dei terminali postali (POS/ATM) riportati negli estratti conto ufficiali, "
            "emerge una netta <b>migrazione per aree geografiche</b> che non trova alcuna correlazione con la residenza stabile della coppia:<br/>"
            "1. <b>Fase 2016 — 2020 (Presidio Branch_Alpha):</b> Operatività concentrata esclusivamente presso l'Ufficio Postale di <b>Branch_Alpha</b> (ATM n. 4095, Cassa 3, Cassa 4);<br/>"
            "2. <b>Fase Inizio 2022 (Presidio Branch_Beta):</b> Improvvisa comparsa dell'ATM n. 8821 di <b>Branch_Beta</b>, teatro dei doppi prelievi a catena in 60 secondi del febbraio 2022;<br/>"
            "3. <b>Fase 2025 — 2026 (Presidio District_North):</b> I prelievi si spostano verso l'ATM n. 650 e la Cassa 6 dell'Ufficio Postale di <b>District_North</b>.<br/>"
            "• <b>Valore Probatorio per il Giudice:</b> Dimostra documentalmente che le carte si muovevano al seguito delle abitudini territoriali e lavorative del <b>terzo utilizzatore</b>, "
            "mentre i coniugi Rossi-Bianchi, per motivi anagrafici e di salute, avevano mobilità urbana limitata o assente.",
            box_p
        )]
    ]
    t_an2 = Table(an2_data, colWidths=[523])
    t_an2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_an2)
    story.append(Spacer(1, 2.5))

    # Analisi 3
    an3_data = [
        [Paragraph("<b>ANALISI 3: SCOMPOSIZIONE DI CANALE — ATM (MACCHINA) VS SPORTELLO FISICO (OPERATORE)</b>", ParagraphStyle('AH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary))],
        [Paragraph(
            "• <b>Prelievi ad ATM Postamat (83% delle operazioni):</b> Eseguiti tramite digitazione PIN in orario mattutino (ore 08:15 — 09:30). "
            "Garantivano l'anonimato visivo dell'operatore, ma lasciano traccia dell'orario preciso al minuto e del numero seriale della carta utilizzata.<br/>"
            "• <b>Prelievi a Sportello Cassa con Operatore Fisico (17% delle operazioni):</b> Cruciali sotto il profilo probatorio perché per ciascuna operazione "
            "Poste Italiane è obbligata ex lege alla conservazione della <b>distinta cartacea firmata</b> e all'identificazione del presentatore:<br/>"
            "&nbsp;&nbsp;− <b>04/06/2019 (Branch_Alpha Cassa 4):</b> Prelievo a sportello di € 500,00 eseguito a soli 9 minuti da un prelievo ATM di € 600;<br/>"
            "&nbsp;&nbsp;− <b>07/03/2020 (Branch_Alpha Cassa 3, ore 09:22):</b> <font color='#B91C1C'><b>MAXI-PRELIEVO DI € 12.000,00 IN BANCONOTE</b></font>;<br/>"
            "&nbsp;&nbsp;− <b>09/08/2025 (District_North Cassa 6):</b> Prelievo di € 500,00 allo sportello.<br/>"
            "• <b>Valore per l'Azione ex art. 119 TUB:</b> L'avvocato ha il diritto potestativo di pretendere da Poste Italiane la copia delle distinte con la firma di chi ha ritirato il contante.",
            box_p
        )]
    ]
    t_an3 = Table(an3_data, colWidths=[523])
    t_an3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_an3)

    # Pagina 3
    story.append(PageBreak())

    # Analisi 4
    an4_data = [
        [Paragraph("<b>ANALISI 4: L'INDICE DI 'CAPACITÀ DI RISPARMIO REPRESSA' (IL TASSO DI ESTRAZIONE PENSIONISTICA)</b>", ParagraphStyle('AH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary))],
        [Paragraph(
            "Questa analisi confronta la percentuale di pensione INPS che usciva dal conto mese per mese nei due periodi storici:<br/>"
            "• <b>Periodo 2016 — 2021 (Era del Drenaggio):</b><br/>"
            "&nbsp;&nbsp;− Entrate Pensionistiche Totali: <b>€ 68.576,40</b><br/>"
            "&nbsp;&nbsp;− Prelievi Contanti Totali: <b>€ 69.100,00</b><br/>"
            "&nbsp;&nbsp;− <b>TASSO MEDIO DI ESTRAZIONE CONTANTI: 100,7%</b> (veniva prelevata la totalità della pensione, oltre a intaccare la giacenza pregressa fino a prosciugarla).<br/>"
            "• <b>Periodo 2022 — 2026 (Era di Gestione Senza Prelievi Seriali):</b><br/>"
            "&nbsp;&nbsp;− Entrate Pensionistiche Totali: <b>€ 59.870,00</b><br/>"
            "&nbsp;&nbsp;− Uscite Complessive Totali: <b>€ 30.673,16</b><br/>"
            "&nbsp;&nbsp;− <b>TASSO REALE DI ASSORBIMENTO: 51,2%</b> (il restante 48,8% è rimasto intonso sul conto, generando i 31.428,90 € attuali).<br/>"
            "• <b>Valore Probatorio Inconfutabile:</b> La forbice tra il <b>100,7%</b> e il <b>51,2%</b> certifica che la capacità di spesa della famiglia non è mai stata di 950-1.400 € al mese: "
            "l'eccedente del 50% veniva sistematicamente drenato dal terzo senza alcuna corrispondenza con i bisogni alimentari o di cura dei due anziani.",
            box_p
        )]
    ]
    t_an4 = Table(an4_data, colWidths=[523])
    t_an4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_an4)
    story.append(Spacer(1, 4))

    # CONCLUSIONI OPERATIVE E PROSPETTO PER L'AVVOCATO
    story.append(Paragraph("5. Conclusioni Operative e Conclusioni Istruttorie per l'Atto di Giudizio", h1_s))
    story.append(Paragraph(
        "Alla luce delle risultanze matematiche e contabili, la strategia processuale per la tutela del patrimonio dei signori Rossi e Bianchi "
        "si articola nei seguenti punti perentori:<br/>"
        "1. <b>Domanda Principale di Ripetizione di Indebito (Solo Capitale):</b> In via principale, richiedere la condanna del terzo alla restituzione "
        "della somma di <b>€ 30.620,65</b> (Scenario A - surplus accertato rispetto al tenore di vita reale) oltre a <b>€ 83,00</b> per oneri seconda carta, "
        "ovvero della maggior somma di <b>€ 40.138,33</b> (Scenario B);<br/>"
        "2. <b>Domanda di Rendiconto ex Art. 1713 c.c. (In via Principale o Istruttoria):</b> Chiedere che il convenuto sia condannato a depositare "
        "il rendiconto dettagliato corredato di pezze giustificative per l'intero importo di <b>€ 69.100,00</b> prelevato in contanti tra il 2016 e il 2021; "
        "in difetto di prova documentale delle spese sostenute nell'interesse dei titolari, condannarlo al pagamento dell'intera differenza non giustificata;<br/>"
        "3. <b>Istanza ex art. 119 TUB e Ordine di Esibizione ex art. 210 c.p.c.:</b> Chiedere al Giudice l'ordine di esibizione nei confronti di Poste Italiane "
        "della distinta originale di cassa relativa al <b>Maxi-Prelievo da € 12.000,00 del 07/03/2020</b> (UP Branch_Alpha Cassa 3) e di quella del 04/06/2019 (Cassa 4), "
        "nonché del modulo contrattuale di richiesta e consegna della seconda carta Postamat (avvenuta nel 2017 e rinnovata nel 2022);<br/>"
        "4. <b>Prescrizione Decennale:</b> Procedere con la notifica dell'atto o di diffida interruttiva <b>senza indugio entro il corrente anno 2026</b> "
        "al fine di impedire la prescrizione delle prime mensilità del 2016.",
        body_s
    ))
    story.append(Spacer(1, 4))

    # Timbro e Certificazione
    cert_data = [
        [Paragraph("<b>CERTIFICAZIONE DI CONFORMITÀ TECNICO-CONTABILE</b>", ParagraphStyle('CH', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary)),
         Paragraph("<b>IL CONSULENTE TECNICO FORENSE</b>", ParagraphStyle('CH2', fontName='Helvetica-Bold', fontSize=7.4, leading=9.4, textColor=c_primary, alignment=2))],
        [Paragraph("I calcoli esposti nel presente elaborato derivano dall'estrazione analitica integrale e senza interpolazioni delle serie storiche documentali (104 pagine complessive) relative al c/c n. 000012345678. La quadratura contabile globale è asseverata con un margine di errore matematico nullo (€ 0,00).", ParagraphStyle('CP', fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=c_dark)),
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
    pdf_file = out_dir / "conteggio_capitale_distratto.pdf"
    build_pdf(str(pdf_file))
    
    # Copia anche in directory brain artifacts
    brain_dir = Path(r"C:\Users\f3d3r\.gemini\antigravity\brain\421db0d3-6198-47cb-ac32-a7c650140e7b")
    if brain_dir.exists():
        shutil.copy(str(pdf_file), str(brain_dir / "conteggio_capitale_distratto.pdf"))
        print(f"[OK] Copiato in artifacts brain: {brain_dir / 'conteggio_capitale_distratto.pdf'}")
