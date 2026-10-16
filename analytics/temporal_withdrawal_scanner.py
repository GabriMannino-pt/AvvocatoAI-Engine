# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["OPENBLAS_NUM_THREADS"] = "1"
from core.config import settings
import fitz
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
os.environ["TESSDATA_PREFIX"] = str(settings.tessdata_dir)

def scan_2022_2026_withdrawals():
    pdf_path = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input/estratti conto Rossi_Bianchi_2.pdf")
    doc = fitz.open(pdf_path)
    print(f"Scanning Doc 2 ({len(doc)} pages) for PRELIEVO and ACCREDITO/PENSIONE in 2022-2026...", flush=True)
    
    events = []
    
    # Doc 2 pages 15 to 63 cover 2021 to 2026
    for pno in range(15, len(doc)):
        pix = doc[pno].get_pixmap(dpi=130)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        try:
            text = pytesseract.image_to_string(img, lang="ita")
        except Exception as e:
            continue
            
        for line in text.split("\n"):
            line_u = line.upper()
            if any(k in line_u for k in ["PRELIEVO", "POSTAMAT", "ACCREDITO", "PENSIONE", "INPS"]):
                # check if year is 22, 23, 24, 25, 26 or 2022, 2023, etc.
                if any(yr in line for yr in ["/22", "/23", "/24", "/25", "/26", "/2022", "/2023", "/2024", "/2025", "/2026"]):
                    events.append({
                        "page": pno + 1,
                        "line": line.strip()
                    })
                    print(f"[P.{pno+1}] {line.strip()}", flush=True)

    print(f"\nTotal lines matched: {len(events)}", flush=True)

if __name__ == "__main__":
    scan_2022_2026_withdrawals()
