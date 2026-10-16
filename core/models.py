"""
Data models representing the complete forensic provenance chain and analytics.
Strictly separates RAW DATA != NORMALIZED DATA != INTERPRETED DATA.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import datetime

class ChannelType(str, Enum):
    ATM = "ATM"
    SPORTELLO_AUTOMATICO = "SPORTELLO_AUTOMATICO"
    SPORTELLO_FISICO = "SPORTELLO_FISICO"
    CASSA = "CASSA"
    OPERATORE = "OPERATORE"
    POSTAMAT = "POSTAMAT"
    BONIFICO_ONLINE = "BONIFICO_ONLINE"
    POS = "POS"
    UNKNOWN = "UNKNOWN"

class TransactionType(str, Enum):
    PENSIONE = "PENSIONE"
    STIPENDIO = "STIPENDIO"
    BONIFICO_IN = "BONIFICO_IN"
    BONIFICO_OUT = "BONIFICO_OUT"
    PRELIEVO_ATM = "PRELIEVO_ATM"
    PRELIEVO_SPORTELLO_FISICO = "PRELIEVO_SPORTELLO_FISICO"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
    PENSION_CREDIT = "PENSION_CREDIT"
    SALARY_CREDIT = "SALARY_CREDIT"
    PAGAMENTO_CARTA = "PAGAMENTO_CARTA"
    POS = "POS"
    POS_PAYMENT = "POS_PAYMENT"
    ADDEBITO = "ADDEBITO"
    RID_SDD = "RID_SDD"
    ASSEGNO = "ASSEGNO"
    VERSAMENTO_CONTANTE = "VERSAMENTO_CONTANTE"
    DEPOSIT = "DEPOSIT"
    COMMISSIONE = "COMMISSIONE"
    BANK_FEE = "BANK_FEE"
    INTERESSI = "INTERESSI"
    IMPOSTE = "IMPOSTE"
    SPESE = "SPESE"
    GIROCONTO = "GIROCONTO"
    TRASFERIMENTO = "TRASFERIMENTO"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    ALTRO = "ALTRO"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class ReviewStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CORRECTED = "CORRECTED"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"
    POSSIBLE_OCR_AMBIGUOUS = "POSSIBLE_OCR_AMBIGUOUS"

class AnomalyCategory(str, Enum):
    AMOUNT_ANOMALY = "AMOUNT_ANOMALY"
    FREQUENCY_ANOMALY = "FREQUENCY_ANOMALY"
    TEMPORAL_ANOMALY = "TEMPORAL_ANOMALY"
    LOCATION_ANOMALY = "LOCATION_ANOMALY"
    CARD_ANOMALY = "CARD_ANOMALY"
    COUNTERPARTY_ANOMALY = "COUNTERPARTY_ANOMALY"
    BALANCE_ANOMALY = "BALANCE_ANOMALY"
    SEQUENCE_ANOMALY = "SEQUENCE_ANOMALY"
    DOCUMENT_ANOMALY = "DOCUMENT_ANOMALY"
    OCR_ANOMALY = "OCR_ANOMALY"
    RECONCILIATION_ANOMALY = "RECONCILIATION_ANOMALY"
    BEHAVIOR_CHANGE = "BEHAVIOR_CHANGE"
    LEGAL_RELEVANCE = "LEGAL_RELEVANCE"

class EpistemicLevel(str, Enum):
    FATTO_ACCERTATO = "FATTO_ACCERTATO"
    ANOMALIA = "ANOMALIA"
    IPOTESI = "IPOTESI"
    PROFILO_GIURIDICO = "PROFILO_GIURIDICO"
    ILLECITO_ACCERTATO = "ILLECITO_ACCERTATO"

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

class RawOCRToken(BaseModel):
    page: int
    bbox: BoundingBox
    text: str
    confidence: float
    source_image: Optional[str] = None
    pass_type: str = "PASS_A"

class Cell(BaseModel):
    column_name: str
    raw_text: str
    normalized_value: Any = None
    bbox: BoundingBox
    confidence: float
    source_image: Optional[str] = None

class Row(BaseModel):
    page: int
    row_id: str
    y_position: int
    cells: List[Cell] = Field(default_factory=list)
    raw_line_text: str = ""

class Transaction(BaseModel):
    id: str
    document_name: str
    page: int
    row_id: str
    
    # Dates and Times
    date_accounting: Optional[str] = None
    date_value: Optional[str] = None
    time_str: Optional[str] = None
    
    # Descriptions (RAW vs NORMALIZED)
    description: str
    description_raw: Optional[str] = None
    description_normalized: Optional[str] = None
    
    # Financial Amounts
    amount_debit: Optional[float] = None
    amount_credit: Optional[float] = None
    amount: Optional[float] = None
    direction: Optional[str] = None  # 'DEBIT' or 'CREDIT'
    balance: Optional[float] = None
    balance_after: Optional[float] = None
    
    # Classifications
    operation_code: Optional[str] = None
    atm_id: Optional[str] = None
    card_number: Optional[str] = None
    card_id: Optional[str] = None
    channel: ChannelType = ChannelType.UNKNOWN
    channel_detail: str = "UNKNOWN"
    transaction_type: TransactionType = TransactionType.OTHER
    category: str = "ALTRO"
    
    # Counterparty & Location
    counterparty: Optional[str] = None
    counterparty_normalized: Optional[str] = None
    branch: Optional[str] = None
    atm: Optional[str] = None
    location: Optional[str] = None
    reference_number: Optional[str] = None
    
    # Forensic Provenance & Evidence
    bounding_box: BoundingBox
    image_crop_path: Optional[str] = None
    raw_ocr_text: str
    source_text: Optional[str] = None
    confidence_score: float = 0.0
    ocr_confidence: float = 0.0
    extraction_confidence: float = 0.0
    field_confidences: Dict[str, float] = Field(default_factory=dict)
    
    # Status & Audit
    status: ReviewStatus = ReviewStatus.VERIFIED
    validation_status: str = "VERIFIED"
    anomaly_score: int = 0
    legal_relevance: Optional[str] = None
    evidence_links: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    human_correction: Optional[Dict[str, Any]] = None
    audit_history: List[Dict[str, Any]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if self.description_raw is None:
            self.description_raw = self.raw_ocr_text or self.description
        if self.description_normalized is None:
            self.description_normalized = self.description
        if self.source_text is None:
            self.source_text = self.raw_ocr_text
        if self.ocr_confidence == 0.0 and self.confidence_score > 0.0:
            self.ocr_confidence = self.confidence_score
        if self.card_id is None and self.card_number:
            self.card_id = self.card_number
        if self.balance_after is None and self.balance is not None:
            self.balance_after = self.balance
        if self.amount is None:
            if self.amount_debit is not None:
                self.amount = self.amount_debit
                self.direction = "DEBIT"
            elif self.amount_credit is not None:
                self.amount = self.amount_credit
                self.direction = "CREDIT"

class StatementSummary(BaseModel):
    document_name: str
    page_count: int
    initial_balance: Optional[float] = None
    total_debits: float = 0.0
    total_credits: float = 0.0
    final_balance_reported: Optional[float] = None
    final_balance_calculated: Optional[float] = None
    discrepancy: float = 0.0
    is_mathematically_reconciled: bool = False
    transaction_count: int = 0
    warnings: List[str] = Field(default_factory=list)

class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Anomaly(BaseModel):
    id: str
    category: str
    severity: AnomalySeverity
    score: int = 0
    title: str
    description: str
    involved_transaction_ids: List[str] = Field(default_factory=list)
    involved_dates: List[str] = Field(default_factory=list)
    discrepancy_amount: Optional[float] = None
    explanation: str
    evidence_links: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    missing_documentation: Optional[str] = None
    legal_relevance: Optional[str] = None

class CardProfile(BaseModel):
    card_id: str
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    active_period: Optional[str] = None
    number_of_transactions: int = 0
    cash_withdrawals: int = 0
    total_cash: float = 0.0
    locations: List[str] = Field(default_factory=list)
    atm_locations: List[str] = Field(default_factory=list)
    branches: List[str] = Field(default_factory=list)
    first_operation: Optional[str] = None
    last_operation: Optional[str] = None
    replacement_relationship: Optional[str] = None
    overlap_with_other_cards: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)

class CardConcurrencyRecord(BaseModel):
    id: str
    date: str
    cards_involved: List[str]
    transaction_ids: List[str]
    time_difference_minutes: Optional[int] = None
    locations: List[str] = Field(default_factory=list)
    classification: str = "Compatibile"
    explanation: str = ""

class PeriodicReconciliation(BaseModel):
    period_id: str
    period_type: str  # 'QUARTERLY', 'YEARLY'
    period_name: str  # es. 'Q1 2016', 'Anno 2016'
    year: int
    quarter: Optional[int] = None
    opening_balance: float
    total_credits: float
    total_debits: float
    total_cash_withdrawals: float = 0.0
    total_transfers: float = 0.0
    total_fees: float = 0.0
    theoretical_balance: float
    actual_balance: float
    difference: float
    is_reconciled: bool
    transaction_count: int
    unreconciled_reason: Optional[str] = None

class CounterpartyProfile(BaseModel):
    name: str
    normalized_name: str
    first_seen: str
    last_seen: str
    operation_count: int
    total_credits: float = 0.0
    total_debits: float = 0.0
    average_amount: float = 0.0
    max_amount: float = 0.0
    frequency: str = "Occasionale"
    periodicity: str = "Nessuna"
    is_primary_income_source: bool = False
    is_sole_income_source: bool = False

class LegalHypothesis(BaseModel):
    id: str
    epistemic_level: EpistemicLevel = EpistemicLevel.IPOTESI
    norm_reference: str
    norm_title: str
    article: str
    jurisdiction: str = "ITALIAN_LAW"
    applicable_date: Optional[str] = None
    temporal_version: str = "VIGENTE ALLA DATA DEL FATTO"
    required_elements: List[str]
    facts_found: List[str]
    missing_facts: List[str]
    confidence_degree: str
    suggested_documents: List[str]
    forensic_notes: str

class DocumentRequest(BaseModel):
    id: str
    recipient: str = "ISTITUTO BANCARIO / POSTALE"
    document_name: str
    subject_holder: str
    purpose: str
    fact_to_prove: str
    priority: str = "HIGH"
    legal_basis: str

class ForensicCase(BaseModel):
    case_id: str
    title: str
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    documents: List[str] = Field(default_factory=list)
    transactions: List[Transaction] = Field(default_factory=list)
    summary: Optional[StatementSummary] = None
    quarterly_reports: List[PeriodicReconciliation] = Field(default_factory=list)
    annual_reports: List[PeriodicReconciliation] = Field(default_factory=list)
    card_profiles: Dict[str, CardProfile] = Field(default_factory=dict)
    card_concurrency: List[CardConcurrencyRecord] = Field(default_factory=list)
    counterparties: Dict[str, CounterpartyProfile] = Field(default_factory=dict)
    anomalies: List[Anomaly] = Field(default_factory=list)
    legal_hypotheses: List[LegalHypothesis] = Field(default_factory=list)
    document_requests: List[DocumentRequest] = Field(default_factory=list)
