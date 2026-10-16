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

def inspect_exact_periods():
    pdf_path = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input/estratti conto Rossi_Bianchi_2.pdf")
    doc = fitz.open(pdf_path)
    
    # Let's inspect pages 18 to 45
    # Period 1: April 2022 - December 2022 (pages 18 to 26)
    # Period 2: November 2023 - July 2024 (pages 33 to 42)
    
    print("=== PERIOD 1: APRIL 2022 - DECEMBER 2022 ===", flush=True)
    for pno in range(18, 26):
        pix = doc[pno].get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        txt = pytesseract.image_to_string(img, lang="ita")
        lines = txt.split("\n")
        print(f"--- PAGE {pno+1} ---", flush=True)
        for l in lines:
            lu = l.upper()
            if any(k in lu for k in ["PAGAMENTO", "POS", "CANONE", "SPESE", "BOLLO", "COMMISSIONE", "ADDEBITO", "FARMAC", "CONAD", "MD", "COOP", "EUROSPIN", "ENEL", "PRELIEVO"]):
                print(f"  {l.strip()}", flush=True)

    print("\n=== PERIOD 2: NOVEMBER 2023 - JULY 2024 ===", flush=True)
    for pno in range(32, 42):
        pix = doc[pno].get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        txt = pytesseract.image_to_string(img, lang="ita")
        lines = txt.split("\n")
        print(f"--- PAGE {pno+1} ---", flush=True)
        for l in lines:
            lu = l.upper()
            if any(k in lu for k in ["PAGAMENTO", "POS", "CANONE", "SPESE", "BOLLO", "COMMISSIONE", "ADDEBITO", "FARMAC", "CONAD", "MD", "COOP", "EUROSPIN", "ENEL", "PRELIEVO"]):
                print(f"  {l.strip()}", flush=True)

if __name__ == "__main__":
    inspect_exact_periods()
