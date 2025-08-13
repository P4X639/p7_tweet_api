# Tests pour l'API de prédiction
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

def test_api_import():
    """Test que les modules s'importent correctement"""
    try:
        from api.sentiment_api import create_api
        from services.dagshub_service import DagsHubService
        assert True
    except ImportError as e:
        pytest.fail(f"Erreur d'import: {e}")

def test_preprocessing_import():
    """Test que le module de prétraitement s'importe correctement"""
    try:
        from utils.preprocessing import preprocess_for_model, clean_text_classical
        assert True
    except ImportError as e:
        pytest.fail(f"Erreur d'import preprocessing: {e}")

# Tests plus complets à ajouter après déploiement
def test_text_cleaning():
    """Test basique des fonctions de nettoyage"""
    from utils.preprocessing import clean_text_classical, clean_text_bert
    
    text = "OMG! I can't believe this #amazing product!!! "
    
    classical = clean_text_classical(text, lemmatize=False)
    bert = clean_text_bert(text)
    
    assert len(classical) > 0
    assert len(bert) > 0
    assert classical != bert  # Vérifier que les méthodes diffèrent
