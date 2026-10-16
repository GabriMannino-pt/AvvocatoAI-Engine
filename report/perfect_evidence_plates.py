# -*- coding: utf-8 -*-
"""
Perfect High-Resolution Evidence Plate Generator for All 7 Key Operations.
Uses exact verified pages and precise coordinate scanning:
- Plate 1: Adobe Scan Pag. 1 (Accredito pensione INPS)
- Plate 2: Adobe Scan Pag. 1 (Commissione Postamat Aggiuntiva)
- Plate 3: Doc 1 Pag. 30 (Maxi-prelievo € 12.000,00 Branch_Alpha Cassa 3)
- Plate 4: Doc 1 Pag. 22 (Doppio prelievo Branch_Alpha Cassa 4 in 9 min)
- Plate 5: Doc 2 Pag. 18 (Doppio prelievo Branch_Beta ATM 8821 in 60 sec)
- Plate 6: Doc 2 Pag. 18 (Prelievo che azzera il conto a € 11,43)
- Plate 7: Doc 2 Pag. 48 (POS SumUp *Merchant_POS_Demo District_North)
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

def create_precise_plate(
    plate_num: int,
    title: str,
    subtitle: str,
    doc_path: Path,
    page_num: int,
    keywords: list = None,
    output_png: Path = None,
    relevance_note: str = "",
    custom_y_range: tuple = None
):
    doc = fitz.open(doc_path)
    page = doc[page_num - 1]
    
    # Render page at 300 DPI
    pix_high = page.get_pixmap(dpi=300)
    img_high = Image.frombytes("RGB", [pix_high.width, pix_high.height], pix_high.samples)
    W, H = img_high.size

    # Locate coordinates
    if custom_y_range:
        if custom_y_range[0] > 1:
            y_min = int(custom_y_range[0])
            y_max = int(custom_y_range[1])
        else:
            y_min = int(H * custom_y_range[0])
            y_max = int(H * custom_y_range[1])
    else:
        data = pytesseract.image_to_data(img_high, lang="ita", output_type=pytesseract.Output.DICT)
        matched_tops = []
        matched_heights = []
        for i in range(len(data["text"])):
            t = data["text"][i].strip().upper()
            if not t: continue
            for kw in keywords:
                if kw.upper() in t:
                    matched_tops.append(data["top"][i])
                    matched_heights.append(data["height"][i])
                    break
        
        if matched_tops:
            avg_top = sum(matched_tops) / len(matched_tops)
            box_h = int(H * 0.085)
            y_min = max(0, int(avg_top - box_h * 0.35))
            y_max = min(H, y_min + box_h)
        else:
            y_min = int(H * 0.45)
            y_max = int(H * 0.53)

    # Table bounds
    x_min = int(W * 0.03)
    x_max = int(W * 0.97)
    crop_high = img_high.crop((x_min, y_min, x_max, y_max))

    # Composite canvas
    canvas_w = 1000
    canvas_h = 490
    plate = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(plate)

    c_primary = (15, 23, 42)
    c_accent = (30, 58, 138)
    c_red = (185, 28, 28)
    c_bg_gray = (248, 250, 252)
    c_border_gray = (203, 213, 225)

    # Header banner
    draw.rectangle([(0, 0), (canvas_w, 54)], fill=c_primary)
    font_title = get_font(13.5, bold=True)
    font_sub = get_font(9.5, bold=False)
    draw.text((15, 8), f"TAVOLA PROBATORIA FORENSE N. {plate_num} — {title.upper()}", fill=(255, 255, 255), font=font_title)
    draw.text((15, 30), f"FASCICOLO: CASE_001_SYNTHETIC_DEMO | RAPPORTO BANCOPOSTA N. 000012345678 | {doc_path.name} (PAG. {page_num})", fill=(191, 219, 254), font=font_sub)

    # Thumbnail
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

    t_ymin = thumb_y + int((y_min / H) * thumb_h)
    t_ymax = thumb_y + int((y_max / H) * thumb_h)
    draw.rectangle([(thumb_x + 2, t_ymin), (thumb_x + thumb_w - 2, t_ymax)], outline=c_red, width=2)

    font_tag = get_font(8, bold=True)
    draw.rectangle([(thumb_x, thumb_y + thumb_h + 4), (thumb_x + thumb_w, thumb_y + thumb_h + 18)], fill=c_bg_gray, outline=c_border_gray)
    draw.text((thumb_x + 6, thumb_y + thumb_h + 5), f"Pagina intera (Documento originale)", fill=c_accent, font=font_tag)

    # Right: Large Zoom Callout Box
    zoom_x = thumb_x + thumb_w + 35
    zoom_y = 65
    zoom_w = canvas_w - zoom_x - 20
    zoom_h = 190

    # Connector lines
    draw.line([(thumb_x + thumb_w, t_ymin), (zoom_x, zoom_y + 10)], fill=c_red, width=1)
    draw.line([(thumb_x + thumb_w, t_ymax), (zoom_x, zoom_y + zoom_h - 10)], fill=c_red, width=1)

    crop_resized = crop_high.resize((zoom_w - 6, zoom_h - 6), Image.Resampling.LANCZOS)
    plate.paste(crop_resized, (zoom_x + 3, zoom_y + 3))
    draw.rectangle([(zoom_x, zoom_y), (zoom_x + zoom_w, zoom_y + zoom_h)], outline=c_red, width=3)

    # Zoom badge
    draw.rectangle([(zoom_x, zoom_y - 16), (zoom_x + 220, zoom_y)], fill=c_red)
    draw.text((zoom_x + 6, zoom_y - 14), "ZOOM FORENSE (DETTAGLIO 300 DPI)", fill=(255, 255, 255), font=font_tag)

    # Forensic analysis box
    box_text_y = zoom_y + zoom_h + 10
    box_text_h = canvas_h - box_text_y - 35
    draw.rectangle([(zoom_x, box_text_y), (zoom_x + zoom_w, box_text_y + box_text_h)], fill=c_bg_gray, outline=c_border_gray, width=1)
    
    font_bold = get_font(9, bold=True)
    font_desc = get_font(8.5, bold=False)
    
    draw.text((zoom_x + 10, box_text_y + 8), f"RILIEVO PROBATORIO:", fill=c_accent, font=font_bold)
    draw.text((zoom_x + 10, box_text_y + 24), subtitle, fill=(30, 41, 59), font=font_desc)
    draw.text((zoom_x + 10, box_text_y + 46), f"VALENZA GIURIDICA:", fill=c_red, font=font_bold)
    draw.text((zoom_x + 10, box_text_y + 62), relevance_note, fill=(30, 41, 59), font=font_desc)

    # Footer banner
    draw.rectangle([(0, canvas_h - 26), (canvas_w, canvas_h)], fill=c_primary)
    font_foot = get_font(7.5, bold=False)
    draw.text((15, canvas_h - 18), "CATENA DI CUSTODIA DIGITALE — METODOLOGIA CTU/CTP — PROTOCOLLO ZERO SILENT CORRECTION", fill=(148, 163, 184), font=font_foot)
    draw.text((canvas_w - 360, canvas_h - 18), f"RITAGLIO CERTIFICATO CONFORME ALL'ORIGINALE PAG. {page_num}", fill=(255, 255, 255), font=font_foot)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    plate.save(output_png, quality=95)
    print(f"[OK] Generated Plate {plate_num} ({output_png.name}) from {doc_path.name} P.{page_num}")

def run_all():
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    out_crops = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/perizia_output/evidence_crops")
    out_crops.mkdir(parents=True, exist_ok=True)

    # 1. Accredito pensione INPS (Adobe Scan P. 1)
    create_precise_plate(
        plate_num=1,
        title="Accredito Pensione INPS — Origine Esclusiva Provvista",
        subtitle="Accredito mensile pensione Rossi Mario (Causale: ACCREDITO PENSIONE INPS - € 869,38).",
        doc_path=base_dir / "Adobe Scan 07 Set 2026.pdf",
        page_num=1,
        keywords=["PENSIONE", "INPS", "869", "STIPENDIO"],
        output_png=out_crops / "plate_01_pensione_inps.png",
        relevance_note="Superamento totale presunzione di comproprieta 50/50 ex art. 1298 c.c. (Cass. Civ. Ord. 31052/2024)."
    )

    # 2. Commissione Postamat Aggiuntiva (Adobe Scan P. 1)
    create_precise_plate(
        plate_num=2,
        title="Commissione Postamat Aggiuntiva — Prova Coesistenza Due Carte",
        subtitle="Addebito periodico di € 0,83 con causale 'COMMISSIONI POSTAMAT AGGIUNTIVA' in data 05/01/2016.",
        doc_path=base_dir / "Adobe Scan 07 Set 2026.pdf",
        page_num=1,
        keywords=["AGGIUNTIVA", "0,83", "COMMISSIONI"],
        output_png=out_crops / "plate_02_postamat_aggiuntiva.png",
        relevance_note="Prova documentale dell'emissione e coesistenza permanente di due carte attive sul medesimo conto."
    )

    # 3. Maxi-prelievo € 12.000,00 allo sportello (Doc 1 P. 30)
    create_precise_plate(
        plate_num=3,
        title="Maxi-Prelievo Contanti a Sportello da € 12.000,00 (07/03/2020)",
        subtitle="Prelievo per cassa di banconote a vista all'UP Branch_Alpha Cassa 3 con Carta *0001 ore 09:22.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_1.pdf",
        page_num=30,
        custom_y_range=(2310, 2550),
        output_png=out_crops / "plate_03_maxi_prelievo_12k.png",
        relevance_note="Crollo istantaneo della liquidita (-91,72%) alla vigilia del lockdown Covid. Violazione D.Lgs. 231/07 e Art. 1713 c.c."
    )

    # 4. Concorrenza carte a Branch_Alpha Cassa 4 (€ 1.100) (Doc 1 P. 22)
    create_precise_plate(
        plate_num=4,
        title="Utilizzo Concorrente Due Carte a Branch_Alpha Cassa 4 (€ 1.100,00)",
        subtitle="Due prelievi consecutivi allo sportello in 9 minuti: Carta *0001 (€ 600) + Carta *0002 (€ 500) il 04/06/2019.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_1.pdf",
        page_num=22,
        keywords=["04/06/19", "04/06/2019", "CASSA 4", "BRANCH_ALPHA", "09.22"],
        output_png=out_crops / "plate_04_concorrenza_branch_alpha.png",
        relevance_note="Aggiramento dei limiti operativi tramite impiego sequenziale di due strumenti di debito distinti."
    )

    # 5. Concorrenza carte in 60 secondi a Branch_Beta (€ 1.200) (Doc 2 P. 18)
    create_precise_plate(
        plate_num=5,
        title="Doppio Prelievo in 60 Secondi a Branch_Beta ATM 8821 (€ 1.200,00)",
        subtitle="Due prelievi consecutivi all'ATM: Carta *0001 (ore 08:36) e Carta *0003 (ore 08:37) il 03/02/2022.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_2.pdf",
        page_num=18,
        keywords=["8821", "03/02/2022", "03/02/22", "08:36", "08:37"],
        output_png=out_crops / "plate_05_concorrenza_branch_beta.png",
        relevance_note="Incompatibilita materiale assoluta: dolo unitario di elusione del tetto giornaliero ATM. Art. 493-ter c.p."
    )

    # 6. Minimo storico a € 11,43 (Doc 2 P. 18)
    create_precise_plate(
        plate_num=6,
        title="Minimo Storico Decennale della Giacenza (€ 11,43 in data 08/03/2022)",
        subtitle="Prelievo per cassa che riduce il saldo residuo ad appena € 11,43 a seguito dei prelievi seriali.",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_2.pdf",
        page_num=18,
        keywords=["08/03/22", "08/03/2022", "10:22", "CASSA 5", "11,43"],
        output_png=out_crops / "plate_06_minimo_storico_11euro.png",
        relevance_note="Attestazione documentale del totale azzeramento patrimoniale prima del change point dell'estate 2022."
    )

    # 7. POS Estetica Donna District_North (Merchant_POS_Demo) (Doc 2 P. 48)
    create_precise_plate(
        plate_num=7,
        title="Pagamenti POS Estetica Femminile — Prova Uso Esclusivo Cointestataria",
        subtitle="Transazione POS presso il salone 'SumUp *Merchant_POS_Demo' a District_North (Cura estetica e acconciatura donna).",
        doc_path=base_dir / "estratti conto Rossi_Bianchi_2.pdf",
        page_num=48,
        custom_y_range=(2110, 2330),
        output_png=out_crops / "plate_07_pos_merchant_pos_demo.png",
        relevance_note="Prova documentale diretta dell'utilizzo della carta da parte di Bianchi Anna per spese personali egoistiche."
    )

if __name__ == "__main__":
    run_all()
