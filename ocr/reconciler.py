"""
OCR Comparison and Discrepancy Reconciler.
Enforces the Zero Silent Correction rule:
- Recognizes syntactic equivalence (e.g. 600,00 vs 600.00)
- Flags semantic divergence (e.g. 600,00 vs 800,00) with NEEDS_REVIEW
- Never picks arbitrarily between conflicting interpretations.
"""
import re
from typing import List, Dict, Any, Optional, Tuple

class OCRReconciler:
    @staticmethod
    def clean_financial_string(raw: str) -> str:
        """
        Strips whitespace and currency symbols for numeric comparison.
        """
        s = raw.strip().replace("€", "").replace("EUR", "").replace(" ", "")
        return s

    @staticmethod
    def parse_numeric_amount(raw: str) -> Optional[float]:
        """
        Parses Italian (1.234,56) and Standard (1,234.56 or 1234.56) financial notation.
        Returns None if parsing fails.
        """
        s = OCRReconciler.clean_financial_string(raw)
        if not s:
            return None
        
        # Check for Italian format: 1.234,56 or 600,00
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                # Italian: dot thousands, comma decimals
                s = s.replace(".", "").replace(",", ".")
            else:
                # English: comma thousands, dot decimals
                s = s.replace(",", "")
        elif "," in s:
            # e.g. 600,00
            s = s.replace(",", ".")
        # Now s should have only dots
        try:
            return float(s)
        except ValueError:
            return None

    def reconcile_candidates(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compares multiple OCR reads for the same field/cell.
        candidates: List of dicts with keys: 'text', 'confidence', 'pass_name'
        """
        if not candidates:
            return {
                "consensus_text": "",
                "normalized_amount": None,
                "confidence": 0.0,
                "status": "UNREADABLE_REGION",
                "interpretations": [],
                "warnings": ["UNREADABLE_REGION"]
            }
        
        # Filter out empty texts
        valid = [c for c in candidates if c.get("text", "").strip()]
        if not valid:
            return {
                "consensus_text": "",
                "normalized_amount": None,
                "confidence": 0.0,
                "status": "UNREADABLE_REGION",
                "interpretations": [],
                "warnings": ["UNREADABLE_REGION"]
            }
        
        raw_texts = [c["text"].strip() for c in valid]
        confidences = [c.get("confidence", 50.0) for c in valid]
        
        # Check numeric equivalence
        parsed_numbers = [self.parse_numeric_amount(t) for t in raw_texts]
        all_numeric = all(n is not None for n in parsed_numbers)
        
        if all_numeric:
            unique_values = set(parsed_numbers)
            if len(unique_values) == 1:
                # E.g. "600,00" and "600.00" -> Exactly the same numeric value!
                val = list(unique_values)[0]
                avg_conf = min(100.0, (sum(confidences) / len(confidences)) + 5.0)  # agreement bonus
                return {
                    "consensus_text": raw_texts[0],
                    "normalized_amount": val,
                    "confidence": avg_conf,
                    "status": "VERIFIED",
                    "interpretations": raw_texts,
                    "warnings": []
                }
            else:
                # Divergence! E.g. "600,00" vs "800,00"
                # DO NOT pick arbitrarily!
                return {
                    "consensus_text": raw_texts[0],
                    "normalized_amount": parsed_numbers[0],  # provisional primary
                    "confidence": max(10.0, min(confidences) - 20.0),  # penalize confidence
                    "status": "NEEDS_REVIEW",
                    "interpretations": raw_texts,
                    "divergent_amounts": list(unique_values),
                    "warnings": ["POSSIBLE_WRONG_DIGIT", "AMBIGUOUS_TEXT"]
                }
        else:
            # Textual field comparison
            normalized_texts = [re.sub(r'\s+', ' ', t).upper() for t in raw_texts]
            if len(set(normalized_texts)) == 1:
                return {
                    "consensus_text": raw_texts[0],
                    "normalized_amount": None,
                    "confidence": sum(confidences) / len(confidences),
                    "status": "VERIFIED",
                    "interpretations": raw_texts,
                    "warnings": []
                }
            else:
                return {
                    "consensus_text": raw_texts[0],
                    "normalized_amount": None,
                    "confidence": max(20.0, min(confidences) - 15.0),
                    "status": "NEEDS_REVIEW",
                    "interpretations": raw_texts,
                    "warnings": ["AMBIGUOUS_TEXT"]
                }
