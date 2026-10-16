"""
Multi-Pass OCR Pipeline Coordinator.
Implements Pass A (full page), Pass B (region), and Pass C (targeted zoom + whitelist).
"""
import os
from typing import List, Dict, Any, Optional
from core.models import BoundingBox, RawOCRToken, Cell, Row
from ocr.tesseract_engine import TesseractEngine
from ocr.reconciler import OCRReconciler
from ingestion.pdf_renderer import PDFRenderer
from ingestion.preprocessor import ImagePreprocessor

class MultiPassOCR:
    def __init__(self, lang: str = "ita"):
        self.engine = TesseractEngine(lang=lang)
        self.reconciler = OCRReconciler()
        self.preprocessor = ImagePreprocessor()
        self.renderer = PDFRenderer()

    def run_pass_a(self, image_path: str, page_num: int = 1) -> List[RawOCRToken]:
        """
        Pass A: Full-page layout and token extraction.
        """
        return self.engine.extract_full_page_tokens(image_path, page_num=page_num, psm=6)

    def run_pass_b_region(self, image_path: str, bbox: BoundingBox, page_num: int = 1) -> Dict[str, Any]:
        """
        Pass B: Region-targeted OCR on cropped region.
        """
        crop_path = self.renderer.crop_region(image_path, bbox.model_dump())
        result = self.engine.ocr_region(crop_path, page_num=page_num, psm=6)
        result["pass_name"] = "PASS_B_REGION"
        return result

    def run_pass_c_targeted(self, image_path: str, bbox: BoundingBox, page_num: int = 1, is_numeric: bool = True) -> Dict[str, Any]:
        """
        Pass C: Targeted high-resolution super-sampling + whitelist on difficult / low-confidence cells.
        """
        crop_path = self.renderer.crop_region(image_path, bbox.model_dump())
        super_res_crop = self.preprocessor.super_resolve_crop(crop_path, scale=2.5)
        
        # Run specialized whitelist Tesseract pass
        result = self.engine.ocr_region(super_res_crop, page_num=page_num, psm=7, numeric_only=is_numeric)
        result["pass_name"] = "PASS_C_TARGETED"
        return result

    def verify_cell(self, image_path: str, cell: Cell, page_num: int = 1, is_numeric: bool = False) -> Cell:
        """
        Verifies a single cell with multi-pass OCR if confidence is below threshold or if numeric.
        """
        candidates = [{
            "text": cell.raw_text,
            "confidence": cell.confidence,
            "pass_name": "PASS_A"
        }]
        
        # If low confidence or numeric, run Pass C targeted
        if cell.confidence < 85.0 or is_numeric:
            pass_c_res = self.run_pass_c_targeted(image_path, cell.bbox, page_num=page_num, is_numeric=is_numeric)
            candidates.append({
                "text": pass_c_res["text"],
                "confidence": pass_c_res["mean_confidence"],
                "pass_name": "PASS_C"
            })
        
        recon = self.reconciler.reconcile_candidates(candidates)
        
        updated_cell = cell.model_copy()
        if recon["consensus_text"]:
            updated_cell.raw_text = recon["consensus_text"]
        if recon["normalized_amount"] is not None:
            updated_cell.normalized_value = recon["normalized_amount"]
        updated_cell.confidence = recon["confidence"]
        return updated_cell
