# -*- coding: utf-8 -*-
import os
import sys
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
            self.drawString(36, 814, "TRIBUNALE CIVILE E PENALE — ALLEGATO PERITALE: ENTRATE ED USCITE 2022 — 2026")
            self.drawRightString(559, 814, "FASC. CASE_001_SYNTHETIC_DEMO | C/C 000012345678")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 808, 559, 808)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 32, 559, 32)
        
        self.drawString(36, 22, "Standard Metodologico Forense CTU/CTP — Zero Silent Correction — Quadratura Matematica al Centesimo")
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

    title_s = ParagraphStyle("DocTitle", parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14.5, leading=18.5, textColor=c_primary, spaceAfter=3)
    sub_s = ParagraphStyle("DocSub", parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11.5, textColor=c_accent, spaceAfter=5)
    h1_s = ParagraphStyle("H1", parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10, leading=13.5, textColor=c_primary, spaceBefore=7, spaceAfter=3, keepWithNext=True)
    body_s = ParagraphStyle("Body", parent=styles['Normal'], fontName='Helvetica', fontSize=7.3, leading=10.2, textColor=c_dark, spaceAfter=2.5)
    body_bold = ParagraphStyle("BodyB", parent=body_s, fontName='Helvetica-Bold')
    box_p = ParagraphStyle("BoxP", parent=body_s, fontName='Helvetica', fontSize=7.3, leading=10.4, textColor=c_dark)
    
    th_s = ParagraphStyle("TH", fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.white, alignment=1)
    tc_s = ParagraphStyle("TC", fontName='Helvetica', fontSize=6.8, leading=8.8, textColor=c_dark)
    tc_bold = ParagraphStyle("TCB", parent=tc_s, fontName='Helvetica-Bold')
    tc_green = ParagraphStyle("TCG", parent=tc_s, fontName='Helvetica-Bold', textColor=c_green)

    story = []

    # Frontespizio
    story.append(Paragraph("RELAZIONE CONTABILE FORENSE: ENTRATE ED USCITE (2022 — 2026)", title_s))
    story.append(Paragraph("ANALISI COMPARATIVA DEL FABBISOGNO REALE, CROLLO DEI PRELIEVI E DINAMICA DELL'ACCUMULO PASSIVO", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=4))

    # Meta Table
    meta_table_data = [
        [Paragraph("<b>Fascicolo Giudiziario:</b>", body_s), Paragraph("<b>CASE_001_SYNTHETIC_DEMO</b>", body_bold), Paragraph("<b>Periodo Esaminato:</b>", body_s), Paragraph("<b>01/01/2022 — 30/06/2026 (54 Mesi)</b>", body_bold)],
        [Paragraph("<b>Rapporto Bancario:</b>", body_s), Paragraph("Conto BancoPosta Piu N. <b>000012345678</b>", body_s), Paragraph("<b>Origine Provvista:</b>", body_s), Paragraph("<font color='#047857'><b>100% Pensione INPS Rossi Mario</b></font>", body_bold)],
        [Paragraph("<b>Codice IBAN:</b>", body_s), Paragraph("<code>IT60 X 07601 01000 000012345678</code>", body_s), Paragraph("<b>Accumulo Netto Periodo:</b>", body_s), Paragraph("<font color='#047857'><b>+ € 29.196,84</b></font>", body_bold)],
        [Paragraph("<b>Intestatari Ufficiali:</b>", body_s), Paragraph("ROSSI MARIO — BIANCHI ANNA", body_s), Paragraph("<b>Stato Quadratura:</b>", body_s), Paragraph("<font color='#047857'><b>CONFERMATA AL CENTESIMO (€ 0,00)</b></font>", body_bold)],
    ]
    t_meta = Table(meta_table_data, colWidths=[95, 175, 100, 153])
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

    # Introduzione
    story.append(Paragraph("1. Premessa Metodologica e Obiettivo della Ricostruzione", h1_s))
    story.append(Paragraph(
        "Il presente allegato peritale certifica in modo analitico, per ciascun anno solare compreso tra il <b>2022 e il 30 giugno 2026</b>, "
        "il volume esatto delle <b>entrate pensionistiche INPS</b> accreditate a favore del Signor Rossi Mario, "
        "la variazione effettiva della giacenza del conto corrente BancoPosta Piu n. 000012345678, e le <b>uscite totali annue e mensili</b> "
        "(comprensive di prelievi contanti, pagamenti tramite circuito POS ed oneri bancari di tenuta conto).<br/>"
        "Tale ricostruzione fornisce al Giudice la <b>prova quantitativa e scientifica del fabbisogno reale di vita della coppia di anziani</b>: "
        "dimostrando che nel quinquennio in cui i prelievi non autorizzati sono cessati, la coppia ha vissuto con una media complessiva di circa <b>€ 568 al mese</b>, "
        "smentendo categoricamente che negli anni 2016-2021 occorressero oltre € 950-1.400 mensili.",
        body_s
    ))
    story.append(Spacer(1, 3))

    # Dettaglio Anno per Anno
    story.append(Paragraph("2. Schede Analitiche di Riconciliazione Anno per Anno (2022 — 2026)", h1_s))

    # Box 2022
    b_2022 = [
        [Paragraph("<b>ANNO 2022 (L'Anno del Cambio di Rotta e della Flessione dei Prelievi)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.8, leading=9.8, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2021:</b> € 2.232,06<br/>"
            "• <b>Entrate da Pensione INPS nel 2022:</b> + € 12.450,00<br/>"
            "• <b>Saldo Finale al 31/12/2022:</b> € 7.861,43<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 5.629,37<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 12.450,00 (Entrate) − € 5.629,37 (Crescita) = <b>€ 6.820,63 USCITE TOTALI ANNUE</b><br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 6.820,63 / 12 mesi = <font color='#B91C1C'><b>€ 568,39 AL MESE</b></font><br/>"
            "<i>Nota Peritale: Nel primo trimestre 2022 si concentrano ancora gli ultimi prelievi seriali (doppi prelievi a Branch_Beta) e si registra il minimo storico di € 11,43 in data 08/03/2022. "
            "Da maggio 2022 i prelievi si arrestano drasticamente e la spesa reale della seconda meta dell'anno scende a circa € 300/mese.</i>",
            box_p
        )]
    ]
    t_2022 = Table(b_2022, colWidths=[523])
    t_2022.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2022)
    story.append(Spacer(1, 3))

    # Box 2023
    b_2023 = [
        [Paragraph("<b>ANNO 2023 (L'Anno dell'Accumulo Pieno e Stabilizzato)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.8, leading=9.8, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2022:</b> € 7.861,43<br/>"
            "• <b>Entrate da Pensione INPS nel 2023:</b> + € 13.120,00<br/>"
            "• <b>Saldo Finale al 31/12/2023:</b> € 15.571,43<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 7.710,00<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 13.120,00 (Entrate) − € 7.710,00 (Crescita) = <b>€ 5.410,00 USCITE TOTALI ANNUE</b><br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 5.410,00 / 12 mesi = <font color='#047857'><b>€ 450,83 AL MESE</b></font><br/>"
            "<i>Nota Peritale: Le uscite complessive (contanti + spese POS per supermercato e farmacia) scendono a soli € 450 mensili, permettendo la conservazione di quasi il 60% della pensione.</i>",
            box_p
        )]
    ]
    t_2023 = Table(b_2023, colWidths=[523])
    t_2023.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2023)
    story.append(Spacer(1, 3))

    # Box 2024
    b_2024 = [
        [Paragraph("<b>ANNO 2024 (La Conferma Definitiva del Fabbisogno Minimo Ordinario)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.8, leading=9.8, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2023:</b> € 15.571,43<br/>"
            "• <b>Entrate da Pensione INPS nel 2024:</b> + € 13.650,00<br/>"
            "• <b>Saldo Finale al 31/12/2024:</b> € 23.991,43<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 8.420,00<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 13.650,00 (Entrate) − € 8.420,00 (Crescita) = <b>€ 5.230,00 USCITE TOTALI ANNUE</b><br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 5.230,00 / 12 mesi = <font color='#047857'><b>€ 435,83 AL MESE</b></font><br/>"
            "<i>Nota Peritale: In quest'anno si registra il fabbisogno mensile piu basso dell'intero decennio (€ 435/mese). La giacenza sul conto supera per la prima volta € 20.000.</i>",
            box_p
        )]
    ]
    t_2024 = Table(b_2024, colWidths=[523])
    t_2024.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2024)
    story.append(Spacer(1, 3))

    # Box 2025
    b_2025 = [
        [Paragraph("<b>ANNO 2025 (La Salita a Quota 29.000 € e Subentro Nuova Carta)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.8, leading=9.8, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2024:</b> € 23.991,43<br/>"
            "• <b>Entrate da Pensione INPS nel 2025:</b> + € 14.150,00<br/>"
            "• <b>Saldo Finale al 31/12/2025:</b> € 29.621,43<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 5.630,00<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 14.150,00 (Entrate) − € 5.630,00 (Crescita) = <b>€ 8.520,00 USCITE TOTALI ANNUE</b><br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 8.520,00 / 12 mesi = <font color='#1E3A8A'><b>€ 710,00 AL MESE</b></font><br/>"
            "<i>Nota Peritale: Nonostante una lieve ripresa dei prelievi estivi e il subentro della Carta *8984, il saldo a fine anno tocca il record di € 29.621,43.</i>",
            box_p
        )]
    ]
    t_2025 = Table(b_2025, colWidths=[523])
    t_2025.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2025)
    story.append(Spacer(1, 3))

    # Box 2026 (Semestre)
    b_2026 = [
        [Paragraph("<b>ANNO 2026 (Primo Semestre: 01/01/2026 — 30/06/2026 = 6 Mesi)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.8, leading=9.8, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2025:</b> € 29.621,43<br/>"
            "• <b>Entrate da Pensione INPS nel primo semestre 2026:</b> + € 6.500,00<br/>"
            "• <b>Saldo Finale al 30/06/2026:</b> € 31.428,90<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 1.807,47<br/>"
            "• <b>Calcolo Matematico Uscite Semestrali:</b> € 6.500,00 (Entrate) − € 1.807,47 (Crescita) = <b>€ 4.692,53 USCITE TOTALI DEL SEMESTRE</b><br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 4.692,53 / 6 mesi = <font color='#1E3A8A'><b>€ 782,09 AL MESE</b></font><br/>"
            "<i>Nota Peritale: Chiusura definitiva del decennio con saldo record di € 31.428,90 e quadratura perfetta al centesimo certificata con Poste Italiane.</i>",
            box_p
        )]
    ]
    t_2026 = Table(b_2026, colWidths=[523])
    t_2026.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2026)
    story.append(Spacer(1, 4))

    # Pagina 2: Quadro Riassuntivo e Rilevanza Giudiziaria
    story.append(PageBreak())
    story.append(Paragraph("3. Quadro Riassuntivo dell'Era di Accumulo (2022 — 2026)", h1_s))

    summary_data = [
        [Paragraph("Anno / Periodo", th_s), Paragraph("Saldo Iniziale", th_s), Paragraph("Entrate INPS", th_s), Paragraph("Saldo Finale", th_s), Paragraph("Incremento Netto", th_s), Paragraph("Uscite TOTALI (Annue)", th_s), Paragraph("Media Mensile (TUTTO INCLUSO)", th_s)],
        [Paragraph("<b>2022</b>", tc_s), Paragraph("€ 2.232,06", tc_s), Paragraph("€ 12.450,00", tc_s), Paragraph("€ 7.861,43", tc_s), Paragraph("+ € 5.629,37", tc_green), Paragraph("€ 6.820,63", tc_s), Paragraph("<b>€ 568,39 / mese</b>", tc_bold)],
        [Paragraph("<b>2023</b>", tc_s), Paragraph("€ 7.861,43", tc_s), Paragraph("€ 13.120,00", tc_s), Paragraph("€ 15.571,43", tc_s), Paragraph("+ € 7.710,00", tc_green), Paragraph("€ 5.410,00", tc_s), Paragraph("<b>€ 450,83 / mese</b>", tc_green)],
        [Paragraph("<b>2024</b>", tc_s), Paragraph("€ 15.571,43", tc_s), Paragraph("€ 13.650,00", tc_s), Paragraph("€ 23.991,43", tc_s), Paragraph("+ € 8.420,00", tc_green), Paragraph("€ 5.230,00", tc_s), Paragraph("<b>€ 435,83 / mese</b>", tc_green)],
        [Paragraph("<b>2025</b>", tc_s), Paragraph("€ 23.991,43", tc_s), Paragraph("€ 14.150,00", tc_s), Paragraph("€ 29.621,43", tc_s), Paragraph("+ € 5.630,00", tc_green), Paragraph("€ 8.520,00", tc_s), Paragraph("<b>€ 710,00 / mese</b>", tc_bold)],
        [Paragraph("<b>2026 (6 Mesi)</b>", tc_s), Paragraph("€ 29.621,43", tc_s), Paragraph("€ 6.500,00", tc_s), Paragraph("€ 31.428,90", tc_s), Paragraph("+ € 1.807,47", tc_green), Paragraph("€ 4.692,53", tc_s), Paragraph("<b>€ 782,09 / mese</b>", tc_bold)],
        [Paragraph("<b>TOTALE PERIODO</b>", tc_bold), Paragraph("<b>€ 2.232,06</b>", tc_bold), Paragraph("<b>€ 59.870,00</b>", tc_bold), Paragraph("<b>€ 31.428,90</b>", tc_bold), Paragraph("<b>+ € 29.196,84</b>", tc_green), Paragraph("<b>€ 30.673,16</b>", tc_bold), Paragraph("<b>€ 568,02 / mese (Media Globale)</b>", tc_bold)],
    ]
    t_summary = Table(summary_data, colWidths=[70, 70, 75, 75, 75, 78, 80])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8FAFC')]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 5))

    # Rilevanza Forense e Giudiziaria
    story.append(Paragraph("4. Il Valore Probatorio Definitivo per il Tribunale e la Difesa Legale", h1_s))
    story.append(Paragraph(
        "L'analisi scientifica dei 54 mesi compresi tra il 2022 e il 2026 fornisce al Consulente Tecnico di Parte e all'Avvocato difensore "
        "tre conclusioni probatorie insuperabili da produrre in giudizio:<br/>"
        "1. <b>Accertamento del Fabbisogno Reale:</b> Negli ultimi 4 anni e mezzo, per provvedere a <b>TUTTE le esigenze di vita</b> della coppia "
        "(spesa alimentare, farmaci, bollette, contante tascabile e canoni bancari), sono usciti dal conto in media <b>€ 568,02 al mese</b> "
        "(con minimi di appena € 435 — 450 mensili negli anni 2023-2024);<br/>"
        "2. <b>Il Divario Ingiustificato con il Periodo Precedente (2016 — 2021):</b> Nei 6 anni anteriori al change point uscivano dal conto "
        "in media <b>€ 920,00 — € 1.380,00 al mese</b> (oltre al maxi-prelievo da € 12.000 in data 07/03/2020);<br/>"
        "3. <b>La Prova della Predazione Sistematica:</b> Tale evidenza certifica che tra il 2016 e il 2021 venivano prelevati ogni mese "
        "<b>tra i 350 e gli 800 euro in piu</b> rispetto alle reali necessita vitali dei due anziani. Tale surplus (pari a circa € 36.000 in 6 anni, "
        "cui si somma il maxi-prelievo da € 12.000, per complessivi <b>€ 48.000,00 di drenaggio ingiustificato</b>) e imputabile in via esclusiva "
        "alla gestione infedele di chi deteneva materialmente le carte Postamat, e costituisce debito risarcitorio e restitutorio ex artt. 1713 e 2033 c.c.",
        body_s
    ))
    story.append(Spacer(1, 4))

    # Box formula legale per il Giudice
    formula_box = [
        [Paragraph("<b>LA DICHIARAZIONE A VERBALE DA OFFRIRE AL GIUDICE</b>", ParagraphStyle('FH', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_accent))],
        [Paragraph(
            "<i>\"Signor Giudice, i numeri certificati escludono qualsiasi equivoco: negli anni 2023 e 2024, per far vivere dignitosamente i due anziani, "
            "pagare la spesa alimentare al supermercato MD e le medicine alla Farmacia Patane, sono usciti in totale solo € 440 al mese. "
            "La presenza di oltre € 31.400 sul conto e la prova materiale che le uscite si sono dimezzate non appena la persona di fiducia ha smesso di prelevare. "
            "I prelievi di € 950 al mese effettuati prima del 2022 e il prelievo a vista di € 12.000 non servivano affatto per gli anziani, "
            "ma costituivano una sistematica spoliazione del patrimonio di Rossi Mario, soggetta ad obbligo di integrale restituzione.\"</i>",
            ParagraphStyle('FP', fontName='Helvetica-Oblique', fontSize=7.3, leading=10.5, textColor=c_dark)
        )]
    ]
    t_formula = Table(formula_box, colWidths=[523])
    t_formula.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_formula)
    story.append(Spacer(1, 4))

    # Certificato finale
    story.append(Paragraph("5. Attestazione Peritale e Catena di Custodia", h1_s))
    story.append(Paragraph(
        "Si attesta che tutti i dati finanziari sopra esposti sono stati calcolati matematicamente a partire dagli estratti conto ufficiali "
        "di Poste Italiane S.p.A. acquisiti nel fascicolo CASE_001_SYNTHETIC_DEMO. La riconciliazione contabile chiude con un delta pari a € 0,00.",
        body_s
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF successfully generated at: {output_pdf_path}")

if __name__ == '__main__':
    out_file = 'fascicoli/CASE_001_SYNTHETIC_DEMO/perizia_output/Entrate_Uscite_2022_2026.pdf'
    build_pdf(out_file)

