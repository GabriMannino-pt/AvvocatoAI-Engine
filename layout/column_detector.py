"""
Borderless Column Detector and Semantic Slot Assigner.
Infers column boundaries from horizontal X-coordinates, alignment patterns,
and financial text regexes (dates, descriptions, debit, credit, balance).
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from core.models import RawOCRToken, Cell, BoundingBox

DATE_REGEX = re.compile(r'^\b\d{1,2}[\/\.\-]\d{1,2}(?:[\/\.\-]\d{2,4})?\b')
AMOUNT_REGEX = re.compile(r'^-?€?\s*(\d{1,3}(?:[.\s]\d{3})*|\d+)[,.]\d{2}\s*€?$')

class ColumnDetector:
    def __init__(self):
        self.column_headers = {
            "date_accounting": ["DATA CONT.", "DATA REG.", "DATA OPERAZIONE", "DATA", "DATA CONTABILE"],
            "date_value": ["DATA VALUTA", "VALUTA", "VAL."],
            "description": ["DESCRIZIONE", "CAUSALE", "DESCRIZIONE OPERAZIONE", "DETTAGLIO"],
            "debit": ["DARE", "ADDEBITI", "USCITE", "SEGNO -", "ADDEBITO"],
            "credit": ["AVERE", "ACCREDITI", "ENTRATE", "SEGNO +", "ACCREDITO"],
            "balance": ["SALDO", "SALDO CONTABILE", "SALDO DISPONIBILE"]
        }

    def infer_token_type(self, text: str) -> str:
        """
        Classifies a token semantically based on string content.
        """
        cleaned = text.strip()
        if DATE_REGEX.match(cleaned):
            return "DATE"
        if AMOUNT_REGEX.match(cleaned):
            return "AMOUNT"
        return "TEXT"

    def assign_row_cells(self, tokens_in_row: List[RawOCRToken], col_boundaries: Optional[Dict[str, Tuple[int, int]]] = None) -> List[Cell]:
        """
        Assigns tokens within a single row into distinct semantic cells:
        [Date Accounting, Date Value, Description, Debit, Credit, Balance]
        """
        if not tokens_in_row:
            return []

        # Sort tokens left to right
        sorted_tokens = sorted(tokens_in_row, key=lambda t: t.bbox.x)
        
        # If explicit column boundaries exist, bucket tokens into them
        if col_boundaries:
            cell_buckets: Dict[str, List[RawOCRToken]] = {col: [] for col in col_boundaries}
            for t in sorted_tokens:
                center_x = t.bbox.x + (t.bbox.width / 2)
                assigned = False
                for col_name, (x_min, x_max) in col_boundaries.items():
                    if x_min <= center_x <= x_max:
                        cell_buckets[col_name].append(t)
                        assigned = True
                        break
                if not assigned:
                    # Fallback to description
                    if "description" in cell_buckets:
                        cell_buckets["description"].append(t)

            cells = []
            for col_name, bucket in cell_buckets.items():
                if bucket:
                    combined_text = " ".join(t.text for t in bucket)
                    min_x = min(t.bbox.x for t in bucket)
                    min_y = min(t.bbox.y for t in bucket)
                    max_x = max(t.bbox.x2 for t in bucket)
                    max_y = max(t.bbox.y2 for t in bucket)
                    avg_conf = sum(t.confidence for t in bucket) / len(bucket)
                    cells.append(Cell(
                        column_name=col_name,
                        raw_text=combined_text,
                        bbox=BoundingBox(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y),
                        confidence=avg_conf
                    ))
            return cells

        # Heuristic pattern matching for Italian bank statements:
        # Expected sequence: [Date] [Optional Date] [Description tokens...] [Optional Debit] [Optional Credit] [Optional Balance]
        cells = []
        desc_tokens = []
        found_dates = []
        amounts = []

        for t in sorted_tokens:
            t_type = self.infer_token_type(t.text)
            if t_type == "DATE" and len(found_dates) < 2 and not desc_tokens:
                found_dates.append(t)
            elif t_type == "AMOUNT":
                amounts.append(t)
            else:
                desc_tokens.append(t)

        if len(found_dates) >= 1:
            cells.append(Cell(
                column_name="date_accounting",
                raw_text=found_dates[0].text,
                bbox=found_dates[0].bbox,
                confidence=found_dates[0].confidence
            ))
        if len(found_dates) >= 2:
            cells.append(Cell(
                column_name="date_value",
                raw_text=found_dates[1].text,
                bbox=found_dates[1].bbox,
                confidence=found_dates[1].confidence
            ))

        if desc_tokens:
            min_x = min(t.bbox.x for t in desc_tokens)
            min_y = min(t.bbox.y for t in desc_tokens)
            max_x = max(t.bbox.x2 for t in desc_tokens)
            max_y = max(t.bbox.y2 for t in desc_tokens)
            avg_conf = sum(t.confidence for t in desc_tokens) / len(desc_tokens)
            cells.append(Cell(
                column_name="description",
                raw_text=" ".join(t.text for t in desc_tokens),
                bbox=BoundingBox(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y),
                confidence=avg_conf
            ))

        # Handle amounts: typically [Debit/Credit] and optionally [Balance]
        desc_text = " ".join(t.text.upper() for t in desc_tokens)
        is_semantic_debit = any(w in desc_text for w in ["PRELIEVO", "COMMISSION", "SPESE", "PAGAMENTO", "ADDEBIT", "USCITA"])
        is_semantic_credit = any(w in desc_text for w in ["ACCREDIT", "PENSIONE", "STIPENDIO", "VERSAMENTO", "ENTRATA"])

        if len(amounts) == 1:
            amt_token = amounts[0]
            if "SALDO" in desc_text:
                col = "balance"
            elif is_semantic_debit or "-" in amt_token.text:
                col = "debit"
            elif is_semantic_credit:
                col = "credit"
            else:
                col = "movement_amount"
            cells.append(Cell(
                column_name=col,
                raw_text=amt_token.text,
                bbox=amt_token.bbox,
                confidence=amt_token.confidence
            ))
        elif len(amounts) >= 2:
            # First is movement amount, last is balance
            amt_token = amounts[0]
            if is_semantic_debit or "-" in amt_token.text:
                col = "debit"
            elif is_semantic_credit:
                col = "credit"
            else:
                col = "movement_amount"

            cells.append(Cell(
                column_name=col,
                raw_text=amt_token.text,
                bbox=amt_token.bbox,
                confidence=amt_token.confidence
            ))
            cells.append(Cell(
                column_name="balance",
                raw_text=amounts[-1].text,
                bbox=amounts[-1].bbox,
                confidence=amounts[-1].confidence
            ))

        return cells
