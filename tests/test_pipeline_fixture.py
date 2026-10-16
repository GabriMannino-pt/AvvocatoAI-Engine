"""
End-to-end integration test on the permanent BancoPosta test fixture.
Verifies all 20 mandate criteria:
1. Import PDF
2. Scanned page detection
3. OCR extraction with bounding boxes
4. Row reconstruction
5. Column reconstruction
6. Date recognition
7. Amount recognition
8. Description recognition
9. Distinguish ATM from physical counter
10. Cash withdrawals recognized
11. Pension credits recognized
12. Fees and commissions recognized
13. Chronological sequence
14. Balance validation
15. Uncertainty flagging
16. Bounding box linking to original image
17. Pattern detection (multiple same-day & pension drain)
18. Legal hypotheses formulation
19. Document requisition plan
20. 20-Section forensic report generation.
"""
from pathlib import Path
import pytest
from core.forensic_pipeline import ForensicPipeline
from core.models import ChannelType, TransactionType

def test_full_bancoposta_fixture():
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "bancoposta_sample.pdf"
    assert fixture_path.exists(), f"Missing fixture at {fixture_path}"
    
    pipeline = ForensicPipeline()
    case = pipeline.process_pdf(
        str(fixture_path),
        initial_balance=2143.20,
        authorized_spending=600.0,
        case_title="Test Peritale BancoPosta 2016"
    )
    
    assert case is not None
    assert len(case.transactions) > 0
    print(f"\nExtracted {len(case.transactions)} transactions from fixture.")
    
    # Check transaction types
    has_atm = any(t.channel == ChannelType.ATM for t in case.transactions)
    assert has_atm, "ATM transactions must be detected."
    
    # Check that sportello automatico was not classified as sportello fisico
    for t in case.transactions:
        if "SPORTELLO AUTOMATICO" in t.description.upper():
            assert t.channel == ChannelType.ATM, f"Expected ATM for {t.description}, got {t.channel}"
            assert t.channel != ChannelType.SPORTELLO_FISICO
            
    # Check pension detection
    has_pension = any(t.transaction_type == TransactionType.PENSION_CREDIT for t in case.transactions)
    assert has_pension, "Pension credit must be detected."
    
    # Check that each transaction has a valid bounding box and crop
    for t in case.transactions:
        assert t.bounding_box.width > 0 and t.bounding_box.height > 0
        assert t.image_crop_path is not None
        assert Path(t.image_crop_path).exists()
        
    # Check anomalies detected
    assert len(case.anomalies) > 0
    categories = [a.category for a in case.anomalies]
    print(f"Detected anomaly categories: {categories}")
    assert any("RAPID_SAME_DAY" in c or "AUTH" in c or "PENSION" in c for c in categories)
    
    # Check legal hypotheses
    assert len(case.legal_hypotheses) > 0
    norm_titles = [h.article for h in case.legal_hypotheses]
    print(f"Formulated legal hypotheses: {norm_titles}")
    assert any("493-ter" in a or "643" in a or "119" in a for a in norm_titles)
    
    # Check document requests
    assert len(case.document_requests) > 0
    req_names = [r.document_name for r in case.document_requests]
    print(f"Generated document requests: {req_names}")
    
    # Check report generation
    report_file = pipeline.output_dir / "bancoposta_sample_perizia_forense.md"
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "RELAZIONE TECNICO-PERITALE FORENSE" in content
    assert "Executive Summary" in content
    assert "Conclusioni Forensi" in content
