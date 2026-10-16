"""
Structural Builder.
Combines row clustering and column assignment to reconstruct the full digital table,
maintaining the physical coordinates and links to the source image.
"""
from typing import List, Dict, Any, Optional
from core.models import RawOCRToken, Row, Cell, BoundingBox
from layout.row_detector import RowDetector
from layout.column_detector import ColumnDetector

class StructuralBuilder:
    def __init__(self, y_tolerance: int = 14):
        self.row_detector = RowDetector(y_tolerance=y_tolerance)
        self.column_detector = ColumnDetector()

    def build_table_structure(self, tokens: List[RawOCRToken], page_num: int = 1, col_boundaries: Optional[Dict[str, Any]] = None) -> List[Row]:
        """
        Reconstructs the 2D grid of rows and cells from raw tokens.
        """
        if not tokens:
            return []

        # 1. Cluster tokens into rows
        rows = self.row_detector.cluster_tokens_into_rows(tokens, page_num=page_num)

        # 2. For each row, group tokens that belong to that row's Y-span and assign cells
        # We find which tokens are closest to this row
        sorted_tokens = sorted(tokens, key=lambda t: t.bbox.y)
        
        for r in rows:
            row_tokens = [
                t for t in sorted_tokens 
                if abs((t.bbox.y + t.bbox.height / 2) - (r.y_position + 10)) <= 15
            ]
            if not row_tokens:
                # fallback: search in reasonable window
                row_tokens = [t for t in sorted_tokens if abs(t.bbox.y - r.y_position) <= 15]

            r.cells = self.column_detector.assign_row_cells(row_tokens, col_boundaries=col_boundaries)

        return rows
