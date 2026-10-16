"""
Strict Forensic Channel Classifier.
Disambiguates ATM, SPORTELLO AUTOMATICO, SPORTELLO FISICO, CASSA, and OPERATORE.
CRITICAL MANDATE:
The word "SPORTELLO" alone does NOT mean physical counter!
"PRELIEVO POSTAMAT NOSTRO SPORTELLO AUTOMATICO" -> ATM / SPORTELLO_AUTOMATICO (NOT SPORTELLO_FISICO).
"""
import re
from typing import Tuple, Optional, Dict
from core.models import ChannelType

class ChannelClassifier:
    # Pattern definitions
    ATM_PATTERNS = [
        r'\bPOSTAMAT\b',
        r'\bATM\b',
        r'\bBANCOMAT\b',
        r'\bSPORTELLO\s+AUTOMATICO\b',
        r'\bPRELIEVO\s+CARTA\b',
        r'\bCARD\s+DISPENSING\b',
        r'\bCIRCOLO\s+ATM\b',
        r'\bAUTOMATED\s+TELLER\b'
    ]
    
    PHYSICAL_COUNTER_PATTERNS = [
        r'\bSPORTELLO\s+(?:SEDE|FILIALE|OPERATORE|FISICO)\b',
        r'\bCASSA\s+OPERATORE\b',
        r'\bOPERAZIONE\s+DI\s+SPORTELLO\b',
        r'\bDISPOSIZIONE\s+ALLO\s+SPORTELLO\b',
        r'\bA\s+MEZZO\s+CASSA\b',
        r'\bDISTINTA\s+DI\s+CASSA\b',
        r'\bCASSIERE\b',
        r'\bOPERATORE\s+DI\s+SPORTELLO\b'
    ]

    POS_PATTERNS = [
        r'\bPOS\b',
        r'\bPAGAMENTO\s+POS\b',
        r'\bTRANSAZIONE\s+POS\b',
        r'\bESERCENTE\b',
        r'\bACQUISTO\s+CARTA\b'
    ]

    TRANSFER_PATTERNS = [
        r'\bBONIFICO\b',
        r'\bPOSTAGIRO\b',
        r'\bGIROCONTO\b',
        r'\bSEPA\s+CREDIT\s+TRANSFER\b'
    ]

    def classify(self, text: str) -> Tuple[ChannelType, str]:
        """
        Classifies transaction channel based on textual context, keywords, and qualifiers.
        Returns:
            (channel: ChannelType, channel_detail: str)
        """
        upper = text.upper()
        
        # 1. Check for ATM / Postamat / Sportello Automatico first
        # Look specifically for "SPORTELLO AUTOMATICO"
        if "SPORTELLO AUTOMATICO" in upper or "POSTAMAT" in upper or "ATM" in upper or "BANCOMAT" in upper:
            if "POSTAMAT" in upper:
                return ChannelType.ATM, "POSTAMAT_SPORTELLO_AUTOMATICO"
            elif "SPORTELLO AUTOMATICO" in upper:
                return ChannelType.ATM, "SPORTELLO_AUTOMATICO"
            else:
                return ChannelType.ATM, "CIRCUITO_ATM"

        # 2. Check for explicit Physical Counter / Cassa Operatore
        for pat in self.PHYSICAL_COUNTER_PATTERNS:
            if re.search(pat, upper):
                return ChannelType.SPORTELLO_FISICO, "SPORTELLO_FISICO_OPERATORE"

        # 3. Check POS / Pagamenti Carta
        for pat in self.POS_PATTERNS:
            if re.search(pat, upper):
                return ChannelType.POS, "PAGAMENTO_POS_ESERCENTE"

        # 4. Check Bonifici / Trasferimenti
        for pat in self.TRANSFER_PATTERNS:
            if re.search(pat, upper):
                return ChannelType.BONIFICO_ONLINE, "BONIFICO_POSTAGIRO"

        # 5. Generic word "SPORTELLO" without "AUTOMATICO" or "OPERATORE"
        # Forensically: NEVER assume physical counter!
        if "SPORTELLO" in upper:
            return ChannelType.UNKNOWN, "SPORTELLO_AMBIGUO_RICHIEDE_VERIFICA"

        return ChannelType.UNKNOWN, "CANALE_NON_DETERMINATO"

    def extract_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extracts ATM terminal ID, card number, and operation reference if present.
        """
        upper = text.upper()
        meta = {
            "atm_id": None,
            "card_number": None,
            "operation_code": None
        }
        
        # ATM ID pattern: e.g. "ATM N. 12345" or "TERMINALE 8921" or "SPORT. 123"
        atm_match = re.search(r'\b(?:ATM|SPORTELLO|TERMINALE|TERM)\b\s*(?:N\.?|NUM\.?)?\s*([A-Z0-9]{3,10})', upper)
        if atm_match:
            meta["atm_id"] = atm_match.group(1)

        # Card mask: e.g. "CARTA N. 5354 **** 1234" or "CARTA **** 1234" or "PAN ...1234"
        card_match = re.search(r'(?:CARTA|PAN|TESSERA)?.*?(?:[\*X]{2,16}\s*|\.{2,10}\s*)(\d{4})\b', upper)
        if card_match:
            meta["card_number"] = f"****{card_match.group(1)}"

        # Operation code / reference: e.g. "OPERAZ. 000123" or "RIF. 98765432"
        op_match = re.search(r'(?:OPERAZ(?:IONE|\.)?|RIF(?:ERIMENTO|\.)?|OP\.)\s*(?:N\.?)?\s*([0-9]{4,12})', upper)
        if op_match:
            meta["operation_code"] = op_match.group(1)

        return meta
