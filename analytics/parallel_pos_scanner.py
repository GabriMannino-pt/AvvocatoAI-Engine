# -*- coding: utf-8 -*-
"""
Fast Parallel POS & Card Purchase Scanner for Case CASE_001_SYNTHETIC_DEMO.
Scans all 104 pages with multi-threading to find any POS payments or merchant transactions.
"""
import os
import sys
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["OPENBLAS_NUM_THREADS"] = "1"
from core.config import settings
import fitz
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
os.environ["TESSDATA_PREFIX"] = str(settings.tessdata_dir)

def process_page(args):
    doc_name, pno, pix_bytes, width, height = args
    img = Image.frombytes("RGB", [width, height], pix_bytes)
    try:
        text = pytesseract.image_to_string(img, lang="ita")
    except Exception as e:
        return doc_name, pno, f"ERROR: {e}", []

    lines = text.split("\n")
    matches = []
    
    for line in lines:
        l_clean = line.strip()
        l_u = l_clean.upper()
        if not l_u:
            continue
            
        # Filter out informational footer
        if any(x in l_u for x in ["SCONTI BANCOPOSTA", "NEGOZI CONVENZIONATI", "LIMITAZIONI", "INFORMATIV"]):
            continue
            
        # Target keywords
        keywords = [
            "PAGAMENTO", "PAGAM.", "P.O.S", "POS ", "COMMERC", "ESERC",
            "ACQUIST", "SUPERMERC", "FARMAC", "BENZIN", "CARBURAN", "DISTRIBUT",
            "CONAD", "COOP", "EUROSPIN", "LIDL", "CRAI", "DECO"
        ]
        if any(w in l_u for w in keywords):
            matches.append(l_clean)
            
    return doc_name, pno, text, matches

def main():
    t0 = time.time()
    docs = [
        "Adobe Scan 07 Set 2026.pdf",
        "estratti conto Rossi_Bianchi_1.pdf",
        "estratti conto Rossi_Bianchi_2.pdf"
    ]
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    tasks = []
    
    print("[1/3] Rendering pages into memory...", flush=True)
    for doc_name in docs:
        pdf_path = base_dir / doc_name
        if not pdf_path.exists():
            continue
        doc = fitz.open(pdf_path)
        print(f"  {doc_name}: {len(doc)} pages", flush=True)
        for pno in range(len(doc)):
            page = doc[pno]
            # 110 DPI is very fast and perfectly readable for block uppercase BancoPosta font
            pix = page.get_pixmap(dpi=110)
            tasks.append((doc_name, pno + 1, pix.samples, pix.width, pix.height))
            
    print(f"[2/3] Executing parallel OCR across {len(tasks)} pages with 6 workers...", flush=True)
    all_results = []
    pos_hits = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(process_page, task) for task in tasks]
        for f in as_completed(futures):
            doc_name, pno, text, matches = f.result()
            completed += 1
            if completed % 10 == 0 or completed == len(tasks):
                print(f"  Progress: {completed}/{len(tasks)} pages scanned ({(time.time()-t0):.1f}s)...", flush=True)
                
            if matches:
                for m in matches:
                    print(f"  --> FOUND in [{doc_name} Pag.{pno}]: {m}", flush=True)
                    pos_hits.append({
                        "doc": doc_name,
                        "page": pno,
                        "line": m
                    })
                    
    print(f"\n[3/3] Scan complete in {time.time()-t0:.1f}s. Total matches found: {len(pos_hits)}", flush=True)
    
    out_file = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/perizia_output/pos_investigation_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(pos_hits, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {out_file}", flush=True)

if __name__ == "__main__":
    main()
