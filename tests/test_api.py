# scripts de tests unitaires simple pour l'API
import requests
import json
import pytest
from datetime import datetime

# Configuration de base pour les tests
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

class TestAPIBasic:
    """Tests unitaires minimaux pour l'API de sentiment"""
    
    def test_health_endpoint(self):
        """Test que l'endpoint de santé répond correctement"""
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
    
    def test_predict_endpoint_structure(self):
        """Test que l'endpoint de prédiction retourne la structure attendue"""
        test_text = "Amazing service!"
        payload = {"text": test_text, "user_id": "test_user"}
        
        response = requests.post(f"{API_BASE_URL}/predict", json=payload)
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
            response = requests.post(f"{API_BASE_URL}/predict", json=payload)
            
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
        
        response = requests.post(f"{API_BASE_URL}/feedback", json=feedback_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "message" in data

if __name__ == "__main__":
    # Exécution des tests
    print(f"[!] Tests executés sur: {API_BASE_URL}")
    pytest.main([__file__, "-v"])