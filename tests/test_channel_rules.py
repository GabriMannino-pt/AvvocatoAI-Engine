"""
Unit tests for the Channel Classifier.
Verifies the mandatory rule:
"PRELIEVO POSTAMAT NOSTRO SPORTELLO AUTOMATICO" must NEVER be classified as SPORTELLO_FISICO.
"""
import pytest
from financial.channel_classifier import ChannelClassifier
from core.models import ChannelType

def test_postamat_sportello_automatico():
    classifier = ChannelClassifier()
    text = "PRELIEVO POSTAMAT NOSTRO SPORTELLO AUTOMATICO N. 8821"
    channel, detail = classifier.classify(text)
    
    assert channel == ChannelType.ATM
    assert "SPORTELLO_AUTOMATICO" in detail or "POSTAMAT" in detail
    assert channel != ChannelType.SPORTELLO_FISICO

def test_sportello_fisico_cassa():
    classifier = ChannelClassifier()
    text = "DISPOSIZIONE ALLO SPORTELLO FISICO CASSA OPERATORE"
    channel, detail = classifier.classify(text)
    
    assert channel == ChannelType.SPORTELLO_FISICO
    assert "SPORTELLO_FISICO" in detail

def test_ambiguous_sportello():
    classifier = ChannelClassifier()
    text = "COMMISSIONE SPORTELLO"
    channel, detail = classifier.classify(text)
    
    # Must NOT assume physical counter automatically!
    assert channel == ChannelType.UNKNOWN
    assert "AMBIGUO" in detail

def test_extract_atm_metadata():
    classifier = ChannelClassifier()
    text = "PRELIEVO POSTAMAT TERMINALE 8921 CARTA N. 5354 **** 1234 OPERAZ. 000456"
    meta = classifier.extract_metadata(text)
    
    assert meta["atm_id"] == "8921"
    assert meta["card_number"] == "****1234"
    assert meta["operation_code"] == "000456"
