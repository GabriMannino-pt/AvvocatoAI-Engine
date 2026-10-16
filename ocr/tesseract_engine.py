"""
Tesseract OCR Engine wrapper with coordinate extraction, PSM configuration,
and specialized whitelist profiles for financial banking documents.
"""
import os
import pytesseract
from PIL import Image
from typing import List, Dict, Any, Optional
from core.config import settings
from core.models import BoundingBox, RawOCRToken

# Ensure Tesseract executable and tessdata are registered
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
os.environ["TESSDATA_PREFIX"] = settings.tessdata_dir

class TesseractEngine:
    def __init__(self, lang: str = "ita"):
        self.lang = lang

    def extract_full_page_tokens(self, image_path: str, page_num: int = 1, psm: int = 6) -> List[RawOCRToken]:
        """
        Executes layout-aware OCR on a page image.
        Returns a list of RawOCRToken objects, each with exact coordinates and confidence.
        """
        img = Image.open(image_path)
        config = f"--psm {psm} --oem 1"
        data = pytesseract.image_to_data(img, lang=self.lang, config=config, output_type=pytesseract.Output.DICT)
        
        tokens: List[RawOCRToken] = []
        n_boxes = len(data["text"])
        
        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = float(data["conf"][i])
            if text and conf >= 0:  # conf < 0 means structural whitespace or separator
                bbox = BoundingBox(
                    x=int(data["left"][i]),
                    y=int(data["top"][i]),
                    width=int(data["width"][i]),
                    height=int(data["height"][i])
                )
                tokens.append(RawOCRToken(
                    page=page_num,
                    bbox=bbox,
                    text=text,
                    confidence=conf,
                    source_image=image_path,
                    pass_type="PASS_A"
                ))
        return tokens

    def ocr_region(self, crop_path: str, page_num: int = 1, psm: int = 7, numeric_only: bool = False) -> Dict[str, Any]:
        """
        Targeted OCR on an isolated cropped snippet (e.g. single cell, date, amount).
        """
        img = Image.open(crop_path)
        whitelist_param = ""
        if numeric_only:
            whitelist_param = "-c tessedit_char_whitelist=0123456789.,-+€EUR"
        
        config = f"--psm {psm} --oem 1 {whitelist_param}".strip()
        data = pytesseract.image_to_data(img, lang=self.lang, config=config, output_type=pytesseract.Output.DICT)
        
        words = []
        confidences = []
        for i in range(len(data["text"])):
            t = data["text"][i].strip()
            c = float(data["conf"][i])
            if t and c >= 0:
                words.append(t)
                confidences.append(c)
        
        full_text = " ".join(words)
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "text": full_text,
            "mean_confidence": mean_conf,
            "tokens": words,
            "confidences": confidences,
            "crop_path": crop_path
        }
