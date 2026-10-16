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
            self.drawString(36, 814, "TRIBUNALE CIVILE E PENALE — ALLEGATO PERITALE: ENTRATE ED USCITE 2016 — 2022")
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
    c_amber = colors.HexColor("#B45309")

    title_s = ParagraphStyle("DocTitle", parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=c_primary, spaceAfter=2)
    sub_s = ParagraphStyle("DocSub", parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.2, leading=11, textColor=c_accent, spaceAfter=4)
    h1_s = ParagraphStyle("H1", parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=c_primary, spaceBefore=5, spaceAfter=3, keepWithNext=True)
    body_s = ParagraphStyle("Body", parent=styles['Normal'], fontName='Helvetica', fontSize=7.2, leading=10, textColor=c_dark, spaceAfter=2)
    body_bold = ParagraphStyle("BodyB", parent=body_s, fontName='Helvetica-Bold')
    box_p = ParagraphStyle("BoxP", parent=body_s, fontName='Helvetica', fontSize=7.1, leading=9.8, textColor=c_dark)
    
    th_s = ParagraphStyle("TH", fontName='Helvetica-Bold', fontSize=6.8, leading=8.8, textColor=colors.white, alignment=1)
    tc_s = ParagraphStyle("TC", fontName='Helvetica', fontSize=6.6, leading=8.5, textColor=c_dark)
    tc_bold = ParagraphStyle("TCB", parent=tc_s, fontName='Helvetica-Bold')
    tc_red = ParagraphStyle("TCR", parent=tc_s, fontName='Helvetica-Bold', textColor=c_red)
    tc_green = ParagraphStyle("TCG", parent=tc_s, fontName='Helvetica-Bold', textColor=c_green)

    story = []

    # Frontespizio
    story.append(Paragraph("RELAZIONE CONTABILE FORENSE: ENTRATE ED USCITE (2016 — 2022)", title_s))
    story.append(Paragraph("ANALISI DELL'ERA DEL MASSIMO DRENAGGIO DEI CONTANTI, IL MAXI-PRELIEVO DA € 12.000 E IL CROLLO A € 11,43", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=4))

    # Meta Table
    meta_table_data = [
        [Paragraph("<b>Fascicolo Giudiziario:</b>", body_s), Paragraph("<b>CASE_001_SYNTHETIC_DEMO</b>", body_bold), Paragraph("<b>Periodo Esaminato:</b>", body_s), Paragraph("<b>01/01/2016 — 31/12/2022 (7 Anni / 84 Mesi)</b>", body_bold)],
        [Paragraph("<b>Rapporto Bancario:</b>", body_s), Paragraph("Conto BancoPosta Più N. <b>000012345678</b>", body_s), Paragraph("<b>Origine Provvista:</b>", body_s), Paragraph("<font color='#047857'><b>100% Pensione INPS Rossi Mario</b></font>", body_bold)],
        [Paragraph("<b>Prelievi Contanti Periodo:</b>", body_s), Paragraph("<font color='#B91C1C'><b>€ 75.600,00 (96,5% delle Uscite)</b></font>", body_bold), Paragraph("<b>Maxi-Prelievo a Vista:</b>", body_s), Paragraph("<font color='#B91C1C'><b>€ 12.000,00 (07/03/2020 Branch_Alpha)</b></font>", body_bold)],
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
    story.append(Paragraph("1. Premessa Metodologica e Inquadramento dell'Era del Massimo Prelievo", h1_s))
    story.append(Paragraph(
        "Il presente allegato peritale certifica in modo analitico e rigoroso i flussi finanziari registrati sul c/c BancoPosta Più n. 000012345678 "
        "negli anni compresi tra il <b>01/01/2016 e il 31/12/2022</b>. Questo settennio costituisce la cosiddetta <b>«Era del Drenaggio Sistematico»</b>, "
        "caratterizzata dall'estrazione reiterata e pressoché totale dei contanti mediante carte Postamat a ridosso dell'accredito mensile INPS.<br/>"
        "La metodologia applicata è quella della quadratura a <i>Zero Silent Correction</i>: ciascun valore contabile è accertato tramite l'identità "
        "<code>Uscite Totali = Saldo Iniziale + Accrediti INPS − Saldo Finale</code>. Da tale formula emerge chiaramente che per l'intero settennio "
        "i prelievi contanti hanno rappresentato il <b>96,5% di tutte le uscite dal conto</b>, lasciando la giacenza stagnante o prosciugandola interamente.",
        body_s
    ))
    story.append(Spacer(1, 3))

    # Dettaglio Anno per Anno
    story.append(Paragraph("2. Schede Analitiche di Riconciliazione Anno per Anno (2016 — 2022)", h1_s))

    # Box 2016
    b_2016 = [
        [Paragraph("<b>ANNO 2016 (L'Inizio dell'Era del Drenaggio Seriale e la Carta *6525)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2015:</b> € 5.173,75<br/>"
            "• <b>Entrate da Pensione INPS nel 2016:</b> + € 10.845,20<br/>"
            "• <b>Saldo Finale al 31/12/2016:</b> € 5.506,55<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 332,80<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 10.845,20 (Entrate) − € 332,80 (Crescita) = <b>€ 10.512,40 USCITE TOTALI ANNUE</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Prelievi Contanti:</i> <font color='#B91C1C'><b>€ 10.200,00</b></font> <b>(il 97,0% di tutte le uscite!)</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Canoni e Oneri Bancari:</i> € 312,40<br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 10.512,40 / 12 mesi = <font color='#B91C1C'><b>€ 876,03 AL MESE</b></font> "
            "(di cui ben <b>€ 850,00 / mese</b> di soli prelievi in contanti!)<br/>"
            "<i>Nota Peritale: Operatività basata sulla Carta Postamat *6525. Prelievi seriali da € 600,00 cad. eseguiti sistematicamente entro 48 ore dall'accredito INPS presso l'ATM 4095 di Branch_Alpha.</i>",
            box_p
        )]
    ]
    t_2016 = Table(b_2016, colWidths=[523])
    t_2016.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2016)
    story.append(Spacer(1, 2.5))

    # Box 2017
    b_2017 = [
        [Paragraph("<b>ANNO 2017 (La Reiterazione Sistematica e il Subentro della Carta *0002)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2016:</b> € 5.506,55<br/>"
            "• <b>Entrate da Pensione INPS nel 2017:</b> + € 11.020,80<br/>"
            "• <b>Saldo Finale al 31/12/2017:</b> € 5.677,35<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 170,80<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 11.020,80 (Entrate) − € 170,80 (Crescita) = <b>€ 10.850,00 USCITE TOTALI ANNUE</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Prelievi Contanti:</i> <font color='#B91C1C'><b>€ 10.400,00</b></font> <b>(il 95,9% di tutte le uscite!)</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Canoni e Oneri Bancari:</i> € 450,00<br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 10.850,00 / 12 mesi = <font color='#B91C1C'><b>€ 904,17 AL MESE</b></font> "
            "(di cui ben <b>€ 866,67 / mese</b> di soli prelievi in contanti!)<br/>"
            "<i>Nota Peritale: A fine 2017 compare la Carta Postamat *0002. Il saldo rimane bloccato attorno a € 5.600 poiché l'intero afflusso pensionistico viene assorbito dai prelievi.</i>",
            box_p
        )]
    ]
    t_2017 = Table(b_2017, colWidths=[523])
    t_2017.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2017)
    story.append(Spacer(1, 2.5))

    # Box 2018
    b_2018 = [
        [Paragraph("<b>ANNO 2018 (Stagnazione della Giacenza e Drenaggio del 96% dell'Assegno)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2017:</b> € 5.677,35<br/>"
            "• <b>Entrate da Pensione INPS nel 2018:</b> + € 11.250,40<br/>"
            "• <b>Saldo Finale al 31/12/2018:</b> € 6.007,75<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 330,40<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 11.250,40 (Entrate) − € 330,40 (Crescita) = <b>€ 10.920,00 USCITE TOTALI ANNUE</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Prelievi Contanti:</i> <font color='#B91C1C'><b>€ 10.500,00</b></font> <b>(il 96,2% di tutte le uscite!)</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Canoni e Oneri Bancari:</i> € 420,00<br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 10.920,00 / 12 mesi = <font color='#B91C1C'><b>€ 910,00 AL MESE</b></font> "
            "(di cui ben <b>€ 875,00 / mese</b> di soli prelievi in contanti!)<br/>"
            "<i>Nota Peritale: Su oltre € 11.250 di pensione accreditata, il patrimonio a fine anno cresce di soli € 330. Totale assenza di pagamenti tracciabili per utenze domestiche o spesa alimentare.</i>",
            box_p
        )]
    ]
    t_2018 = Table(b_2018, colWidths=[523])
    t_2018.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2018)

    # Pagina 2
    story.append(PageBreak())

    # Box 2019
    b_2019 = [
        [Paragraph("<b>ANNO 2019 (La Comparsa della Carta *0001 e il Primo Episodio di Doppia Carta)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2018:</b> € 6.007,75<br/>"
            "• <b>Entrate da Pensione INPS nel 2019:</b> + € 11.520,00<br/>"
            "• <b>Saldo Finale al 31/12/2019:</b> € 6.327,75<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 320,00<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 11.520,00 (Entrate) − € 320,00 (Crescita) = <b>€ 11.200,00 USCITE TOTALI ANNUE</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Prelievi Contanti:</i> <font color='#B91C1C'><b>€ 10.700,00</b></font> <b>(il 95,5% di tutte le uscite!)</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Canoni e Oneri Bancari:</i> € 500,00<br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 11.200,00 / 12 mesi = <font color='#B91C1C'><b>€ 933,33 AL MESE</b></font> "
            "(di cui ben <b>€ 891,67 / mese</b> di soli prelievi in contanti!)<br/>"
            "<i>Nota Peritale: A maggio 2019 subentra la Carta *0001. Il 04/06/2019 si verifica il primo episodio di concorso: prelievo di € 600 con Carta *0001 alle 09:22 "
            "e secondo prelievo di € 500 con Carta *0002 alle 09:31 allo sportello Cassa 4 di Branch_Alpha (€ 1.100 in 9 minuti).</i>",
            box_p
        )]
    ]
    t_2019 = Table(b_2019, colWidths=[523])
    t_2019.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2019)
    story.append(Spacer(1, 2.5))

    # Box 2020 (MAXI PRELIEVO)
    b_2020 = [
        [Paragraph("<b>ANNO 2020 (L'Anno del Maxi-Prelievo da € 12.000 allo Sportello e il Crollo Patrimoniale)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_red))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2019:</b> € 6.327,75<br/>"
            "• <b>Entrate da Pensione INPS nel 2020:</b> + € 11.840,00<br/>"
            "• <b>Saldo Finale al 31/12/2020:</b> € 1.582,06<br/>"
            "• <b>Variazione Patrimoniale Netta:</b> <font color='#B91C1C'><b>− € 4.745,69 (IL CONTO È CROLLATO)</b></font><br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 6.327,75 (Iniziale) + € 11.840,00 (Entrate) − € 1.582,06 (Finale) = <font color='#B91C1C'><b>€ 16.585,69 USCITE TOTALI ANNUE</b></font><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Prelievi Contanti:</i> <font color='#B91C1C'><b>€ 16.200,00</b></font> <b>(compreso il Maxi-Prelievo di € 12.000,00 del 07/03/2020!)</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Canoni e Oneri Bancari:</i> € 385,69<br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 16.585,69 / 12 mesi = <font color='#B91C1C'><b>€ 1.382,14 AL MESE</b></font> "
            "(di cui <b>€ 1.350,00 / mese</b> di prelievi contanti medi!)<br/>"
            "<i>Nota Peritale: Il 07/03/2020 alle 09:22 (Cassa 3 UP Branch_Alpha, Carta *0001) vengono ritirati in banconote allo sportello € 12.000,00 in un solo secondo. "
            "Il saldo precipita da € 13.082,06 a € 1.082,06. Senza il maxi-prelievo straordinario, le spese ordinarie ammontavano a € 382,14/mese.</i>",
            box_p
        )]
    ]
    t_2020 = Table(b_2020, colWidths=[523])
    t_2020.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FEE2E2')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFF5F5')),
        ('BOX', (0,0), (-1,-1), 1, c_red),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2020)
    story.append(Spacer(1, 2.5))

    # Box 2021
    b_2021 = [
        [Paragraph("<b>ANNO 2021 (La Ripresa del Drenaggio a Ciclo Mensile da € 900–1.000)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2020:</b> € 1.582,06<br/>"
            "• <b>Entrate da Pensione INPS nel 2021:</b> + € 12.100,00<br/>"
            "• <b>Saldo Finale al 31/12/2021:</b> € 2.232,06<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 650,00<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 12.100,00 (Entrate) − € 650,00 (Crescita) = <b>€ 11.450,00 USCITE TOTALI ANNUE</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Prelievi Contanti:</i> <font color='#B91C1C'><b>€ 11.100,00</b></font> <b>(il 96,9% di tutte le uscite!)</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Canoni e Oneri Bancari:</i> € 350,00<br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 11.450,00 / 12 mesi = <font color='#B91C1C'><b>€ 954,17 AL MESE</b></font> "
            "(di cui ben <b>€ 925,00 / mese</b> di soli prelievi in contanti!)<br/>"
            "<i>Nota Peritale: Dopo il prosciugamento del 2020, l'attività predatoria riprende a ritmo pieno, asportando oltre il 91% di ciascun assegno pensionistico accreditato.</i>",
            box_p
        )]
    ]
    t_2021 = Table(b_2021, colWidths=[523])
    t_2021.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_2021)
    story.append(Spacer(1, 2.5))

    # Box 2022
    b_2022 = [
        [Paragraph("<b>ANNO 2022 (L'Anno di Svolta / Change Point: Doppi Prelievi, Crollo a € 11,43 e Stop Prelievi)</b>", ParagraphStyle('BH', fontName='Helvetica-Bold', fontSize=7.6, leading=9.6, textColor=c_primary))],
        [Paragraph(
            "• <b>Saldo Iniziale al 31/12/2021:</b> € 2.232,06<br/>"
            "• <b>Entrate da Pensione INPS nel 2022:</b> + € 12.450,00<br/>"
            "• <b>Saldo Finale al 31/12/2022:</b> € 7.861,43<br/>"
            "• <b>Crescita Patrimoniale Netta:</b> + € 5.629,37<br/>"
            "• <b>Calcolo Matematico Uscite Totali:</b> € 12.450,00 (Entrate) − € 5.629,37 (Crescita) = <b>€ 6.820,63 USCITE TOTALI ANNUE</b><br/>"
            "&nbsp;&nbsp;↳ <i>di cui Prelievi Contanti:</i> <b>€ 6.500,00</b> (concentrati nei primi mesi)<br/>"
            "&nbsp;&nbsp;↳ <i>di cui Canoni e Oneri Bancari:</i> € 320,63<br/>"
            "• <b>Media Mensile Totale (TUTTO COMPRESO):</b> € 6.820,63 / 12 mesi = <b>€ 568,39 AL MESE</b> (Prelievi: € 541,67 / mese)<br/>"
            "<i>Nota Peritale: A febbraio 2022 si verificano i doppi prelievi simultanei in 60 secondi con due carte a Branch_Beta (€ 1.200 il 03/02 e € 1.200 il 25/02). "
            "L'08/03/2022 il saldo crolla al minimo storico assoluto di <b>€ 11,43</b>. Da quel momento i prelievi seriali cessano e il saldo sale a € 7.861 a fine anno.</i>",
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

    # Pagina 3: Quadro Sinottico, Comparazione Forense e Valore Giuridico
    story.append(PageBreak())
    story.append(Paragraph("3. Quadro Riassuntivo Sinottico del Periodo di Drenaggio (2016 — 2022)", h1_s))

    synoptic_data = [
        [Paragraph("Anno", th_s), Paragraph("Saldo Iniziale", th_s), Paragraph("Entrate INPS", th_s), Paragraph("Saldo Finale", th_s), Paragraph("Variazione Saldo", th_s), Paragraph("Uscite Totali", th_s), Paragraph("Prelievi Contanti", th_s), Paragraph("Incid. %", th_s), Paragraph("Media Uscite/Mese", th_s)],
        [Paragraph("<b>2016</b>", tc_s), Paragraph("€ 5.173,75", tc_s), Paragraph("€ 10.845,20", tc_s), Paragraph("€ 5.506,55", tc_s), Paragraph("+ € 332,80", tc_green), Paragraph("€ 10.512,40", tc_s), Paragraph("€ 10.200,00", tc_red), Paragraph("97,0%", tc_bold), Paragraph("<b>€ 876,03</b>", tc_bold)],
        [Paragraph("<b>2017</b>", tc_s), Paragraph("€ 5.506,55", tc_s), Paragraph("€ 11.020,80", tc_s), Paragraph("€ 5.677,35", tc_s), Paragraph("+ € 170,80", tc_green), Paragraph("€ 10.850,00", tc_s), Paragraph("€ 10.400,00", tc_red), Paragraph("95,9%", tc_bold), Paragraph("<b>€ 904,17</b>", tc_bold)],
        [Paragraph("<b>2018</b>", tc_s), Paragraph("€ 5.677,35", tc_s), Paragraph("€ 11.250,40", tc_s), Paragraph("€ 6.007,75", tc_s), Paragraph("+ € 330,40", tc_green), Paragraph("€ 10.920,00", tc_s), Paragraph("€ 10.500,00", tc_red), Paragraph("96,2%", tc_bold), Paragraph("<b>€ 910,00</b>", tc_bold)],
        [Paragraph("<b>2019</b>", tc_s), Paragraph("€ 6.007,75", tc_s), Paragraph("€ 11.520,00", tc_s), Paragraph("€ 6.327,75", tc_s), Paragraph("+ € 320,00", tc_green), Paragraph("€ 11.200,00", tc_s), Paragraph("€ 10.700,00", tc_red), Paragraph("95,5%", tc_bold), Paragraph("<b>€ 933,33</b>", tc_bold)],
        [Paragraph("<b>2020</b>", tc_s), Paragraph("€ 6.327,75", tc_s), Paragraph("€ 11.840,00", tc_s), Paragraph("€ 1.582,06", tc_s), Paragraph("<font color='#B91C1C'><b>− € 4.745,69</b></font>", tc_red), Paragraph("€ 16.585,69", tc_red), Paragraph("€ 16.200,00*", tc_red), Paragraph("97,7%", tc_bold), Paragraph("<b>€ 1.382,14</b>", tc_red)],
        [Paragraph("<b>2021</b>", tc_s), Paragraph("€ 1.582,06", tc_s), Paragraph("€ 12.100,00", tc_s), Paragraph("€ 2.232,06", tc_s), Paragraph("+ € 650,00", tc_green), Paragraph("€ 11.450,00", tc_s), Paragraph("€ 11.100,00", tc_red), Paragraph("96,9%", tc_bold), Paragraph("<b>€ 954,17</b>", tc_bold)],
        [Paragraph("<b>2022</b>", tc_s), Paragraph("€ 2.232,06", tc_s), Paragraph("€ 12.450,00", tc_s), Paragraph("€ 7.861,43", tc_s), Paragraph("+ € 5.629,37", tc_green), Paragraph("€ 6.820,63", tc_s), Paragraph("€ 6.500,00", tc_s), Paragraph("95,3%", tc_bold), Paragraph("<b>€ 568,39</b>", tc_bold)],
        [Paragraph("<b>TOTALE</b>", tc_bold), Paragraph("<b>€ 5.173,75</b>", tc_bold), Paragraph("<b>€ 81.026,40</b>", tc_bold), Paragraph("<b>€ 7.861,43</b>", tc_bold), Paragraph("<b>+ € 2.687,68</b>", tc_green), Paragraph("<b>€ 78.338,72</b>", tc_bold), Paragraph("<b>€ 75.600,00</b>", tc_red), Paragraph("<b>96,5%</b>", tc_bold), Paragraph("<b>€ 932,60 / m</b>", tc_bold)],
    ]
    t_synoptic = Table(synoptic_data, colWidths=[40, 58, 62, 58, 65, 60, 64, 42, 74])
    t_synoptic.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_accent),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, c_accent),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8FAFC')]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_synoptic)
    story.append(Spacer(1, 1))
    story.append(Paragraph("<font size='6' color='#64748B'>* Include il Maxi-Prelievo di € 12.000,00 eseguito a sportello il 07/03/2020 presso l'UP di Branch_Alpha (Cassa 3, Carta *0001).</font>", body_s))
    story.append(Spacer(1, 4))

    # Sezione Confronto Diretto
    story.append(Paragraph("4. Confronto Forense: Era del Drenaggio (2016–2021) vs Era Post-Svolta (2023–2026)", h1_s))
    
    comp_data = [
        [Paragraph("Parametro Contabile / Forense", th_s), Paragraph("Periodo 2016 — 2021 (Drenaggio Seriale)", th_s), Paragraph("Periodo 2023 — 2026 (Accumulo Passivo)", th_s), Paragraph("Differenza Forense Accertata", th_s)],
        [Paragraph("<b>Frequenza Prelievi</b>", tc_bold), Paragraph("18 — 22 prelievi l'anno (sistematici post-INPS)", tc_s), Paragraph("3 — 5 prelievi l'anno (trimestri interi a zero)", tc_s), Paragraph("<font color='#047857'><b>Crollo dell'80% delle estrazioni</b></font>", tc_bold)],
        [Paragraph("<b>Media Prelievi Contanti</b>", tc_bold), Paragraph("<b>€ 850,00 — € 1.350,00 al mese</b>", tc_red), Paragraph("<b>€ 350,00 — € 400,00 al mese</b>", tc_green), Paragraph("<font color='#B91C1C'><b>Surplus prelevato: € 500 — € 800/mese</b></font>", tc_bold)],
        [Paragraph("<b>Uscite Totali dal Conto</b>", tc_bold), Paragraph("<b>€ 876,00 — € 1.382,00 al mese</b>", tc_red), Paragraph("<b>€ 435,00 — € 710,00 al mese</b>", tc_green), Paragraph("<font color='#047857'><b>Fabbisogno reale medio: € 568/mese</b></font>", tc_bold)],
        [Paragraph("<b>Evoluzione Giacenza</b>", tc_bold), Paragraph("Stagnante a € 5.000, poi crollo a € 1.582 (2020) e € 11,43 (2022)", tc_s), Paragraph("Esplosione da € 2.232 ad <b>€ 31.428,90</b> al 30/06/2026", tc_green), Paragraph("<font color='#047857'><b>Accumulo di + € 29.196,84</b></font>", tc_bold)],
        [Paragraph("<b>Incidenza Contante su Uscite</b>", tc_bold), Paragraph("<b>96,5%</b> di tutte le somme uscite dal conto", tc_red), Paragraph("Circa <b>50% — 60%</b> (comparsa spese POS tracciate)", tc_s), Paragraph("Totale anomalia nel settennio 2016-2022", tc_bold)],
    ]
    t_comp = Table(comp_data, colWidths=[120, 135, 135, 133])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#334155')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 4))

    # Valore Probatorio e Inquadramento Giuridico
    story.append(Paragraph("5. Conclusioni Probatorie per l'Azione Giudiziaria", h1_s))
    story.append(Paragraph(
        "Dalla comparazione scientifica dei due settenni scaturiscono tre pilastri probatori inattaccabili a sostegno della difesa:<br/>"
        "1. <b>Superamento della Presunzione di Contitolarità (Art. 1298 c.c.):</b> La totalità delle entrate (€ 81.026,40 nel 2016-2022 ed "
        "€ 128.450,00 nel decennio) proviene esclusivamente dalla pensione INPS del Signor Rossi Mario. Ai sensi di <i>Cass. Ord. n. 31052/2024</i> "
        "e <i>Cass. n. 9721/2020</i>, l'intero saldo e tutte le somme prelevate appartengono di diritto al solo titolare della provvista;<br/>"
        "2. <b>Prova Scientifica della Spoliazione (Indebito Arricchimento / Appropriazione Indebita):</b> Gli estratti conto degli anni successivi (2023-2026) "
        "dimostrano in modo inoppugnabile che il fabbisogno vitale effettivo della coppia ammontava a soli <b>€ 435 — € 568 mensili</b>. "
        "Pertanto, i prelievi di € 850 — 1.350 mensili eseguiti nel periodo 2016-2021 non rispondevano a bisogni della coppia, ma integravano una <b>distrazione "
        "ingiustificata di circa € 36.000,00</b> di somme pensionistiche, oltre al maxi-prelievo da € 12.000,00;<br/>"
        "3. <b>Obbligo di Rendiconto e Ripetizione dell'Indebito (Artt. 1713 e 2033 c.c.):</b> Chiunque abbia detenuto le carte Postamat con PIN o abbia "
        "effettuato i prelievi per conto degli anziani è tenuto per legge a <b>rendicontare la destinazione di ciascun singolo euro</b>; in difetto di prova documentale "
        "di spese sostenute nell'interesse esclusivo del pensionato, le somme dovranno essere integralmente restituite.",
        body_s
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generato con successo: {output_pdf_path}")

if __name__ == "__main__":
    out_dir = Path(r"d:\Progetti\AVVOCATO_AI\fascicoli\CASE_001_SYNTHETIC_DEMO\perizia_output")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_file = out_dir / "Entrate_Uscite_2016_2022.pdf"
    build_pdf(str(pdf_file))
    
    # Copia anche in directory brain artifacts
    brain_dir = Path(r"C:\Users\f3d3r\.gemini\antigravity\brain\421db0d3-6198-47cb-ac32-a7c650140e7b")
    if brain_dir.exists():
        shutil.copy(str(pdf_file), str(brain_dir / "Entrate_Uscite_2016_2022.pdf"))
        print(f"[OK] Copiato in artifacts brain: {brain_dir / 'Entrate_Uscite_2016_2022.pdf'}")
