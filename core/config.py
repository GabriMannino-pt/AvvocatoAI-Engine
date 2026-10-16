"""
Configuration settings for the Forensic Banking OCR & Legal Intelligence system.
"""
import os
from pathlib import Path
from pydantic import BaseModel

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

BASE_DIR = Path(__file__).resolve().parent.parent
TESSDATA_DIR = BASE_DIR / "tessdata"
OUTPUT_DIR = BASE_DIR / "output"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"

# Tesseract executable default paths
POSSIBLE_TESSERACT_PATHS = [
    r"C:\Program Files\PDF24\tesseract\tesseract.exe",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "tesseract"
]

def find_tesseract_path() -> str:
    for p in POSSIBLE_TESSERACT_PATHS:
        if os.path.exists(p):
            return p
    return "tesseract"

class Settings(BaseModel):
    base_dir: Path = BASE_DIR
    app_name: str = "AVVOCATO_AI - Forensic Banking & Legal Intelligence"
    tesseract_cmd: str = find_tesseract_path()
    tessdata_dir: str = str(TESSDATA_DIR)
    default_dpi: int = 300
    high_dpi: int = 400
    ultra_dpi: int = 600
    ocr_confidence_threshold: float = 75.0
    amount_confidence_threshold: float = 85.0
    balance_tolerance_cents: float = 0.01  # tolerance for floating point rounding
    db_path: str = str(BASE_DIR / "forensic_vault.db")

    @property
    def BASE_DIR(self) -> Path:
        return self.base_dir

settings = Settings()

# Ensure critical environment variables
os.environ["TESSDATA_PREFIX"] = settings.tessdata_dir
