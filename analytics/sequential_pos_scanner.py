# -*- coding: utf-8 -*-
"""
Sequential, Memory-Efficient POS Scanner for Case CASE_001_SYNTHETIC_DEMO.
Renders one page at a time at 110 DPI, releases memory, and searches for POS / merchant transactions.
"""
import os
import sys
import gc
import json
import time
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

def scan_all():
    docs = [
        "Adobe Scan 07 Set 2026.pdf",
        "estratti conto Rossi_Bianchi_1.pdf",
        "estratti conto Rossi_Bianchi_2.pdf"
    ]
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    out_file = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/perizia_output/pos_investigation_results.json")
    
    pos_matches = []
    t0 = time.time()
    total_pages = 0
    
    for doc_name in docs:
        pdf_path = base_dir / doc_name
        if not pdf_path.exists():
            continue
        doc = fitz.open(pdf_path)
        print(f"\n>>> SCANNING: {doc_name} ({len(doc)} pages)", flush=True)
        
        for pno in range(len(doc)):
            total_pages += 1
            page = doc[pno]
            # 110 DPI is fast and light on RAM
            pix = page.get_pixmap(dpi=110)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            del pix
            
            try:
                text = pytesseract.image_to_string(img, lang="ita")
            except Exception as e:
                print(f"  [P.{pno+1}] OCR Error: {e}", flush=True)
                del img
                gc.collect()
                continue
                
            del img
            gc.collect()
            
            # Check if this page is a movements page
            is_movement_page = any(w in text.upper() for w in ["MOVIMENTI", "OPERAZIONI", "ESTRATTO CONTO AL", "DATA CONTABILE"])
            
            # Search for any merchant / POS keywords
            for line in text.split("\n"):
                l_clean = line.strip()
                l_u = l_clean.upper()
                if not l_u:
                    continue
                if any(x in l_u for x in ["SCONTI BANCOPOSTA", "NEGOZI CONVENZIONATI", "LIMITAZIONI", "INFORMATIV"]):
                    continue
                # Specific keywords
                if any(w in l_u for w in [
                    "PAGAMENTO", "PAGAM.", "P.O.S", "POS ", "COMMERC", "ESERC",
                    "ACQUIST", "SUPERMERC", "FARMAC", "BENZIN", "CARBURAN", "DISTRIBUT",
                    "CONAD", "COOP", "EUROSPIN", "LIDL", "CRAI", "DECO"
                ]):
                    print(f"  [MATCH Pag.{pno+1}]: {l_clean}", flush=True)
                    pos_matches.append({
                        "doc": doc_name,
                        "page": pno + 1,
                        "is_movement_page": is_movement_page,
                        "line": l_clean
                    })
                    
            if (pno + 1) % 10 == 0 or (pno + 1) == len(doc):
                print(f"  Scanned {pno+1}/{len(doc)} pages of {doc_name} (elapsed: {time.time()-t0:.1f}s)...", flush=True)

    print(f"\n=== SCAN COMPLETED in {time.time()-t0:.1f}s ===", flush=True)
    print(f"Total pages scanned: {total_pages}", flush=True)
    print(f"Total potential POS entries detected: {len(pos_matches)}", flush=True)
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(pos_matches, f, indent=2, ensure_ascii=False)
    print(f"Results saved in: {out_file}", flush=True)

if __name__ == "__main__":
    scan_all()
