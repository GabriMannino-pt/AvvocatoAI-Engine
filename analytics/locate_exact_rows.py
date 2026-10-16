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

def locate():
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    
    # 1. Look for 12.000 in Doc 1 (Pages 25 to 40)
    doc1 = fitz.open(base_dir / "estratti conto Rossi_Bianchi_1.pdf")
    print(">>> Searching Doc 1 for 12.000 / 07/03/20...", flush=True)
    for pno in range(20, 38):
        pix = doc1[pno].get_pixmap(dpi=120)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        txt = pytesseract.image_to_string(img, lang="ita")
        for line in txt.split("\n"):
            l_u = line.upper()
            if any(k in l_u for k in ["12.000", "12000", "07/03/20", "07/03/2020", "04/06/19", "04/06/2019", "CASSA 3", "CASSA 4"]):
                print(f"  [Doc1 P.{pno+1}] {line.strip()}", flush=True)

    # 2. Look for Branch_Beta 03/02/22 and 11,43 in Doc 2
    doc2 = fitz.open(base_dir / "estratti conto Rossi_Bianchi_2.pdf")
    print("\n>>> Searching Doc 2 for Branch_Beta / 11,43 / Merchant_POS_Demo...", flush=True)
    for pno in range(10, 25):
        pix = doc2[pno].get_pixmap(dpi=120)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        txt = pytesseract.image_to_string(img, lang="ita")
        for line in txt.split("\n"):
            l_u = line.upper()
            if any(k in l_u for k in ["03/02/22", "03/02/2022", "25/02/22", "8821", "11,43", "08/03/22"]):
                print(f"  [Doc2 P.{pno+1}] {line.strip()}", flush=True)

if __name__ == "__main__":
    locate()
