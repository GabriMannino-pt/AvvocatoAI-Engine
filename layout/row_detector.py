"""
Geometric Row Detector.
Clusters OCR tokens into physical table rows based on Y-coordinates,
line heights, and spatial continuity, ensuring rows are strictly ordered geometrically.
"""
from typing import List, Dict, Any
from core.models import RawOCRToken, Row, BoundingBox

class RowDetector:
    def __init__(self, y_tolerance: int = 14):
        self.y_tolerance = y_tolerance

    def cluster_tokens_into_rows(self, tokens: List[RawOCRToken], page_num: int = 1) -> List[Row]:
        """
        Groups raw OCR tokens into horizontal rows based on vertical proximity.
        Tokens in the same row are sorted by X coordinate (left-to-right).
        """
        if not tokens:
            return []
        
        # Sort all tokens by vertical Y position first
        sorted_by_y = sorted(tokens, key=lambda t: t.bbox.y)
        
        row_clusters: List[List[RawOCRToken]] = []
        current_cluster: List[RawOCRToken] = [sorted_by_y[0]]
        current_y_center = sorted_by_y[0].bbox.y + (sorted_by_y[0].bbox.height / 2)
        
        for t in sorted_by_y[1:]:
            t_y_center = t.bbox.y + (t.bbox.height / 2)
            # If within vertical tolerance or substantial vertical overlap
            if abs(t_y_center - current_y_center) <= self.y_tolerance:
                current_cluster.append(t)
                # Update moving average of row center
                current_y_center = sum(item.bbox.y + (item.bbox.height / 2) for item in current_cluster) / len(current_cluster)
            else:
                row_clusters.append(current_cluster)
                current_cluster = [t]
                current_y_center = t_y_center
        
        if current_cluster:
            row_clusters.append(current_cluster)
            
        # Build Row objects, ordering each row's tokens left to right
        rows: List[Row] = []
        for idx, cluster in enumerate(row_clusters):
            cluster_sorted_x = sorted(cluster, key=lambda t: t.bbox.x)
            
            y_pos = int(min(t.bbox.y for t in cluster_sorted_x))
            raw_line_text = " ".join(t.text for t in cluster_sorted_x)
            
            row_id = f"p{page_num}_r{idx+1:03d}"
            rows.append(Row(
                page=page_num,
                row_id=row_id,
                y_position=y_pos,
                raw_line_text=raw_line_text
            ))
            
        return rows
