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

def locate_targets():
    base_dir = Path("fascicoli/CASE_001_SYNTHETIC_DEMO/documenti_input")
    
    docs = [
        ("estratti conto Rossi_Bianchi_1.pdf", ["12.000", "12000", "07/03/20", "04/06/19", "04/06/2019", "CASSA 4", "CASSA 3", "30980001", "0002"]),
        ("estratti conto Rossi_Bianchi_2.pdf", ["12.000", "12000", "03/02/22", "03/02/2022", "8821", "11,43", "08/03/22", "MERCHANT_POS_DEMO", "40150003"])
    ]
    
    for doc_name, terms in docs:
        pdf_path = base_dir / doc_name
        doc = fitz.open(pdf_path)
        print(f"\n==================== {doc_name} ({len(doc)} pages) ====================")
        for pno in range(len(doc)):
            page = doc[pno]
            pix = page.get_pixmap(dpi=130)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            txt = pytesseract.image_to_string(img, lang="ita")
            
            for line in txt.split("\n"):
                l_u = line.upper()
                for t in terms:
                    if t.upper() in l_u:
                        print(f"[{doc_name} Pag.{pno+1}] Match for '{t}': {line.strip()[:110]}")
                        break

if __name__ == "__main__":
    locate_targets()
