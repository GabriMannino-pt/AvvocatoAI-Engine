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

def find_evidence_targets():
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    
    # 1. Adobe Scan 07 Set 2026.pdf (Op 1 & Op 2)
    doc_adobe = fitz.open(base_dir / "Adobe Scan 07 Set 2026.pdf")
    pix = doc_adobe[0].get_pixmap(dpi=300)
    img_adobe = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    data = pytesseract.image_to_data(img_adobe, lang="ita", output_type=pytesseract.Output.DICT)
    
    print(f"=== Adobe Scan 07 Set 2026 (size: {img_adobe.size}) ===")
    for i in range(len(data["text"])):
        w = data["text"][i].strip().upper()
        if any(k in w for k in ["PENSIONE", "INPS", "AGGIUNTIVA", "COMMISSIONI", "600,00"]):
            x, y, w_b, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            print(f"  Word '{w}' at y={y}, x={x}")
            
    # 2. Check Doc 1 for 12.000 (around page 30) and 04/06/2019 (around page 23)
    doc1 = fitz.open(base_dir / "estratti conto Rossi_Bianchi_1.pdf")
    print("\n=== Scanning Doc 1 Pages 20 to 35 for 12k and 04/06/2019 ===")
    for pno in range(19, 35):
        page = doc1[pno]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        d = pytesseract.image_to_data(img, lang="ita", output_type=pytesseract.Output.DICT)
        for i in range(len(d["text"])):
            w = d["text"][i].strip().upper()
            if any(k in w for k in ["12.000", "12000", "BRANCH_ALPHA", "04/06/19", "04/06/2019", "0002", "0001"]):
                y = d["top"][i]
                print(f"  Doc1 P.{pno+1}: '{w}' at y={y}")

    # 3. Check Doc 2 for Branch_Beta 03/02/2022 (around page 10-18) and Merchant_POS_Demo (around page 48-60)
    doc2 = fitz.open(base_dir / "estratti conto Rossi_Bianchi_2.pdf")
    print("\n=== Scanning Doc 2 for Branch_Beta 03/02/2022, Minimo 11,43 and Merchant_POS_Demo ===")
    for pno in [13, 14, 15, 16, 47, 48, 49, 54, 55, 59, 60]:
        if pno >= len(doc2): continue
        page = doc2[pno]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        d = pytesseract.image_to_data(img, lang="ita", output_type=pytesseract.Output.DICT)
        for i in range(len(d["text"])):
            w = d["text"][i].strip().upper()
            if any(k in w for k in ["8821", "BRANCH_BETA", "11,43", "DONNA", "EFFETTO"]):
                y = d["top"][i]
                print(f"  Doc2 P.{pno+1}: '{w}' at y={y}")

if __name__ == "__main__":
    find_evidence_targets()
