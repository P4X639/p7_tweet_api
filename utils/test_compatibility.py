# Script de test de compatibilité des versions (corrigé)
import os
import sys
import json
import logging
from pathlib import Path

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_env_from_file():
    """Charge les variables d'environnement depuis le fichier .env"""
    # Recherche du fichier .env dans plusieurs emplacements
    possible_locations = [
        Path(__file__).parent / ".env",           # Dans le dossier du script
        Path(__file__).parent.parent / ".env",   # Dans le dossier parent
        Path("/app/.env"),                       # Chemin absolu Docker
        Path.cwd() / ".env"                      # Répertoire de travail actuel
    ]
    
    env_file = None
    for location in possible_locations:
        if location.exists():
            env_file = location
            logger.info(f"Fichier .env trouvé: {location}")
            break
    
    if not env_file:
        logger.error("Fichier .env non trouvé dans les emplacements suivants:")
        for location in possible_locations:
            logger.error(f"  - {location}")
        return False
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    logger.debug(f"Variable chargée: {key}")
                    
        logger.info("Variables d'environnement chargées avec succès")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier .env: {e}")
        return False

def check_environment_variables():
    """Vérifie que les variables d'environnement nécessaires sont présentes"""
    required_vars = ["DAGSHUB_USERNAME", "DAGSHUB_REPO", "DAGSHUB_TOKEN", "MODEL_RUN_ID"]
    
    print("\n" + "=" * 60)
    print("VÉRIFICATION VARIABLES D'ENVIRONNEMENT")
    print("=" * 60)
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Masquer le token pour la sécurité
            if var == "DAGSHUB_TOKEN":
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NON DÉFINI")
            all_present = False
    
    return all_present

def check_tensorflow_compatibility():
    """Vérifie la compatibilité TensorFlow"""
    try:
        import tensorflow as tf
        
        print("\n" + "=" * 60)
        print("ANALYSE TENSORFLOW")
        print("=" * 60)
        
        current_tf_version = tf.__version__
        print(f"Version TensorFlow actuelle: {current_tf_version}")
        
        # Recherche du fichier JSON dans plusieurs emplacements
        possible_json_locations = [
            Path(__file__).parent / "model_config.json",
            Path(__file__).parent.parent / "model_config.json",
            Path("/app/model_config.json"),
            Path.cwd() / "model_config.json"
        ]
        
        json_file = None
        for location in possible_json_locations:
            if location.exists():
                json_file = location
                print(f"Fichier model_config.json trouvé: {location}")
                break
        
        if json_file:
            with open(json_file, 'r') as f:
                config = json.load(f)
            
            model_tf_version = config.get("environment", {}).get("tensorflow_version", "unknown")
            print(f"Version TensorFlow du modèle: {model_tf_version}")
            
            if model_tf_version != "unknown":
                def parse_version(v):
                    try:
                        return tuple(map(int, v.split('.')[:3]))
                    except:
                        return (0, 0, 0)
                
                current_v = parse_version(current_tf_version)
                model_v = parse_version(model_tf_version)
                
                print(f"\nAnalyse de compatibilité:")
                print(f"Version modèle parsée: {model_v}")
                print(f"Version actuelle parsée: {current_v}")
                
                if current_v == model_v:
                    print("✅ Versions identiques - Compatibilité parfaite")
                    return True
                elif current_v > model_v:
                    major_diff = current_v[0] - model_v[0]
                    minor_diff = current_v[1] - model_v[1]
                    
                    if major_diff > 0:
                        print("❌ Version actuelle plus récente (différence majeure)")
                        print("   Risque: Incompatibilité de format de modèle")
                        print("   Solution: Mettre à jour requirements.txt vers tensorflow-cpu>=2.17.0")
                        return False
                    elif minor_diff > 2:
                        print("⚠️ Version actuelle plus récente (différence mineure)")
                        print("   Risque: Problèmes de désérialisation possibles")
                        return True
                    else:
                        print("✅ Version actuelle légèrement plus récente - Compatible")
                        return True
                else:
                    major_diff = model_v[0] - current_v[0]
                    minor_diff = model_v[1] - current_v[1]
                    
                    if major_diff > 0:
                        print("❌ Version actuelle plus ancienne (différence majeure)")
                        print("   Problème: Format de modèle non supporté")
                        print("   Solution: Mettre à jour requirements.txt vers tensorflow-cpu>=2.17.0")
                        return False
                    else:
                        print("⚠️ Version actuelle plus ancienne")
                        print("   Recommandation: Mettre à jour TensorFlow")
                        return True
        else:
            print("⚠️ Fichier model_config.json non trouvé")
            print("Emplacements cherchés:")
            for location in possible_json_locations:
                print(f"  - {location}")
            return True
        
    except ImportError as e:
        print(f"❌ TensorFlow non installé: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse TensorFlow: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_loading_simulation():
    """Simule le chargement du modèle pour identifier les erreurs"""
    try:
        import tensorflow as tf
        import tempfile
        
        print("\n" + "=" * 60)
        print("SIMULATION CHARGEMENT MODÈLE")
        print("=" * 60)
        
        # Test de création d'un modèle simple
        print("🔄 Test de création d'un modèle simple...")
        test_model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(100,)),
            tf.keras.layers.Embedding(1000, 64),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        print("✅ Modèle de test créé avec succès")
        
        # Test de sauvegarde/chargement
        with tempfile.NamedTemporaryFile(suffix='.keras', delete=False) as tmp_file:
            test_model.save(tmp_file.name)
            print("✅ Sauvegarde de test réussie")
            
            # Test de chargement
            loaded_model = tf.keras.models.load_model(tmp_file.name, compile=False)
            print("✅ Chargement de test réussi")
            
            # Nettoyage
            try:
                os.unlink(tmp_file.name)
            except:
                pass
        
        print("\n💡 Conclusion: TensorFlow fonctionne correctement")
        print("   Le problème vient probablement de l'incompatibilité de versions")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans la simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dagshub_service():
    """Test du service DagsHub avec analyse détaillée"""
    try:
        # Ajout du path pour les services
        services_paths = [
            str(Path(__file__).parent / "services"),
            str(Path(__file__).parent.parent / "services"),
            str(Path("/app/services")),
            str(Path.cwd() / "services")
        ]
        
        for path in services_paths:
            if Path(path).exists():
                sys.path.insert(0, path)
                print(f"Services path ajouté: {path}")
                break
        
        try:
            from dagshub_service import DagsHubService
        except ImportError as e:
            print(f"❌ Impossible d'importer DagsHubService: {e}")
            print("Chemins vérifiés:")
            for path in services_paths:
                exists = Path(path).exists()
                print(f"  - {path}: {'✅' if exists else '❌'}")
            return False
        
        print("\n" + "=" * 60)
        print("TEST SERVICE DAGSHUB AVEC ANALYSE VERSIONS")
        print("=" * 60)
        
        service = DagsHubService()
        
        # Test du chargement de configuration
        print("\n🔄 Test de chargement de configuration...")
        config_success = service.load_model_config()
        
        if config_success:
            print("✅ Configuration chargée avec succès")
            print("\nAnalyse de compatibilité:")
            
            if service.version_compatibility:
                status = service.version_compatibility["overall_status"]
                print(f"Status global: {status}")
                
                if service.version_compatibility["critical_issues"]:
                    print("\nProblèmes critiques:")
                    for issue in service.version_compatibility["critical_issues"]:
                        print(f"  ❌ {issue}")
                
                if service.version_compatibility["warnings"]:
                    print("\nAvertissements:")
                    for warning in service.version_compatibility["warnings"]:
                        print(f"  ⚠️ {warning}")
                
                # Recommandations spécifiques
                if status == "INCOMPATIBLE":
                    print("\n💡 RECOMMANDATIONS:")
                    print("   1. Mettez à jour votre requirements.txt:")
                    print("      tensorflow-cpu==2.17.0")
                    print("   2. Rebuild votre container:")
                    print("      docker-compose build --no-cache")
                    print("   3. Redémarrez:")
                    print("      docker-compose up")
        else:
            print("❌ Échec du chargement de configuration")
            return False
        
        # Test du chargement complet
        print("\n🔄 Test de chargement complet...")
        success = service.test_connection()
        
        return success
        
    except Exception as e:
        print(f"❌ Erreur test service: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test complet de compatibilité"""
    print("🔧 DIAGNOSTIC DE COMPATIBILITÉ TENSORFLOW")
    print("=" * 60)
    print(f"Répertoire de travail: {Path.cwd()}")
    print(f"Script exécuté depuis: {Path(__file__).parent}")
    
    # Chargement des variables d'environnement
    if not load_env_from_file():
        print("❌ Impossible de charger les variables d'environnement")
        return False
    
    # Vérification des variables d'environnement
    if not check_environment_variables():
        print("❌ Variables d'environnement manquantes")
        return False
    
    # Tests de compatibilité
    tests = [
        ("TensorFlow", check_tensorflow_compatibility),
        ("Simulation modèle", test_model_loading_simulation),
        ("Service DagsHub", test_dagshub_service)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n🔄 Exécution du test: {test_name}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Erreur dans le test {test_name}: {e}")
            results[test_name] = False
    
    # Résumé final
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ RÉUSSI" if passed else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("Votre configuration devrait fonctionner.")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("\nACTIONS RECOMMANDÉES:")
        print("1. Mettre à jour requirements.txt:")
        print("   tensorflow-cpu==2.17.0")
        print("   tensorboard==2.17.0")
        print("2. Rebuild le container:")
        print("   docker-compose build --no-cache")
        print("3. Redémarrer:")
        print("   docker-compose up")
        print("4. Vérifier les logs détaillés ci-dessus")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)