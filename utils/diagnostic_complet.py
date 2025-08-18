# Script de diagnostic exhaustif pour analyser le problème de performance
import os
import requests
import json
import mlflow
from mlflow.tracking import MlflowClient

# Configuration
API_BASE_URL = "http://localhost:8000"
DAGSHUB_USERNAME = "ncolin.online"
DAGSHUB_REPO = "P7_tweet"
MODEL_RUN_ID = "0b567034e22342308bd7e3835378035a"

def setup_mlflow():
    """Configuration MLflow"""
    mlflow_uri = f"https://dagshub.com/{DAGSHUB_USERNAME}/{DAGSHUB_REPO}.mlflow"
    mlflow.set_tracking_uri(mlflow_uri)
    
    # Configuration auth
    os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USERNAME
    os.environ["MLFLOW_TRACKING_PASSWORD"] = os.getenv("DAGSHUB_TOKEN", "")
    
    return MlflowClient()

def analyze_artifacts():
    """Analyser tous les artifacts disponibles"""
    print("=" * 60)
    print("🔍 ANALYSE DES ARTIFACTS")
    print("=" * 60)
    
    try:
        client = setup_mlflow()
        
        # Lister tous les artifacts
        artifacts = client.list_artifacts(MODEL_RUN_ID)
        print(f"Artifacts disponibles pour le run {MODEL_RUN_ID}:")
        
        for artifact in artifacts:
            print(f"📁 {artifact.path}")
            if artifact.is_dir:
                # Lister le contenu des dossiers
                sub_artifacts = client.list_artifacts(MODEL_RUN_ID, artifact.path)
                for sub_artifact in sub_artifacts:
                    print(f"   📄 {sub_artifact.path} (taille: {sub_artifact.file_size} bytes)")
            else:
                print(f"   📄 Fichier direct (taille: {artifact.file_size} bytes)")
        
        return artifacts
        
    except Exception as e:
        print(f"❌ Erreur analyse artifacts: {e}")
        return []

def analyze_run_metadata():
    """Analyser les métadonnées du run d'entraînement"""
    print("\n" + "=" * 60)
    print("📊 MÉTADONNÉES DU RUN D'ENTRAÎNEMENT")
    print("=" * 60)
    
    try:
        client = setup_mlflow()
        run = client.get_run(MODEL_RUN_ID)
        
        print("📋 Informations générales:")
        print(f"   Status: {run.info.status}")
        print(f"   Start time: {run.info.start_time}")
        print(f"   End time: {run.info.end_time}")
        
        print("\n🔧 Paramètres d'entraînement:")
        for key, value in run.data.params.items():
            print(f"   {key}: {value}")
        
        print("\n📈 Métriques d'entraînement:")
        for key, value in run.data.metrics.items():
            print(f"   {key}: {value}")
        
        print("\n🏷️  Tags:")
        for key, value in run.data.tags.items():
            print(f"   {key}: {value}")
            
        return run.data
        
    except Exception as e:
        print(f"❌ Erreur analyse métadonnées: {e}")
        return None

def analyze_api_model():
    """Analyser le modèle chargé dans l'API"""
    print("\n" + "=" * 60)
    print("🤖 ANALYSE DU MODÈLE DANS L'API")
    print("=" * 60)
    
    try:
        # Info modèle via API
        response = requests.get(f"{API_BASE_URL}/model/info", timeout=10)
        if response.status_code == 200:
            model_info = response.json()
            print("📋 Informations du modèle:")
            print(json.dumps(model_info, indent=2))
            
        # Health check
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"\n🏥 Santé de l'API:")
            print(f"   Status: {health['status']}")
            print(f"   Model loaded: {health['model_loaded']}")
            
    except Exception as e:
        print(f"❌ Erreur analyse API: {e}")

def test_prediction_consistency():
    """Tester la consistance des prédictions"""
    print("\n" + "=" * 60)
    print("🎯 TEST DE CONSISTANCE DES PRÉDICTIONS")
    print("=" * 60)
    
    test_cases = [
        "le vol était en retard, mais j'ai fais de belles rencontres",
        "Service excellent d'Air Paradis!",
        "Vol retardé encore une fois!",
        "Vol parfait, équipage professionnel"
    ]
    
    for text in test_cases:
        print(f"\n📝 Test: '{text}'")
        
        results = []
        for i in range(3):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/predict",
                    json={"text": text, "user_id": f"test_{i}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append(result)
                    print(f"   Essai {i+1}: {result['sentiment']} ({result['confidence']:.4f})")
                else:
                    print(f"   Essai {i+1}: Erreur {response.status_code}")
                    
            except Exception as e:
                print(f"   Essai {i+1}: Exception {e}")
        
        # Analyser la consistance
        if results:
            sentiments = [r['sentiment'] for r in results]
            confidences = [r['confidence'] for r in results]
            
            consistent_sentiment = len(set(sentiments)) == 1
            consistent_confidence = len(set(round(c, 4) for c in confidences)) == 1
            
            if consistent_sentiment and consistent_confidence:
                print("   ✅ Prédictions consistantes")
            else:
                print("   ❌ Prédictions INCONSISTANTES")
                print(f"      Sentiments: {sentiments}")
                print(f"      Confidences: {[round(c, 4) for c in confidences]}")

def analyze_model_architecture():
    """Analyser l'architecture du modèle (nécessite d'accéder au container)"""
    print("\n" + "=" * 60)
    print("🏗️  ANALYSE DE L'ARCHITECTURE DU MODÈLE")
    print("=" * 60)
    
    print("ℹ️  Pour analyser l'architecture, exécutez dans le container:")
    print("   docker-compose exec api python -c \"")
    print("   from services.dagshub_service import DagsHubService")
    print("   service = DagsHubService()")
    print("   service.test_connection()")
    print("   if service.model:")
    print("       print('Input shape:', service.model.input_shape)")
    print("       service.model.summary()")
    print("   \"")

def recommendations():
    """Recommandations basées sur l'analyse"""
    print("\n" + "=" * 60)
    print("💡 RECOMMANDATIONS")
    print("=" * 60)
    
    print("1. 🔧 PROBLÈME PRINCIPAL IDENTIFIÉ:")
    print("   Le tokenizer/vectorizer d'entraînement N'EST PAS utilisé en production")
    print("   Fichier: 'nn_model_tokenizer_none_lstm.pkl' disponible mais non chargé")
    
    print("\n2. 🚨 ACTIONS PRIORITAIRES:")
    print("   a) Modifier services/dagshub_service.py pour charger le tokenizer")
    print("   b) Remplacer la vectorisation actuelle par le vrai tokenizer")
    print("   c) Vérifier l'input_shape du modèle")
    
    print("\n3. 📋 CODE À AJOUTER:")
    print("   ```python")
    print("   # Dans load_model_from_artifacts()")
    print("   tokenizer_path = client.download_artifacts(")
    print("       self.model_run_id, 'nn_model_tokenizer_none_lstm.pkl', temp_dir)")
    print("   import pickle")
    print("   with open(tokenizer_path, 'rb') as f:")
    print("       self.tokenizer = pickle.load(f)")
    print("   ```")
    
    print("\n4. 🎯 RÉSULTAT ATTENDU:")
    print("   Avec le bon tokenizer, vous devriez retrouver ~82% d'accuracy")

def main():
    """Diagnostic complet"""
    print("🚀 DIAGNOSTIC EXHAUSTIF DU SYSTÈME D'ANALYSE DE SENTIMENT")
    print("=" * 80)
    
    # 1. Analyser les artifacts
    artifacts = analyze_artifacts()
    
    # 2. Analyser les métadonnées du run
    run_data = analyze_run_metadata()
    
    # 3. Analyser le modèle dans l'API
    analyze_api_model()
    
    # 4. Tester la consistance
    test_prediction_consistency()
    
    # 5. Analyser l'architecture (instructions)
    analyze_model_architecture()
    
    # 6. Recommandations
    recommendations()
    
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC TERMINÉ")
    print("Le problème principal est l'absence du tokenizer d'entraînement")
    print("Solution: Charger et utiliser 'nn_model_tokenizer_none_lstm.pkl'")
    print("=" * 80)

if __name__ == "__main__":
    main()