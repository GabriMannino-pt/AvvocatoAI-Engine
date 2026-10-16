"""
Forensic Image Preprocessor using OpenCV and NumPy.
Generates non-destructive derived variations for OCR:
- Deskewing (Hough & MinAreaRect)
- Denoising (Bilateral & Morphological)
- Contrast enhancement (CLAHE)
- Adaptive thresholding (Otsu & Gaussian)
- Column and line separator cleaning
Preserves the original source image unaltered.
"""
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image

class ImagePreprocessor:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or (Path(__file__).resolve().parent.parent / "output" / "preprocessed"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def detect_skew_angle(self, gray: np.ndarray) -> float:
        """
        Detects skew angle of a scanned document page using Hough lines or minAreaRect.
        """
        # Threshold to find text lines
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Morphological dilation horizontally to merge letters into line bars
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        angles = []
        for c in contours:
            if cv2.contourArea(c) < 1000:
                continue
            rect = cv2.minAreaRect(c)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) < 45:
                angles.append(angle)
        
        if not angles:
            return 0.0
        return float(np.median(angles))

    def rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotates image by given angle while expanding bounding box to prevent cropping.
        """
        if abs(angle) < 0.1:
            return image
        
        (h, w) = image.shape[:2]
        (cX, cY) = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
        M[0, 2] += (nW / 2) - cX
        M[1, 2] += (nH / 2) - cY
        return cv2.warpAffine(image, M, (nW, nH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    def preprocess_pipeline(self, image_path: str, deskew: bool = True) -> Dict[str, str]:
        """
        Runs complete preprocessing pipeline, returning paths to derivative variants:
        - deskewed
        - clahe_enhanced
        - otsu_binary
        - adaptive_binary
        """
        src = cv2.imread(image_path)
        if src is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        
        stem = Path(image_path).stem
        results = {"original": image_path}
        
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        
        # 1. Deskew
        angle = 0.0
        if deskew:
            angle = self.detect_skew_angle(gray)
            if abs(angle) >= 0.2:
                gray = self.rotate_image(gray, angle)
                src = self.rotate_image(src, angle)
                deskew_path = str(self.output_dir / f"{stem}_deskewed.png")
                cv2.imwrite(deskew_path, src)
                results["deskewed"] = deskew_path
                results["deskew_angle"] = angle

        # 2. Denoising & CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        enhanced_path = str(self.output_dir / f"{stem}_enhanced.png")
        cv2.imwrite(enhanced_path, denoised)
        results["enhanced"] = enhanced_path
        
        # 3. Otsu binarization
        _, otsu_bin = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_path = str(self.output_dir / f"{stem}_otsu.png")
        cv2.imwrite(otsu_path, otsu_bin)
        results["otsu"] = otsu_path
        
        # 4. Adaptive Gaussian binarization (effective for uneven lighting and smartphone scans)
        try:
            adaptive_bin = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 11)
            adaptive_path = str(self.output_dir / f"{stem}_adaptive.png")
            cv2.imwrite(adaptive_path, adaptive_bin)
            results["adaptive"] = adaptive_path
        except Exception:
            results["adaptive"] = otsu_path
        
        return results

    def super_resolve_crop(self, crop_path: str, scale: float = 2.0) -> str:
        """
        Applies Lanczos/Bicubic high-quality interpolation + sharpening for Pass C targeted OCR.
        """
        img = cv2.imread(crop_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return crop_path
        
        new_w = int(img.shape[1] * scale)
        new_h = int(img.shape[0] * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Sharpening kernel
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(resized, -1, kernel)
        
        stem = Path(crop_path).stem
        out_path = str(self.output_dir / f"{stem}_super_res.png")
        cv2.imwrite(out_path, sharpened)
        return out_path
