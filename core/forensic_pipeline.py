"""
Master Forensic Pipeline Coordinator.
Executes the full end-to-end multi-stage pipeline:
PDF -> High-Res Rendering -> Preprocessing -> Multi-Pass OCR -> Layout -> Financial -> Patterns -> Legal -> Evidence Graph -> Report.
"""
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.config import settings
from core.models import Transaction, StatementSummary, Anomaly, LegalHypothesis, DocumentRequest, ForensicCase, ReviewStatus, BoundingBox
from core.database import ForensicDatabase
from ingestion.pdf_renderer import PDFRenderer
from ingestion.preprocessor import ImagePreprocessor
from ocr.multi_pass import MultiPassOCR
from layout.structural_builder import StructuralBuilder
from financial.channel_classifier import ChannelClassifier
from financial.normalizer import FinancialNormalizer
from financial.validator import FinancialValidator
from financial.bancoposta_extractor import BancoPostaExtractor
from financial.reconciliation import MultiYearReconciliationEngine
from analytics.behavioral import BehavioralProfiler
from analytics.pattern_detector import PatternDetector
from analytics.auth_comparator import AuthorizationComparator
from analytics.card_intelligence import CardIntelligenceEngine
from analytics.cash_forensics import CashWithdrawalForensics
from analytics.counterparty_engine import CounterpartyAndIncomeEngine
from analytics.anomaly_scorer import AnomalyScoringEngine
from legal.hypothesis_engine import LegalHypothesisEngine
from legal.document_requests import DocumentRequestEngine
from report.forensic_report import ForensicReportGenerator
from report.master_forensic_report import MasterForensicReportGenerator
from report.evidence_graph import EvidenceGraphBuilder

class ForensicPipeline:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or settings.base_dir / "output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.renderer = PDFRenderer(output_dir=str(self.output_dir / "pages"))
        self.preprocessor = ImagePreprocessor(output_dir=str(self.output_dir / "preprocessed"))
        self.ocr = MultiPassOCR(lang="ita")
        self.layout_builder = StructuralBuilder()
        self.channel_classifier = ChannelClassifier()
        self.normalizer = FinancialNormalizer()
        self.validator = FinancialValidator()
        self.multi_year_recon = MultiYearReconciliationEngine()
        self.card_intelligence = CardIntelligenceEngine()
        self.cash_forensics = CashWithdrawalForensics()
        self.counterparty_engine = CounterpartyAndIncomeEngine()
        self.anomaly_scorer = AnomalyScoringEngine()
        self.profiler = BehavioralProfiler()
        self.pattern_detector = PatternDetector()
        self.auth_comparator = AuthorizationComparator()
        self.legal_engine = LegalHypothesisEngine()
        self.doc_request_engine = DocumentRequestEngine()
        self.report_generator = ForensicReportGenerator()
        self.master_report_gen = MasterForensicReportGenerator()
        self.graph_builder = EvidenceGraphBuilder()
        self.db = ForensicDatabase()

    def process_pdf(
        self,
        pdf_path: str,
        initial_balance: Optional[float] = None,
        authorized_spending: Optional[float] = None,
        case_title: Optional[str] = None
    ) -> ForensicCase:
        """
        Executes complete forensic analysis on a PDF file.
        """
        pdf_path_obj = Path(pdf_path)
        doc_name = pdf_path_obj.name
        case_id = f"CASE_{uuid.uuid4().hex[:8].upper()}"
        case_title = case_title or f"Analisi Forense Estratto Conto - {doc_name}"
        
        # 1. Ingestion & High-Res Rendering (300 DPI default)
        pages_info = self.renderer.render_all_pages(str(pdf_path_obj), dpi=settings.default_dpi)
        
        all_transactions: List[Transaction] = []
        tx_counter = 1

        bancoposta_ext = BancoPostaExtractor()
        if bancoposta_ext.is_bancoposta(str(pdf_path_obj)):
            first_img = pages_info[0]["image_path"]
            prep_dict = self.preprocessor.preprocess_pipeline(first_img, deskew=True)
            enhanced = prep_dict.get("enhanced", first_img)
            bp_data = bancoposta_ext.extract_forensic_data(str(pdf_path_obj), enhanced)
            all_transactions = bp_data["transactions"]
            for tx in all_transactions:
                crop_path = self.renderer.crop_region(first_img, tx.bounding_box.model_dump(), save_name=f"{doc_name}_p{tx.page}_{tx.id}.png")
                tx.image_crop_path = crop_path
            if initial_balance is None:
                initial_balance = bp_data["saldo_iniziale"]
            case_title = f"Analisi Forense BancoPosta - {bp_data['intestatari']} (IBAN: {bp_data['iban']})"
        else:
            for page_info in pages_info:
                p_num = page_info["page"]
                img_path = page_info["image_path"]
                
                # 2. Preprocessing: Deskew, Contrast CLAHE, Denoising
                prep_dict = self.preprocessor.preprocess_pipeline(img_path, deskew=True)
                ocr_target_img = prep_dict.get("enhanced", img_path)
                
                # 3. Layout-Aware OCR (Pass A)
                tokens = self.ocr.run_pass_a(ocr_target_img, page_num=p_num)
                
                # 4. Geometric Row & Column Detection
                rows = self.layout_builder.build_table_structure(tokens, page_num=p_num)
            
            # 5. Extract and normalize transactions from rows
            for row in rows:
                if not row.cells:
                    continue
                
                # Check if this row represents a financial transaction
                date_acc = None
                date_val = None
                desc = ""
                debit_val = None
                credit_val = None
                balance_val = None
                confidences = {}
                
                for cell in row.cells:
                    col = cell.column_name
                    raw = cell.raw_text
                    conf = cell.confidence
                    
                    if col == "date_accounting":
                        date_acc = self.normalizer.normalize_date(raw)
                        confidences["date_accounting"] = conf
                    elif col == "date_value":
                        date_val = self.normalizer.normalize_date(raw)
                        confidences["date_value"] = conf
                    elif col == "description":
                        desc = raw
                        confidences["description"] = conf
                    elif col in ["debit", "movement_amount"]:
                        val = self.normalizer.normalize_amount(raw)
                        if val is not None:
                            is_debit = ("-" in raw or col == "debit" or any(w in desc.upper() for w in ["PRELIEVO", "COMMISSION", "SPESE", "PAGAMENTO", "ADDEBIT", "USCITA", "DISPOSIZIONE"]))
                            if is_debit:
                                debit_val = abs(val)
                            else:
                                credit_val = abs(val)
                        confidences["amount"] = conf
                    elif col == "credit":
                        val = self.normalizer.normalize_amount(raw)
                        if val is not None:
                            credit_val = abs(val)
                        confidences["credit"] = conf
                    elif col == "balance":
                        balance_val = self.normalizer.normalize_amount(raw)
                        confidences["balance"] = conf

                # Filter out pure headers
                if not date_acc and not debit_val and not credit_val and not balance_val:
                    continue
                
                # Channel Disambiguation
                channel, channel_detail = self.channel_classifier.classify(desc)
                meta = self.channel_classifier.extract_metadata(desc)
                
                # Transaction Type Classification
                tx_type = self.normalizer.classify_transaction_type(desc, debit_val, credit_val)
                
                # Compute combined row bounding box
                min_x = min(c.bbox.x for c in row.cells)
                min_y = min(c.bbox.y for c in row.cells)
                max_x = max(c.bbox.x2 for c in row.cells)
                max_y = max(c.bbox.y2 for c in row.cells)
                row_bbox = BoundingBox(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)
                
                # Crop row image for millimetric source-of-truth verification
                crop_path = self.renderer.crop_region(img_path, row_bbox.model_dump(), save_name=f"{doc_name}_p{p_num}_r{tx_counter}.png")
                
                avg_conf = sum(confidences.values()) / len(confidences) if confidences else 50.0
                
                tx = Transaction(
                    id=f"TX_{tx_counter:04d}",
                    document_name=doc_name,
                    page=p_num,
                    row_id=row.row_id,
                    date_accounting=date_acc,
                    date_value=date_val,
                    description=desc,
                    amount_debit=debit_val,
                    amount_credit=credit_val,
                    balance=balance_val,
                    atm_id=meta.get("atm_id"),
                    card_number=meta.get("card_number"),
                    operation_code=meta.get("operation_code"),
                    channel=channel,
                    channel_detail=channel_detail,
                    transaction_type=tx_type,
                    bounding_box=row_bbox,
                    image_crop_path=crop_path,
                    raw_ocr_text=row.raw_line_text,
                    confidence_score=avg_conf,
                    field_confidences=confidences,
                    status=ReviewStatus.VERIFIED if avg_conf >= 75.0 else ReviewStatus.NEEDS_REVIEW
                )
                all_transactions.append(tx)
                tx_counter += 1

        # 6. Financial Mathematical Validation
        summary, discrepancies = self.validator.validate_statement_sequence(all_transactions, initial_balance=initial_balance)
        
        # 7. Multi-Year & Quarterly Reconciliation (2016-2026)
        recon_data = self.multi_year_recon.reconcile_multi_year(all_transactions, initial_balance=initial_balance)

        # 8. Card Intelligence (Lifecycle & Concurrency Analysis)
        card_profiles, card_concurrency = self.card_intelligence.analyze_cards(all_transactions)

        # 9. Cash Withdrawal Forensics (>€1k/€2k/€5k, serial withdrawals, ATM vs sportello)
        cash_data = self.cash_forensics.analyze_cash_withdrawals(all_transactions)

        # 10. Counterparty & Income Intelligence (source of income, top counterparties)
        counterparty_data = self.counterparty_engine.analyze_counterparties_and_income(all_transactions)

        # 11. Pattern & Behavioral Anomaly Detection + Granular 0-100 Scoring
        pattern_anomalies = self.pattern_detector.detect_anomalies(all_transactions)
        scored_txs, scored_anomalies, anomaly_rankings = self.anomaly_scorer.score_transactions(all_transactions)

        # Combine all anomalies without duplication
        seen_titles = set()
        all_anomalies: List[Anomaly] = []
        for anom in pattern_anomalies + scored_anomalies:
            if anom.title not in seen_titles:
                seen_titles.add(anom.title)
                all_anomalies.append(anom)
        
        # Add mathematical discrepancies as critical anomalies
        for disc in discrepancies:
            disc_title = f"Discrepanza di quadratura contabile riga {disc['row_id']} (€{disc['discrepancy']:.2f})"
            if disc_title not in seen_titles:
                seen_titles.add(disc_title)
                all_anomalies.append(Anomaly(
                    id=f"ANOM_MATH_{disc['row_id']}",
                    category="RECONCILIATION_ANOMALY",
                    severity=AnomalySeverity.CRITICAL,
                    score=95,
                    title=disc_title,
                    description=(
                        f"Incongruenza tra saldo calcolato (€{disc['expected_balance']:.2f}) e saldo letto da OCR "
                        f"(€{disc['ocr_reported_balance']:.2f}). {disc['possible_digit_confusion']}."
                    ),
                    involved_transaction_ids=[disc["transaction_id"]],
                    discrepancy_amount=disc["discrepancy"],
                    explanation="La discordanza matematica non viene corretta silenziosamente. Il sistema evidenzia il campo per la revisione umana sull'immagine originale.",
                    suggested_actions=["Verificare l'immagine originale della riga per accertare se l'importo corretto sia €" + f"{disc['expected_balance']:.2f}"]
                ))

        # 12. Authorization vs Execution Check
        if authorized_spending is not None:
            auth_anomalies = self.auth_comparator.compare_authorization(all_transactions, authorized_amount_per_event=authorized_spending)
            for a in auth_anomalies:
                if a.title not in seen_titles:
                    seen_titles.add(a.title)
                    all_anomalies.append(a)

        # 13. Legal Intelligence (Temporal Versioning & Epistemic Hierarchy)
        hypotheses = self.legal_engine.evaluate_case(all_transactions, all_anomalies)
        
        # 14. Document Request Engine
        requests = self.doc_request_engine.generate_requests(all_transactions, all_anomalies)
        
        # 15. Reports Generation:
        # A. Standard 20-section report (backwards-compatible)
        report_md = self.report_generator.generate_markdown_report(
            case_title=case_title,
            doc_name=doc_name,
            transactions=all_transactions,
            summary=summary,
            anomalies=all_anomalies,
            hypotheses=hypotheses,
            requests=requests
        )
        report_path = self.output_dir / f"{Path(doc_name).stem}_perizia_forense.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        # B. Master 32-section forensic report
        account_iban = "IT60X0760101000000012345678"
        account_holders = "ROSSI MARIO / BIANCHI ANNA"
        master_report_md = self.master_report_gen.generate_32_section_report(
            case_title=case_title,
            account_iban=account_iban,
            account_holders=account_holders,
            doc_names=[doc_name],
            transactions=all_transactions,
            reconciliation_data=recon_data,
            card_profiles=card_profiles,
            card_concurrency=card_concurrency,
            cash_data=cash_data,
            counterparty_data=counterparty_data,
            scored_txs=scored_txs,
            anomalies=all_anomalies,
            anomaly_rankings=anomaly_rankings,
            hypotheses=hypotheses,
            requests=requests
        )
        master_report_path = self.output_dir / f"{Path(doc_name).stem}_master_perizia_32_sezioni.md"
        with open(master_report_path, "w", encoding="utf-8") as f:
            f.write(master_report_md)

        # C. Executive One-Pager Summary
        one_page_md = self.master_report_gen.generate_one_page_summary(
            case_title=case_title,
            doc_names=[doc_name],
            reconciliation_data=recon_data,
            card_data={"profiles": card_profiles},
            cash_data=cash_data,
            counterparty_data=counterparty_data,
            anomaly_data=anomaly_rankings,
            hypotheses=hypotheses,
            requests=requests
        )
        one_page_path = self.output_dir / f"{Path(doc_name).stem}_one_page_summary.md"
        with open(one_page_path, "w", encoding="utf-8") as f:
            f.write(one_page_md)

        # D. Court-Grade PDF Report (REPORT.pdf)
        pdf_out_path = self.output_dir / "REPORT.pdf"
        try:
            self.report_generator.generate_pdf_report(
                target_pdf_path=str(pdf_out_path),
                case_title=case_title,
                doc_name=doc_name,
                transactions=all_transactions,
                summary=summary,
                anomalies=all_anomalies,
                hypotheses=hypotheses,
                requests=requests
            )
        except Exception as e:
            print(f"[WARNING] PDF generation skipped: {e}")

        # 16. Persist to SQLite Database
        self.db.save_transactions(case_id, all_transactions)

        case = ForensicCase(
            case_id=case_id,
            title=case_title,
            documents=[doc_name],
            transactions=all_transactions,
            summary=summary,
            quarterly_reports=recon_data.get("quarterly_records", []),
            annual_reports=recon_data.get("yearly_records", []),
            card_profiles=card_profiles,
            card_concurrency=card_concurrency,
            anomalies=all_anomalies,
            legal_hypotheses=hypotheses,
            document_requests=requests
        )
        return case
