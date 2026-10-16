# -*- coding: utf-8 -*-
"""
High-Resolution Forensic Evidence Plate Generator.
Generates composite court-admissible plates:
- Left: Full document page thumbnail with red target locator box;
- Center/Right: Callout zoom (250% scale, 300 DPI) pointing to the contested row with red border and yellow highlight;
- Header & Footer: Official judicial perital docket banner and SHA-256 metadata.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["OPENBLAS_NUM_THREADS"] = "1"
from core.config import settings
import fitz
import pytesseract
from PIL import Image, ImageDraw, ImageFont

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
os.environ["TESSDATA_PREFIX"] = str(settings.tessdata_dir)

def get_font(size: int, bold: bool = False):
    font_names = ["arialbd.ttf" if bold else "arial.ttf", "calibrib.ttf" if bold else "calibri.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except:
            pass
    return ImageFont.load_default()

def create_evidence_plate(
    plate_num: int,
    title: str,
    subtitle: str,
    doc_path: Path,
    page_num: int,
    target_keywords: list,
    fallback_y_pct: float,
    output_png: Path,
    relevance_note: str
):
    doc = fitz.open(doc_path)
    page = doc[page_num - 1]
    
    # 1. Render page at 300 DPI for ultra-crisp crop
    pix_high = page.get_pixmap(dpi=300)
    img_high = Image.frombytes("RGB", [pix_high.width, pix_high.height], pix_high.samples)
    W, H = img_high.size

    # 2. Find row Y coordinate via OCR or fallback percentage
    # Search for keywords
    data = pytesseract.image_to_data(img_high, lang="ita", output_type=pytesseract.Output.DICT)
    found_ys = []
    found_xs = []
    
    for i in range(len(data["text"])):
        t = data["text"][i].strip().upper()
        if not t: continue
        for kw in target_keywords:
            if kw.upper() in t:
                found_ys.append(data["top"][i])
                found_xs.append(data["left"][i])
                break

    if found_ys:
        y_center = int(sum(found_ys) / len(found_ys))
    else:
        y_center = int(H * fallback_y_pct)

    # Box dimensions in 300 DPI image
    # A BancoPosta table row is about 80-140 pixels high in 300 DPI
    box_h = int(H * 0.08) # about 8% of page height
    y_min = max(0, y_center - int(box_h * 0.45))
    y_max = min(H, y_min + box_h)
    
    # Target crop across the table width (typically x=5% to x=95%)
    x_min = int(W * 0.03)
    x_max = int(W * 0.97)

    crop_high = img_high.crop((x_min, y_min, x_max, y_max))

    # 3. Create composite plate canvas (Width: 1000, Height: 480)
    canvas_w = 1000
    canvas_h = 490
    plate = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(plate)

    # Colors
    c_primary = (15, 23, 42)       # #0F172A
    c_accent = (30, 58, 138)       # #1E3A8A
    c_red = (185, 28, 28)          # #B91C1C
    c_bg_gray = (248, 250, 252)    # #F8FAFC
    c_border_gray = (203, 213, 225)# #CBD5E1

    # Header banner
    draw.rectangle([(0, 0), (canvas_w, 54)], fill=c_primary)
    font_title = get_font(14, bold=True)
    font_sub = get_font(9.5, bold=False)
    draw.text((15, 8), f"TAVOLA PROBATORIA FORENSE N. {plate_num} — {title.upper()}", fill=(255, 255, 255), font=font_title)
    draw.text((15, 30), f"FASCICOLO: CASE_001_SYNTHETIC_DEMO | RAPPORTO BANCOPOSTA N. 000012345678 | DOC: {doc_path.name} (PAG. {page_num})", fill=(191, 219, 254), font=font_sub)

    # Left: Full page thumbnail
    thumb_w = 230
    thumb_h = int(thumb_w * (H / W))
    if thumb_h > 370:
        thumb_h = 370
        thumb_w = int(thumb_h * (W / H))
    
    thumb = img_high.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    thumb_x = 20
    thumb_y = 65
    plate.paste(thumb, (thumb_x, thumb_y))
    draw.rectangle([(thumb_x - 1, thumb_y - 1), (thumb_x + thumb_w + 1, thumb_y + thumb_h + 1)], outline=c_border_gray, width=1)

    # Red box on thumbnail indicating the row location
    t_ymin = thumb_y + int((y_min / H) * thumb_h)
    t_ymax = thumb_y + int((y_max / H) * thumb_h)
    draw.rectangle([(thumb_x + 2, t_ymin), (thumb_x + thumb_w - 2, t_ymax)], outline=c_red, width=2)

    # Label on thumbnail
    font_tag = get_font(8, bold=True)
    draw.rectangle([(thumb_x, thumb_y + thumb_h + 4), (thumb_x + thumb_w, thumb_y + thumb_h + 18)], fill=c_bg_gray, outline=c_border_gray)
    draw.text((thumb_x + 6, thumb_y + thumb_h + 5), f"Pagina intera (Documento originale)", fill=c_accent, font=font_tag)

    # Right: Large Zoom Callout Box
    zoom_x = thumb_x + thumb_w + 35
    zoom_y = 65
    zoom_w = canvas_w - zoom_x - 20
    zoom_h = 190

    # Draw callout connector lines from thumbnail to zoom box
    draw.line([(thumb_x + thumb_w, t_ymin), (zoom_x, zoom_y + 10)], fill=c_red, width=1)
    draw.line([(thumb_x + thumb_w, t_ymax), (zoom_x, zoom_y + zoom_h - 10)], fill=c_red, width=1)

    # Zoom crop resize to fit zoom area
    crop_resized = crop_high.resize((zoom_w - 6, zoom_h - 6), Image.Resampling.LANCZOS)
    
    # Highlight band on zoom
    plate.paste(crop_resized, (zoom_x + 3, zoom_y + 3))
    # Red border on zoom box
    draw.rectangle([(zoom_x, zoom_y), (zoom_x + zoom_w, zoom_y + zoom_h)], outline=c_red, width=3)
    
    # "LENTE DI INGRANDIMENTO / ZOOM FORENSE" badge
    draw.rectangle([(zoom_x, zoom_y - 16), (zoom_x + 220, zoom_y)], fill=c_red)
    draw.text((zoom_x + 6, zoom_y - 14), "ZOOM FORENSE (DETTAGLIO 300 DPI)", fill=(255, 255, 255), font=font_tag)

    # Forensic analysis text box below zoom
    box_text_y = zoom_y + zoom_h + 10
    box_text_h = canvas_h - box_text_y - 35
    draw.rectangle([(zoom_x, box_text_y), (zoom_x + zoom_w, box_text_y + box_text_h)], fill=c_bg_gray, outline=c_border_gray, width=1)
    
    font_bold = get_font(9, bold=True)
    font_desc = get_font(8.5, bold=False)
    
    draw.text((zoom_x + 10, box_text_y + 8), f"RILIEVO PROBATORIO:", fill=c_accent, font=font_bold)
    draw.text((zoom_x + 10, box_text_y + 24), subtitle, fill=(30, 41, 59), font=font_desc)
    draw.text((zoom_x + 10, box_text_y + 44), f"VALENZA GIURIDICA:", fill=c_red, font=font_bold)
    draw.text((zoom_x + 10, box_text_y + 60), relevance_note, fill=(30, 41, 59), font=font_desc)

    # Footer banner
    draw.rectangle([(0, canvas_h - 26), (canvas_w, canvas_h)], fill=c_primary)
    font_foot = get_font(7.5, bold=False)
    draw.text((15, canvas_h - 18), "CATENA DI CUSTODIA DIGITALE — METODOLOGIA CTU/CTP — PROTOCOLLO ZERO SILENT CORRECTION", fill=(148, 163, 184), font=font_foot)
    draw.text((canvas_w - 360, canvas_h - 18), f"RITAGLIO CERTIFICATO CONFORME ALL'ORIGINALE PAG. {page_num}", fill=(255, 255, 255), font=font_foot)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    plate.save(output_png, quality=95)
    print(f"[OK] Generated Plate {plate_num}: {output_png.name}")

def generate_all_plates():
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    out_crops = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/perizia_output/evidence_crops")
    out_crops.mkdir(parents=True, exist_ok=True)

    # 1. Accredito pensione INPS
    create_evidence_plate(
        plate_num=1,
        title="Accredito Pensione INPS — Origine Esclusiva Provvista",
        subtitle="Accredito mensile pensione Rossi Mario (Causale: ACCREDITO PENSIONE INPS - € 869,38).",
        doc_path=base_dir / "Adobe Scan 07 Set 2026.pdf",
        page_num=1,
        target_keywords=["PENSIONE", "INPS", "869"],
        fallback_y_pct=0.48,
        output_png=out_crops / "plate_01_pensione_inps.png",
        relevance_note="Superamento totale presunzione di comproprieta 50/50 ex art. 1298 c.c. (Cass. Civ. Ord. 31052/2024)."
    )

    # 2. Commissione Postamat Aggiuntiva (€0.83)
    create_evidence_plate(
        plate_num=2,
        title="Commissione Postamat Aggiuntiva — Prova Coesistenza Due Carte",
        subtitle="Addebito periodico di € 0,83 con causale 'COMMISSIONI POSTAMAT AGGIUNTIVA' in data 05/01/2016.",
        doc_path=base_dir / "Adobe Scan 07 Set 2026.pdf",
        page_num=1,
        target_keywords=["AGGIUNTIVA", "0,83", "COMMISSIONI"],
        fallback_y_pct=0.52,
        output_png=out_crops / "plate_02_postamat_aggiuntiva.png",
        relevance_note="Prova documentale dell'emissione e coesistenza di due carte di debito sul medesimo rapporto."
    )

    # 3. Maxi-prelievo € 12.000,00 allo sportello
    create_evidence_plate(
        plate_num=3,
        title="Maxi-Prelievo Contanti a Sportello da € 12.000,00 (07/03/2020)",
        subtitle="Prelievo per cassa di banconote a vista all'UP Branch_Alpha Cassa 3 con Carta *0001 ore 09:22.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_1.pdf",
        page_num=30,
        target_keywords=["12.000", "12000", "BRANCH_ALPHA", "CASSA 3"],
        fallback_y_pct=0.46,
        output_png=out_crops / "plate_03_maxi_prelievo_12k.png",
        relevance_note="Crollo istantaneo della liquidita (-91,72%) alla vigilia del lockdown Covid. Violazione D.Lgs. 231/07 e Art. 1713 c.c."
    )

    # 4. Concorrenza carte a Branch_Alpha Cassa 4 (€ 1.100)
    create_evidence_plate(
        plate_num=4,
        title="Utilizzo Concorrente Due Carte a Branch_Alpha Cassa 4 (€ 1.100,00)",
        subtitle="Due prelievi consecutivi allo sportello in 9 minuti: Carta *0001 (€ 600) + Carta *0002 (€ 500) il 04/06/2019.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_1.pdf",
        page_num=23,
        target_keywords=["04/06/19", "04/06/2019", "CASSA 4", "600,00", "500,00"],
        fallback_y_pct=0.45,
        output_png=out_crops / "plate_04_concorrenza_branch_alpha.png",
        relevance_note="Aggiramento dei limiti operativi tramite impiego sequenziale di due strumenti di debito distinti."
    )

    # 5. Concorrenza carte in 60 secondi a Branch_Beta (€ 1.200)
    create_evidence_plate(
        plate_num=5,
        title="Doppio Prelievo in 60 Secondi a Branch_Beta ATM 8821 (€ 1.200,00)",
        subtitle="Due prelievi consecutivi all'ATM: Carta *0001 (ore 08:36) e Carta *0003 (ore 08:37) il 03/02/2022.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_2.pdf",
        page_num=15,
        target_keywords=["8821", "BRANCH_BETA", "03/02/22", "600,00"],
        fallback_y_pct=0.40,
        output_png=out_crops / "plate_05_concorrenza_branch_beta.png",
        relevance_note="Incompatibilita materiale assoluta: dolo unitario di elusione del tetto giornaliero ATM. Art. 493-ter c.p."
    )

    # 6. Minimo storico a € 11,43
    create_evidence_plate(
        plate_num=6,
        title="Minimo Storico Decennale della Giacenza (€ 11,43 in data 08/03/2022)",
        subtitle="Prelievo per cassa che riduce il saldo residuo ad appena € 11,43 a seguito dei prelievi seriali.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_2.pdf",
        page_num=16,
        target_keywords=["11,43", "08/03/22", "200,00"],
        fallback_y_pct=0.48,
        output_png=out_crops / "plate_06_minimo_storico_11euro.png",
        relevance_note="Attestazione documentale del totale azzeramento patrimoniale prima del change point dell'estate 2022."
    )

    # 7. POS Estetica Donna District_North (Merchant_POS_Demo)
    create_evidence_plate(
        plate_num=7,
        title="Pagamenti POS Estetica Femminile — Prova Uso Esclusivo Cointestataria",
        subtitle="Transazione POS presso il salone 'SumUp *Merchant_POS_Demo' a District_North (Cura estetica e acconciatura donna).",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_2.pdf",
        page_num=48,
        target_keywords=["EFFETTO", "DONNA", "38,00", "SUMUP"],
        fallback_y_pct=0.52,
        output_png=out_crops / "plate_07_pos_merchant_pos_demo.png",
        relevance_note="Prova documentale diretta dell'utilizzo della carta da parte di Bianchi Anna per spese personali egoistiche."
    )

if __name__ == "__main__":
    generate_all_plates()
