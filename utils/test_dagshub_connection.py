# Script de test pour vérifier la connexion DagsHub/MLflow
import os
import sys

def test_environment():
    """Test des variables d'environnement"""
    print("=== TEST VARIABLES D'ENVIRONNEMENT ===")
    
    required_vars = ["DAGSHUB_USERNAME", "DAGSHUB_REPO", "DAGSHUB_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "DAGSHUB_TOKEN":
                print(f"✅ {var}: ***{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NON DÉFINI")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Variables manquantes: {missing_vars}")
        return False
    
    print("✅ Toutes les variables sont définies")
    return True

def test_mlflow_connection():
    """Test de connexion MLflow sans OAuth"""
    print("\n=== TEST CONNEXION MLFLOW ===")
    
    try:
        import mlflow
        
        # Configuration des variables d'environnement
        username = os.getenv("DAGSHUB_USERNAME")
        repo = os.getenv("DAGSHUB_REPO")
        token = os.getenv("DAGSHUB_TOKEN")
        
        os.environ["MLFLOW_TRACKING_USERNAME"] = username
        os.environ["MLFLOW_TRACKING_PASSWORD"] = token
        os.environ["DAGSHUB_NO_BROWSER"] = "true"
        
        # Configuration MLflow directe
        mlflow_uri = f"https://dagshub.com/{username}/{repo}.mlflow"
        print(f"URI MLflow: {mlflow_uri}")
        
        mlflow.set_tracking_uri(mlflow_uri)
        
        # Test de connexion
        client = mlflow.tracking.MlflowClient()
        experiments = client.search_experiments(max_results=3)
        
        print(f"✅ Connexion réussie - {len(experiments)} expérience(s) trouvée(s)")
        
        # Afficher les expériences
        for exp in experiments:
            print(f"  - {exp.name} (ID: {exp.experiment_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion MLflow: {e}")
        return False

def test_dagshub_service():
    """Test du service DagsHub"""
    print("\n=== TEST SERVICE DAGSHUB ===")
    
    try:
        # Import du service modifié
        sys.path.append('.')
        from dagshub_service import DagsHubService
        
        # Initialisation du service
        service = DagsHubService()
        
        # Test de connexion
        if service.test_connection():
            print("✅ Service DagsHub initialisé avec succès")
            
            # Test de chargement de modèle (optional)
            print("\n--- Test chargement modèle ---")
            model_loaded = service.load_model_from_dagshub("iris_model")
            if model_loaded:
                print("✅ Modèle chargé depuis DagsHub")
            else:
                print("⚠️  Modèle fallback créé")
            
            # Test de prédiction
            print("\n--- Test prédiction ---")
            result = service.predict("This is a test tweet")
            print(f"Résultat prédiction: {result}")
            
            return True
        else:
            print("❌ Échec test connexion service")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test service: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DES TESTS DAGSHUB/MLFLOW\n")
    
    # Test 1: Variables d'environnement
    if not test_environment():
        print("\n❌ Tests échoués - Variables d'environnement manquantes")
        sys.exit(1)
    
    # Test 2: Connexion MLflow directe
    if not test_mlflow_connection():
        print("\n❌ Tests échoués - Connexion MLflow impossible")
        sys.exit(1)
    
    # Test 3: Service DagsHub
    if not test_dagshub_service():
        print("\n❌ Tests échoués - Service DagsHub non fonctionnel")
        sys.exit(1)
    
    print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
    print("✅ Votre configuration DagsHub/MLflow est opérationnelle")
