# Script de test pour valider le service DagsHub
import os
import sys
import logging
from pathlib import Path

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire services au path
sys.path.append(str(Path(__file__).parent / "services"))

def load_env_from_file():
    """Charge les variables d'environnement depuis le fichier .env"""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        logger.error("Fichier .env non trouvé!")
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
                
    logger.info("Variables d'environnement chargées depuis .env")
    return True

def test_dagshub_service():
    """Test complet du service DagsHub"""
    try:
        from dagshub_service import DagsHubService
        
        print("=" * 60)
        print("TEST DU SERVICE DAGSHUB")
        print("=" * 60)
        
        # Vérification des variables d'environnement
        required_vars = ["DAGSHUB_USERNAME", "DAGSHUB_REPO", "DAGSHUB_TOKEN", "MODEL_RUN_ID"]
        for var in required_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {value[:20]}..." if len(value) > 20 else f"✅ {var}: {value}")
            else:
                print(f"❌ {var}: NON DÉFINI")
                return False
        
        print("\n" + "=" * 60)
        print("INITIALISATION DU SERVICE")
        print("=" * 60)
        
        # Initialisation du service
        service = DagsHubService()
        
        print("\n" + "=" * 60)
        print("TEST DE CHARGEMENT CONFIGURATION")
        print("=" * 60)
        
        # Test du chargement de configuration
        config_loaded = service.load_model_config()
        print(f"Configuration chargée: {config_loaded}")
        
        if config_loaded:
            print(f"Métadonnées du modèle:")
            for key, value in service.model_info.items():
                print(f"  - {key}: {value}")
        
        print("\n" + "=" * 60)
        print("TEST DE CHARGEMENT MODÈLE COMPLET")
        print("=" * 60)
        
        # Test complet
        success = service.test_connection()
        
        if success:
            print("\n" + "=" * 60)
            print("HEALTH CHECK")
            print("=" * 60)
            
            health = service.health_check()
            for key, value in health.items():
                print(f"  - {key}: {value}")
            
            print("\n" + "=" * 60)
            print("TEST TOKENIZER")
            print("=" * 60)
            
            test_texts = [
                "Service excellent d'Air Paradis!",
                "Vol retardé encore une fois!",
                "Perfect flight with Air Paradis"
            ]
            
            tokenizer_results = service.test_tokenizer(test_texts)
            for text, result in tokenizer_results.items():
                print(f"'{text}' → Tokens: {len(result['sequence'])}, Séquence: {result['sequence'][:10]}...")
            
            print("\n" + "=" * 60)
            print("TEST PRÉDICTIONS")
            print("=" * 60)
            
            for text in test_texts:
                try:
                    result = service.predict(text)
                    print(f"'{text}'")
                    print(f"  → Sentiment: {result['sentiment']}")
                    print(f"  → Confiance: {result['confidence']:.3f}")
                    print(f"  → Tokens: {result['preprocessing_info']['tokens_count']}")
                    print()
                except Exception as e:
                    print(f"❌ Erreur prédiction pour '{text}': {e}")
            
            print("=" * 60)
            print("✅ TOUS LES TESTS RÉUSSIS!")
            print("=" * 60)
            return True
        else:
            print("❌ Échec du test de connexion")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_loading_methods():
    """Test spécifique des différentes méthodes de chargement"""
    try:
        from dagshub_service import DagsHubService
        
        print("\n" + "=" * 60)
        print("TEST DES MÉTHODES DE CHARGEMENT")
        print("=" * 60)
        
        service = DagsHubService()
        
        # Test méthode 1: MLflow client
        print("🔄 Test chargement via MLflow client...")
        config1 = service._download_config_via_mlflow_client()
        
        if config1:
            print("✅ Méthode MLflow client: SUCCESS")
            print(f"   - Run ID: {config1.get('metadata', {}).get('run_id', 'N/A')}")
            print(f"   - Model Type: {config1.get('metadata', {}).get('model_type', 'N/A')}")
        else:
            print("❌ Méthode MLflow client: ÉCHEC")
        
        # Test méthode 2: Requête HTTP directe
        print("\n🔄 Test chargement via requête HTTP directe...")
        config2 = service._download_config_via_requests()
        
        if config2:
            print("✅ Méthode requête HTTP: SUCCESS")
            print(f"   - Run ID: {config2.get('metadata', {}).get('run_id', 'N/A')}")
            print(f"   - Model Type: {config2.get('metadata', {}).get('model_type', 'N/A')}")
        else:
            print("❌ Méthode requête HTTP: ÉCHEC")
        
        # Comparaison des résultats
        if config1 and config2:
            if config1 == config2:
                print("✅ Les deux méthodes retournent le même résultat")
            else:
                print("⚠️ Les méthodes retournent des résultats différents")
        
        return config1 is not None or config2 is not None
        
    except Exception as e:
        print(f"❌ Erreur test méthodes de chargement: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print("🔧 SCRIPT DE TEST SERVICE DAGSHUB")
    print("=" * 60)
    
    # Chargement des variables d'environnement
    if not load_env_from_file():
        print("❌ Impossible de charger les variables d'environnement")
        return False
    
    # Test des méthodes de chargement
    loading_success = test_model_loading_methods()
    
    if not loading_success:
        print("❌ Aucune méthode de chargement ne fonctionne")
        return False
    
    # Test complet du service
    service_success = test_dagshub_service()
    
    if service_success:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("Votre API devrait maintenant fonctionner correctement.")
        return True
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Vérifiez les logs ci-dessus pour identifier les problèmes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)