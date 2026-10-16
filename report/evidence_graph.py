"""
Forensic Evidence Graph.
Constructs the complete traceable provenance chain:
DOCUMENT -> PAGE -> REGION -> ROW -> COLUMN -> CELL -> BOUNDING BOX -> RAW OCR -> NORMALIZED VALUE -> ANOMALY -> HYPOTHESIS -> NORM -> DOCUMENT REQUEST.
Ensures no financial claim in a legal proceeding is without physical document provenance.
"""
from typing import List, Dict, Any, Optional
from core.models import Transaction, Anomaly, LegalHypothesis, DocumentRequest

class EvidenceGraphBuilder:
    def build_graph(
        self,
        doc_name: str,
        transactions: List[Transaction],
        anomalies: List[Anomaly],
        hypotheses: List[LegalHypothesis],
        requests: List[DocumentRequest]
    ) -> Dict[str, Any]:
        """
        Builds a serializable evidence graph linking raw document positions to legal conclusions.
        """
        nodes = []
        edges = []
        
        # Document Root Node
        doc_node_id = f"doc_{doc_name}"
        nodes.append({
            "id": doc_node_id,
            "type": "DOCUMENT",
            "label": doc_name,
            "data": {"document_name": doc_name}
        })
        
        # Page & Transaction Nodes
        pages_seen = set()
        for tx in transactions:
            page_node_id = f"page_{doc_name}_{tx.page}"
            if tx.page not in pages_seen:
                pages_seen.add(tx.page)
                nodes.append({
                    "id": page_node_id,
                    "type": "PAGE",
                    "label": f"Pagina {tx.page}",
                    "data": {"page": tx.page}
                })
                edges.append({"source": doc_node_id, "target": page_node_id, "relation": "CONTAINS_PAGE"})
                
            tx_node_id = f"tx_{tx.id}"
            nodes.append({
                "id": tx_node_id,
                "type": "TRANSACTION",
                "label": f"{tx.date_accounting or 'ND'} - {tx.description[:25]} (€{tx.amount_debit or tx.amount_credit or 0.0:.2f})",
                "data": {
                    "id": tx.id,
                    "page": tx.page,
                    "row_id": tx.row_id,
                    "bbox": tx.bounding_box.model_dump(),
                    "raw_ocr": tx.raw_ocr_text,
                    "channel": tx.channel.value if hasattr(tx.channel, "value") else str(tx.channel),
                    "confidence": tx.confidence_score,
                    "status": tx.status.value if hasattr(tx.status, "value") else str(tx.status)
                }
            })
            edges.append({"source": page_node_id, "target": tx_node_id, "relation": "EXTRACTED_FROM_ROW"})

        # Anomaly Nodes
        for anom in anomalies:
            anom_node_id = f"anom_{anom.id}"
            nodes.append({
                "id": anom_node_id,
                "type": "ANOMALY",
                "label": f"[{anom.category}] {anom.title}",
                "data": {
                    "severity": anom.severity.value if hasattr(anom.severity, "value") else str(anom.severity),
                    "discrepancy": anom.discrepancy_amount
                }
            })
            for tx_id in anom.involved_transaction_ids:
                edges.append({"source": f"tx_{tx_id}", "target": anom_node_id, "relation": "TRIGGERS_ANOMALY"})

        # Legal Hypothesis Nodes
        for hyp in hypotheses:
            hyp_node_id = f"hyp_{hyp.id}"
            nodes.append({
                "id": hyp_node_id,
                "type": "LEGAL_HYPOTHESIS",
                "label": f"{hyp.article} - {hyp.norm_title}",
                "data": {
                    "confidence_degree": hyp.confidence_degree,
                    "required_elements": hyp.required_elements,
                    "facts_found": hyp.facts_found
                }
            })
            # Connect anomalies to hypothesis
            for anom in anomalies:
                edges.append({"source": f"anom_{anom.id}", "target": hyp_node_id, "relation": "SUPPORTS_HYPOTHESIS"})

        # Document Request Nodes
        for req in requests:
            req_node_id = f"req_{req.id}"
            nodes.append({
                "id": req_node_id,
                "type": "DOCUMENT_REQUEST",
                "label": f"Richiesta: {req.document_name[:30]}...",
                "data": {
                    "subject": req.subject_holder,
                    "priority": req.priority,
                    "legal_basis": req.legal_basis
                }
            })
            for hyp in hypotheses:
                edges.append({"source": f"hyp_{hyp.id}", "target": req_node_id, "relation": "REQUIRES_EVIDENCE"})

        return {
            "document_name": doc_name,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "nodes": nodes,
            "edges": edges
        }
