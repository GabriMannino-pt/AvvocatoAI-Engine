# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Add app_engine to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["OPENBLAS_NUM_THREADS"] = "1"
from core.config import settings
import fitz
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
os.environ["TESSDATA_PREFIX"] = str(settings.tessdata_dir)

def scan_for_pos():
    docs = [
        "Adobe Scan 07 Set 2026.pdf",
        "estratti conto Rossi_Bianchi_1.pdf",
        "estratti conto Rossi_Bianchi_2.pdf"
    ]
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    
    all_pos = []
    
    for doc_name in docs:
        pdf_path = base_dir / doc_name
        if not pdf_path.exists():
            continue
        doc = fitz.open(pdf_path)
        print(f"=== Scanning {doc_name} ({len(doc)} pages) ===")
        
        for pno in range(len(doc)):
            page = doc[pno]
            # 130 DPI for fast keyword scan
            pix = page.get_pixmap(dpi=130)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            try:
                text = pytesseract.image_to_string(img, lang="ita")
            except Exception as e:
                print(f"Error on page {pno+1}: {e}")
                continue
                
            for line in text.split("\n"):
                line_u = line.upper()
                if any(x in line_u for x in ["SCONTI BANCOPOSTA", "NEGOZI CONVENZIONATI", "LIMITAZIONI", "INFORMATIV"]):
                    continue
                # Look for POS payments or merchant names
                if any(w in line_u for w in [
                    "PAGAMENTO", "PAGAM.", "P.O.S", "POS ", "COMMERC", "ESERC",
                    "ACQUIST", "SUPERMERC", "FARMAC", "BENZIN", "CARBURAN", "DISTRIBUT"
                ]):
                    # Discard false positives like 'SPORTELLO POSTALE' or 'POSTAMAT' unless it also has POS purchase
                    # Note: in Italian BancoPosta, cash withdrawal at counter says 'PRELIEVO POSTAMAT POS UFFICIO POSTALE'
                    # which is a CASH WITHDRAWAL at the postal counter POS terminal, NOT a purchase!
                    all_pos.append({
                        "doc": doc_name,
                        "page": pno + 1,
                        "line": line.strip()
                    })
                    print(f"[{doc_name} P.{pno+1}] {line.strip()}")
                    
    print(f"\nTotal potential POS matches found: {len(all_pos)}")
    for m in all_pos:
        print(m)

if __name__ == "__main__":
    scan_for_pos()
