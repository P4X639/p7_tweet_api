# Script pour debug le chargement de modèle
# À exécuter dans le container

from services.dagshub_service import DagsHubService

print("🔍 DEBUG CHARGEMENT MODÈLE")
print("=" * 40)

service = DagsHubService()

# Vérifier les variables d'environnement
print(f"MODEL_RUN_ID: {service.model_run_id}")
print(f"MODEL_ARTIFACT_PATH: {service.model_artifact_path}")

# Tenter le chargement
print("\n🔄 Test chargement modèle...")
result = service.load_model()

print(f"Résultat chargement: {result}")
print(f"Modèle chargé: {service.model is not None}")
print(f"Info modèle: {service.model_info}")

if service.model:
    print(f"Input shape: {service.model.input_shape}")
    print(f"Output shape: {service.model.output_shape}")
    print("Architecture:")
    service.model.summary()
else:
    print("❌ Aucun modèle chargé")

# Vérifier le tokenizer
print(f"\nTokenizer chargé: {service.tokenizer is not None}")
if service.tokenizer:
    print(f"Type tokenizer: {type(service.tokenizer)}")
else:
    print("❌ Aucun tokenizer chargé")