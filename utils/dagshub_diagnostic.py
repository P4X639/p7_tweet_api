# Script de diagnostic pour vérifier la connexion DagsHub et les artifacts
import os
import mlflow
from mlflow.tracking import MlflowClient
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_dagshub_connection():
    """Test complet de la connexion DagsHub"""
    
    username = os.getenv("DAGSHUB_USERNAME")
    repo = os.getenv("DAGSHUB_REPO") 
    token = os.getenv("DAGSHUB_TOKEN")
    run_id = os.getenv("MODEL_RUN_ID")
    
    print(f"=== DIAGNOSTIC DAGSHUB ===")
    print(f"Username: {username}")
    print(f"Repo: {repo}")
    print(f"Token: {'*' * len(token[:8]) + token[:8] if token else 'None'}")
    print(f"Run ID: {run_id}")
    
    # Configuration MLflow
    os.environ["MLFLOW_TRACKING_USERNAME"] = username
    os.environ["MLFLOW_TRACKING_PASSWORD"] = token
    
    mlflow_uri = f"https://dagshub.com/{username}/{repo}.mlflow"
    mlflow.set_tracking_uri(mlflow_uri)
    
    print(f"\n1. Test de connexion MLflow...")
    try:
        client = MlflowClient()
        print("✅ Client MLflow initialisé")
        
        # Test d'accès au run
        print(f"\n2. Test d'accès au run {run_id}...")
        run = client.get_run(run_id)
        print(f"✅ Run trouvé: {run.info.run_name}")
        print(f"   Status: {run.info.status}")
        print(f"   Start time: {run.info.start_time}")
        
        # Lister les artifacts
        print(f"\n3. Liste des artifacts du run...")
        artifacts = client.list_artifacts(run_id)
        print("📁 Artifacts disponibles:")
        for artifact in artifacts:
            print(f"   - {artifact.path} (taille: {artifact.file_size} bytes)")
        
        # Vérifier si model_config.json existe
        config_exists = any(artifact.path == "model_config.json" for artifact in artifacts)
        if config_exists:
            print("✅ model_config.json trouvé dans les artifacts")
        else:
            print("❌ model_config.json NON TROUVÉ dans les artifacts")
            print("💡 Artifacts disponibles:")
            for artifact in artifacts:
                print(f"   - {artifact.path}")
        
        return config_exists
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_direct_api_access():
    """Test direct de l'API DagsHub"""
    
    username = os.getenv("DAGSHUB_USERNAME")
    repo = os.getenv("DAGSHUB_REPO") 
    token = os.getenv("DAGSHUB_TOKEN")
    run_id = os.getenv("MODEL_RUN_ID")
    
    print(f"\n=== TEST API DIRECT ===")
    
    # Test de l'API DagsHub
    api_url = f"https://dagshub.com/{username}/{repo}.mlflow/api/2.0/mlflow/runs/get"
    
    try:
        response = requests.get(
            api_url,
            params={"run_id": run_id},
            auth=(username, token),
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✅ API DagsHub accessible")
            data = response.json()
            print(f"Run name: {data['run']['info']['run_name']}")
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur connexion API: {e}")

def suggest_solutions():
    """Suggestions de solutions"""
    
    print(f"\n=== SOLUTIONS POSSIBLES ===")
    print("1. 🔄 Problème temporaire DagsHub:")
    print("   - Attendre quelques minutes et réessayer")
    print("   - Vérifier le statut de DagsHub sur leur page")
    
    print("\n2. 🔑 Problème d'authentification:")
    print("   - Vérifier que le token DagsHub est valide")
    print("   - Régénérer un nouveau token si nécessaire")
    
    print("\n3. 📁 Artifact manquant:")
    print("   - Vérifier que model_config.json a bien été sauvegardé")
    print("   - Re-lancer l'entraînement pour créer les artifacts")
    
    print("\n4. 🆔 Run ID incorrect:")
    print("   - Vérifier le Run ID dans DagsHub UI")
    print("   - Mettre à jour MODEL_RUN_ID dans .env")
    
    print("\n5. 🌐 Alternative locale:")
    print("   - Sauvegarder le modèle localement")
    print("   - Utiliser un modèle pré-entraîné par défaut")

if __name__ == "__main__":
    config_exists = test_dagshub_connection()
    test_direct_api_access()
    suggest_solutions()
    
    if not config_exists:
        print(f"\n⚠️  RECOMMANDATION: Créer un fallback ou utiliser un autre run ID")
