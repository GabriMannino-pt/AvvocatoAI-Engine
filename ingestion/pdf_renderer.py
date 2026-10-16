"""
High-Resolution PDF Rendering & Ingestion Engine using PyMuPDF.
Renders pages at 300, 400, 600 DPI and checks if pages are scanned or digital.
Preserves original pristine images immutably as the primary source of truth.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pymupdf as fitz
from PIL import Image
from core.config import settings

class PDFRenderer:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or (settings.BASE_DIR / "output" / "pages"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_scanned_page(self, page: fitz.Page) -> bool:
        """
        Determines whether a page is primarily a scanned image.
        If extracted text has very few words compared to image area, it's considered scanned.
        """
        text = page.get_text("text").strip()
        images = page.get_images()
        # If there is very little text but one or more full-page images, it's scanned
        if len(text) < 150 and len(images) > 0:
            return True
        # If no text at all, definitely scanned
        if len(text) == 0:
            return True
        return False

    def render_page(self, doc_path: str, page_num: int, dpi: int = 300) -> Tuple[str, fitz.Rect]:
        """
        Renders a specific page at the specified DPI (300, 400, 600) and saves it immutably.
        Returns:
            image_path: Absolute path to rendered PNG.
            page_rect: Original page rect in PDF points (for coordinate mapping).
        """
        doc = fitz.open(doc_path)
        if page_num < 1 or page_num > len(doc):
            raise IndexError(f"Page {page_num} out of bounds (1..{len(doc)})")
        
        page = doc[page_num - 1]
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        
        doc_stem = Path(doc_path).stem
        out_filename = f"{doc_stem}_p{page_num}_{dpi}dpi.png"
        out_path = self.output_dir / out_filename
        pix.save(str(out_path))
        
        return str(out_path), page.rect

    def render_all_pages(self, doc_path: str, dpi: int = 300) -> List[Dict[str, Any]]:
        """
        Renders all pages of a PDF and returns metadata.
        """
        doc = fitz.open(doc_path)
        pages_info = []
        for i, page in enumerate(doc):
            page_num = i + 1
            is_scanned = self.is_scanned_page(page)
            img_path, rect = self.render_page(doc_path, page_num, dpi=dpi)
            pages_info.append({
                "page": page_num,
                "is_scanned": is_scanned,
                "image_path": img_path,
                "dpi": dpi,
                "width_pts": rect.width,
                "height_pts": rect.height,
                "pdf_path": doc_path
            })
        return pages_info

    def crop_region(self, image_path: str, bbox: Dict[str, int], save_name: Optional[str] = None) -> str:
        """
        Extracts a region crop from the rendered page image.
        bbox: dict with x, y, width, height (pixel coordinates)
        """
        img = Image.open(image_path)
        x1 = max(0, bbox["x"])
        y1 = max(0, bbox["y"])
        x2 = min(img.width, x1 + bbox["width"])
        y2 = min(img.height, y1 + bbox["height"])
        
        crop = img.crop((x1, y1, x2, y2))
        
        crops_dir = self.output_dir / "crops"
        crops_dir.mkdir(parents=True, exist_ok=True)
        
        if not save_name:
            save_name = f"crop_{x1}_{y1}_{x2}_{y2}.png"
        crop_path = crops_dir / save_name
        crop.save(str(crop_path))
        return str(crop_path)
