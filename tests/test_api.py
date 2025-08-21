import os
import sys
import requests
import json
import pytest
from datetime import datetime

def get_api_base_url():
    """Récupère l'URL de base de l'API avec plusieurs fallbacks"""
    # Priorité 1: Variable d'environnement
    api_url = os.getenv("API_BASE_URL")
    if api_url:
        print(f"[!] Utilisation API_BASE_URL: {api_url}")
        return api_url
    
    # Priorité 2: Argument de ligne de commande
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        api_url = sys.argv[1]
        print(f"[!] Utilisation argument CLI: {api_url}")
        return api_url
    
    # Priorité 3: Default localhost
    api_url = "http://localhost:8000"
    print(f"[!] Utilisation default: {api_url}")
    return api_url

API_BASE_URL = get_api_base_url()

class TestAPIBasic:
    """Tests unitaires minimaux pour l'API de sentiment"""
    
    def test_health_endpoint(self):
        """Test que l'endpoint de santé répond correctement"""
        print(f"[DEBUG] Test health sur: {API_BASE_URL}")
        response = requests.get(f"{API_BASE_URL}/health", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
    
    def test_predict_endpoint_structure(self):
        """Test que l'endpoint de prédiction retourne la structure attendue"""
        test_text = "Amazing service!"
        payload = {"text": test_text, "user_id": "test_user"}
        
        print(f"[DEBUG] Test predict sur: {API_BASE_URL}")
        response = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        # Vérifier les champs obligatoires
        assert "sentiment" in data
        assert "confidence" in data
        assert "text" in data
        assert data["text"] == test_text
    
    def test_predict_sentiment_values(self):
        """Test que les valeurs de sentiment sont correctes"""
        test_cases = [
            {"text": "Great service!", "expected_sentiment": "positive"},
            {"text": "Terrible experience", "expected_sentiment": "negative"}
        ]
        
        for case in test_cases:
            payload = {"text": case["text"], "user_id": "test_user"}
            response = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=30)
            
            assert response.status_code == 200
            data = response.json()
            
            # Vérifier que le sentiment est valide
            assert data["sentiment"] in ["positive", "negative"]
            # Vérifier que la confiance est entre 0 et 1
            assert 0 <= data["confidence"] <= 1
    
    def test_feedback_endpoint(self):
        """Test que l'endpoint de feedback fonctionne"""
        feedback_data = {
            "feedback_type": "correct",
            "prediction_id": "test-123",
            "user_id": "test_user",
            "original_sentiment": "positive",
            "original_confidence": 0.85,
            "original_text": "Test text"
        }
        
        response = requests.post(f"{API_BASE_URL}/feedback", json=feedback_data, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "message" in data

if __name__ == "__main__":
    print(f"[!] Tests exécutés contre: {API_BASE_URL}")
    pytest.main([__file__, "-v"])