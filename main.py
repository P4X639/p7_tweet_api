# Main.py avec Azure Insights fonctionnel - SANS régressions sur les autres services
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
import uvicorn
import sys
from pathlib import Path
import threading

# Configuration des logs - Azure a besoin d'INFO
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Filtres pour réduire le bruit
logging.getLogger("uvicorn.access").addFilter(
    lambda record: not any(pattern in record.getMessage() 
                          for pattern in ["/cgi/", "/boaform/", "loginMsg.js"])
)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv('/app/.env')

# Import des services (GARDER LES ORIGINAUX)
from services.dagshub_service import DagsHubService
from services.dash_ui_service import DashUIService
from services.azure_insights_service import AzureInsightsService

# Variables pour éviter la duplication
_startup_displayed = False

# Services globaux - IMPORTANT : azure_insights_service DOIT être global
dagshub_service = None
dash_ui_service = None
azure_insights_service = None

def display_simple_startup_info():
    """Affichage simplifiÃ© pour Ã©viter la duplication"""
    global _startup_displayed
    
    if _startup_displayed:
        print("[!] RedÃ©marrage de l'API (reload)...")
        return True
    
    _startup_displayed = True
    
    print("=" * 60)
    print("P7 Tweet Sentiment Analysis API")
    print("=" * 60)
    
    # Variables critiques
    model_run_id = os.getenv("MODEL_RUN_ID")
    username = os.getenv("DAGSHUB_USERNAME")
    repo = os.getenv("DAGSHUB_REPO")
    token = os.getenv("DAGSHUB_TOKEN")
    
    # Vérification Azure
    az_connection = os.getenv("AZ_CONNECTION_STRING")
    az_key = os.getenv("AZ_INSTRUMENTATION_KEY")
    
    print("CONFIGURATION:")
    if model_run_id:
        print(f"[✓] MODEL_RUN_ID: {model_run_id}")
    else:
        print("[X] MODEL_RUN_ID: NON DÉFINI")
    
    if username and repo:
        print(f"[✓] DagsHub: {username}/{repo}")
        if model_run_id:
            exp_url = f"https://dagshub.com/{username}/{repo}/experiments/3/runs/{model_run_id}"
            print(f"Expérience: {exp_url}")
    else:
        print("[X] DagsHub: Configuration incomplète")
    
    # Statut Azure
    if az_connection or az_key:
        print(f"[✓] Azure Insights: Configuré")
    else:
        print("[!] Azure Insights: Non configuré (optionnel)")
    
    if not token:
        print("[X] DAGSHUB_TOKEN: NON DÉFINI")
    
    # URLs des services
    api_port = os.getenv("API_PORT", "8000")
    print(f"\nSERVICES:")
    print(f"API: http://localhost:{api_port}")
    print(f"Interface: http://localhost:8050")
    print(f"Admin: http://localhost:8050/admin")
    
    print("=" * 60)
    
    return all([model_run_id, username, repo, token])

# Initialisation de l'API
app = FastAPI(
    title="P7 Tweet Sentiment Analysis API",
    description="API de prédiction de sentiment pour tweets avec Azure Insights",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage avec Azure Insights"""
    global dagshub_service, dash_ui_service, azure_insights_service
    
    try:
        # Affichage des informations (non dupliqué)
        config_ok = display_simple_startup_info()
        
        if not config_ok:
            print("[!] ATTENTION: Configuration incomplète!")
            print("   Vérifiez votre fichier .env")
        
        print("\nINITIALISATION:")
        
        # 1. Service Azure Insights (PRIORITÉ pour le logging)
        print("1. Initialisation Azure Application Insights...")
        azure_insights_service = AzureInsightsService()
        insights_status = azure_insights_service.get_service_status()
        
        if insights_status['enabled']:
            print("[✓] Azure Insights configuré")
            print(f"    - Connection String: {'✓' if insights_status.get('connection_string_configured') else 'X'}")
            print(f"    - Instrumentation Key: {'✓' if insights_status.get('instrumentation_key_configured') else 'X'}")
            
            # Test de connexion
            test_result = azure_insights_service.force_send_test_log()
            if test_result.get('success'):
                print("    [✓] Test de connexion Azure réussi")
            else:
                print(f"    [!] Test Azure: {test_result.get('error')}")
        else:
            print("[!] Azure Insights non configuré (mode dégradé)")
        
        # 2. Service DagsHub (GARDER LE SERVICE ORIGINAL)
        print("2. Chargement du service DagsHub...")
        dagshub_service = DagsHubService()
        
        print("3. Test de connexion...")
        model_loaded = dagshub_service.test_connection()
        
        if model_loaded:
            print("[✓] Modèle chargé avec succès")
            
            # Vérification du statut de configuration (si disponible)
            if hasattr(dagshub_service, 'get_config_status'):
                config_status = dagshub_service.get_config_status()
                status = config_status.get("status", "unknown")
                
                if status == "success":
                    print("[✓] Configuration chargée")
                elif status == "loading":
                    print("[-] Configuration en cours de chargement...")
                elif status == "failed":
                    error = config_status.get("error", "Erreur inconnue")
                    print(f"[!] Configuration échouée: {error}")
                    print("   Fonctionnement avec paramètres par défaut")
                else:
                    print(f"Configuration: {status}")
        else:
            print("[X] Échec du chargement du modèle")
        
        # 3. Interface Dash (passer le service Azure Insights)
        print("4. Démarrage de l'interface Dash...")
        dash_ui_service = DashUIService(
            api_base_url="http://localhost:8000",
            azure_insights_service=azure_insights_service
        )
        
        # Démarrage en arrière-plan
        dash_ui_service.run_in_thread(host='0.0.0.0', port=8050, debug=False)
        print("[✓] Interface Dash démarrée")
        
        # Résumé final avec Azure
        print("\nSTATUT FINAL:")
        print(f"   Modèle: {'[✓] Chargé' if model_loaded else '[X] Échec'}")
        print(f"   Azure Insights: {'[✓] Opérationnel' if insights_status['enabled'] else '[!] Désactivé'}")
        
        if dagshub_service and hasattr(dagshub_service, 'get_config_status'):
            config_status = dagshub_service.get_config_status()
            status = config_status.get("status", "unknown")
            config_icon = "[✓]" if status == "success" else "[-]" if status == "loading" else "[!]"
            print(f"   Configuration: {config_icon} {status}")
        
        # Log startup dans Azure si disponible
        if azure_insights_service and azure_insights_service.enabled:
            startup_data = {
                'event_type': 'api_startup',
                'model_loaded': model_loaded,
                'config_complete': config_ok,
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()
            }
            azure_insights_service.azure_logger.info(
                'API Startup Complete',
                extra={'custom_dimensions': startup_data}
            )
            print("\n[AZURE] Événement de démarrage loggé")
        
        print("\nAPI prête!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"[X] Erreur initialisation: {e}")
        print(f"[X] ERREUR: {e}")
        print("=" * 60)

# Modèles Pydantic
class PredictRequest(BaseModel):
    text: str
    user_id: Optional[str] = "anonymous"

class PredictResponse(BaseModel):
    text: str
    processed_text: str
    sentiment: str
    confidence: float
    model_info: Dict[str, Any]
    user_id: str
    azure_logged: bool = False
    preprocessing_info: Optional[Dict[str, Any]] = None
    config_status: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    model_loaded: bool
    config_loaded: bool
    config_status: Dict[str, Any]
    tokenizer_loaded: Optional[bool] = None
    vocab_size: Optional[int] = None
    input_shape: Optional[str] = None
    version_compatibility: Optional[Dict[str, Any]] = None
    azure_insights: Optional[Dict[str, Any]] = None

class RootResponse(BaseModel):
    message: str
    status: str
    version: str
    docs: str
    dash_ui: str
    model_loaded: bool
    config_status: Dict[str, Any]
    azure_insights: str

# Endpoints principaux
@app.get("/", response_model=RootResponse)
async def root():
    """Endpoint racine - informations générales de l'API"""
    model_loaded = False
    config_status = {"status": "unknown"}
    azure_status = "unknown"
    
    try:
        if dagshub_service:
            model_loaded = dagshub_service.model is not None
            if hasattr(dagshub_service, 'get_config_status'):
                config_status = dagshub_service.get_config_status()
        
        if azure_insights_service:
            azure_status = "enabled" if azure_insights_service.enabled else "disabled"
    except:
        pass
        
    return RootResponse(
        message="P7 Tweet Sentiment Analysis API",
        status="running",
        version="1.0.0",
        docs="/docs",
        dash_ui="http://localhost:8050",
        model_loaded=model_loaded,
        config_status=config_status,
        azure_insights=azure_status
    )

@app.get("/healthcheck", include_in_schema=True)
async def healthcheck():
    """Endpoint simple pour tests CI/CD - indépendant du service API"""
    return {"status": "ok", "service": "p7-tweet-api"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check de l'API - statut complet des services"""
    if not dagshub_service:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    
    try:
        # Utiliser la méthode health_check() du service DagsHub (si disponible)
        if hasattr(dagshub_service, 'health_check'):
            health_data = dagshub_service.health_check()
            config_status = health_data.get("config_status", {})
        else:
            # Fallback pour compatibilité
            health_data = {
                "model_loaded": dagshub_service.model is not None,
                "tokenizer_loaded": dagshub_service.tokenizer is not None,
                "config_loaded": False,
                "config_status": {"status": "unknown"}
            }
            config_status = health_data["config_status"]
        
        model_loaded = health_data.get("model_loaded", False)
        config_loaded = health_data.get("config_loaded", False)
        
        # Statut Azure
        azure_status = {}
        if azure_insights_service:
            azure_status = azure_insights_service.get_service_status()
        
        # Déterminer le statut global
        if not model_loaded:
            status = "critical"
            message = "Modèle non chargé"
        elif config_status.get("status") == "failed":
            status = "degraded"
            message = "Modèle chargé, configuration échouée"
        elif config_status.get("status") == "loading":
            status = "partial"
            message = "Configuration en cours de chargement"
        elif config_loaded:
            status = "healthy"
            message = "API complètement opérationnelle"
        else:
            status = "functional"
            message = "API opérationnelle (configuration par défaut)"
        
        return HealthResponse(
            status=status,
            message=message,
            model_loaded=model_loaded,
            config_loaded=config_loaded,
            config_status=config_status,
            tokenizer_loaded=health_data.get("tokenizer_loaded", False),
            vocab_size=health_data.get("vocab_size", None),
            input_shape=health_data.get("input_shape", None),
            version_compatibility=health_data.get("version_compatibility", {}),
            azure_insights=azure_status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur health check: {str(e)}")

@app.post("/predict", response_model=PredictResponse)
async def predict_sentiment(request: PredictRequest):
    """Prédiction de sentiment avec logging Azure GARANTI"""
    if not dagshub_service or not dagshub_service.model:
        raise HTTPException(status_code=503, detail="Modèle non disponible")
    
    try:
        result = dagshub_service.predict(request.text)
        azure_logged = False
        
        # CRITIQUE : Log dans Azure Insights - TOUJOURS essayer
        if azure_insights_service:
            try:
                prediction_data = {
                    'text': request.text,
                    'sentiment': result['sentiment'],
                    'confidence': result['confidence'],
                    'model_info': result.get('model_info', {}),
                    'user_id': request.user_id,
                    'prediction_timestamp': __import__('datetime').datetime.utcnow().isoformat()
                }
                
                # Appel explicite de log_prediction
                azure_logged = azure_insights_service.log_prediction(prediction_data)
                
                if azure_logged:
                    logger.info(f"[AZURE] Prédiction loggée pour user {request.user_id}")
                else:
                    logger.warning(f"[AZURE] Échec du logging pour user {request.user_id}")
                    
            except Exception as azure_error:
                logger.error(f"[AZURE] Erreur logging prédiction: {azure_error}")
        else:
            logger.warning("[AZURE] Service Azure non disponible")
        
        return PredictResponse(
            text=result["text"],
            processed_text=result.get("processed_text", ""),
            sentiment=result["sentiment"],
            confidence=result["confidence"],
            model_info=result.get("model_info", {}),
            user_id=request.user_id,
            azure_logged=azure_logged,
            preprocessing_info=result.get("preprocessing_info"),
            config_status=result.get("config_status")
        )
        
    except Exception as e:
        logger.error(f"Erreur prédiction: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/feedback", include_in_schema=True)
async def log_feedback(feedback_data: dict):
    """Enregistrer un feedback utilisateur avec logging Azure GARANTI"""
    try:
        logger.info(f"Réception feedback: {feedback_data.get('feedback_type')} pour prédiction {feedback_data.get('prediction_id')}")
        
        azure_logged = False
        
        # CRITIQUE : Log dans Azure Insights - TOUJOURS essayer
        if azure_insights_service:
            try:
                # Enrichir les données de feedback
                feedback_dict = feedback_data.copy()
                feedback_dict['feedback_timestamp'] = __import__('datetime').datetime.utcnow().isoformat()
                
                # Appel explicite de log_feedback
                azure_logged = azure_insights_service.log_feedback(feedback_dict)
                
                if azure_logged:
                    logger.info(f"[AZURE] Feedback loggé: {feedback_data.get('feedback_type')} pour {feedback_data.get('prediction_id')}")
                else:
                    logger.warning(f"[AZURE] Échec du logging feedback: {feedback_data.get('prediction_id')}")
                    
            except Exception as azure_error:
                logger.error(f"[AZURE] Erreur logging feedback: {azure_error}")
        else:
            logger.warning("[AZURE] Service Azure non disponible pour feedback")
        
        return {
            "success": True,
            "message": "Feedback enregistré",
            "azure_logged": azure_logged,
            "feedback_type": feedback_data.get('feedback_type'),
            "prediction_id": feedback_data.get('prediction_id')
        }
        
    except Exception as e:
        logger.error(f"Erreur enregistrement feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/model/info")
async def get_model_info():
    """Informations détaillées du modèle et métadonnées"""
    if not dagshub_service:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    
    try:
        result = {
            "model_info": getattr(dagshub_service, 'model_info', {}),
            "model_loaded": dagshub_service.model is not None,
            "config_status": getattr(dagshub_service, 'get_config_status', lambda: {"status": "unknown"})()
        }
        
        # Ajouter métadonnées si disponibles
        if hasattr(dagshub_service, 'get_model_metadata'):
            result["metadata"] = dagshub_service.get_model_metadata()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/debug/config", include_in_schema=True)
async def get_debug_config():
    """Configuration de debug - informations internes"""
    if not dagshub_service:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    
    result = {
        "model_loaded": dagshub_service.model is not None,
        "tokenizer_loaded": dagshub_service.tokenizer is not None,
        "run_id": getattr(dagshub_service, 'model_run_id', 'unknown'),
        "model_info": getattr(dagshub_service, 'model_info', {})
    }
    
    # Ajouter config si disponible
    if hasattr(dagshub_service, 'model_config'):
        result["config_loaded"] = dagshub_service.model_config is not None
        result["config_data"] = getattr(dagshub_service, 'model_config', None)
    
    if hasattr(dagshub_service, 'get_config_status'):
        result["config_status"] = dagshub_service.get_config_status()
    
    return result

@app.get("/debug/azure-status", include_in_schema=True)
async def get_azure_debug_status():
    """Statut debug Azure via GET"""
    if not azure_insights_service:
        return {"error": "Service Azure non initialisé"}
    
    return {
        "service_status": azure_insights_service.get_service_status(),
        "environment_check": {
            'connection_string_configured': bool(os.getenv("AZ_CONNECTION_STRING")),
            'instrumentation_key_configured': bool(os.getenv("AZ_INSTRUMENTATION_KEY")),
        },
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }

@app.get("/debug/tokenizer", include_in_schema=True)
async def test_tokenizer():
    """Test du tokenizer avec exemples de textes"""
    if not dagshub_service or not dagshub_service.tokenizer:
        raise HTTPException(status_code=503, detail="Tokenizer non disponible")
    
    try:
        # Textes de test pour validation du tokenizer
        test_texts = [
            "Service excellent d'Air Paradis!",
            "Vol retardé encore une fois!",
            "Vol parfait, équipage professionnel"
        ]
        
        results = []
        for text in test_texts:
            sequences = dagshub_service.tokenizer.texts_to_sequences([text])
            tokens_count = len(sequences[0]) if sequences[0] else 0
            unknown_tokens = sum(1 for token in sequences[0] if token == 1) if sequences[0] else 0
            
            results.append({
                "text": text,
                "tokens_count": tokens_count,
                "unknown_tokens": unknown_tokens,
                "sequences": sequences[0][:10] if sequences[0] else []
            })
        
        return {
            "tokenizer_status": "loaded",
            "vocab_size": len(dagshub_service.tokenizer.word_index),
            "oov_token": getattr(dagshub_service.tokenizer, 'oov_token', None),
            "test_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur test tokenizer: {str(e)}")

@app.get("/admin/azure-insights", include_in_schema=True)
async def get_azure_insights_status():
    """Statut du service Azure Application Insights"""
    if not azure_insights_service:
        return {"error": "Service Azure Insights non initialisé"}
    
    return azure_insights_service.get_service_status()

@app.post("/debug/test-azure", include_in_schema=True)
async def test_azure_logging():
    """Test manuel complet d'Azure Insights"""
    if not azure_insights_service:
        return {"error": "Service Azure non initialisé"}
    
    results = {}
    
    # 1. Test de log basique
    try:
        basic_test = azure_insights_service.force_send_test_log()
        results['basic_test'] = basic_test
    except Exception as e:
        results['basic_test'] = {"error": str(e)}
    
    # 2. Test de prédiction
    try:
        test_prediction = {
            'text': 'Test Azure logging prediction via debug endpoint',
            'sentiment': 'positive',
            'confidence': 0.95,
            'user_id': 'debug_endpoint_user',
            'model_info': {'name': 'debug_test_model'}
        }
        pred_result = azure_insights_service.log_prediction(test_prediction)
        results['prediction_test'] = {"success": pred_result, "data_sent": test_prediction}
    except Exception as e:
        results['prediction_test'] = {"error": str(e)}
    
    # 3. Test de feedback
    try:
        test_feedback = {
            'feedback_type': 'correct',
            'prediction_id': 'debug_endpoint_123',
            'user_id': 'debug_endpoint_user',
            'original_sentiment': 'positive',
            'original_confidence': 0.95
        }
        feedback_result = azure_insights_service.log_feedback(test_feedback)
        results['feedback_test'] = {"success": feedback_result, "data_sent": test_feedback}
    except Exception as e:
        results['feedback_test'] = {"error": str(e)}
    
    # 4. Statut du service
    results['service_status'] = azure_insights_service.get_service_status()
    
    return {
        "test_timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        "azure_tests": results,
        "message": "Tests Azure exécutés - vérifiez les logs et Azure Portal dans 3-5 minutes"
    }


# Point d'entrée principal
if __name__ == "__main__":
    # Configuration depuis les variables d'environnement
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    environment = os.getenv("ENVIRONMENT", "production")
    
    # Mode reload uniquement en développement
    reload_mode = environment.lower() in ["development", "dev", "debug"]
    
    print(f"\nDémarrage sur {host}:{port}")
    if reload_mode:
        print("[!] Mode développement - Auto-reload activé")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        reload=reload_mode,
        log_level="info"
    )