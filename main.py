# API FastAPI avec démarrage optimisé et non-dupliqué
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
import uvicorn
import sys
from pathlib import Path

# Configuration des logs AVANT tout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de logging pour ignorer les 404 suspects
logging.getLogger("uvicorn.access").addFilter(
    lambda record: not any(pattern in record.getMessage() 
                          for pattern in ["/cgi/", "/boaform/", "loginMsg.js"])
)
# Suppression du warning - Le serveur de développement (Werkzeug/uvicorn en mode dev)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# Ajouter au début du main.py, après les imports
from dotenv import load_dotenv

# Charger explicitement le fichier .env
load_dotenv('/app/.env')  # Chemin absolu dans le container


# Import des services
from services.dagshub_service import DagsHubService
from services.dash_ui_service import DashUIService

# Variable pour éviter la duplication d'affichage
_startup_displayed = False

def display_simple_startup_info():
    """Affichage simplifié pour éviter la duplication"""
    global _startup_displayed
    
    # Éviter la duplication lors du reload
    if _startup_displayed:
        print("[!] Redémarrage de l'API (reload)...")
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
    
    if not token:
        print("[X] DAGSHUB_TOKEN: NON DÉFINI")
    
    # URLs des services
    api_port = os.getenv("API_PORT", "8000")
    print(f"\nSERVICES:")
    print(f"API: http://localhost:{api_port}")
    print(f"Interface: http://localhost:8050")
    print(f"Admin: http://localhost:8050/admin")
    
    print("=" * 60)
    
    # Vérifier si toutes les variables critiques sont présentes
    return all([model_run_id, username, repo, token])

# Initialisation de l'API
app = FastAPI(
    title="P7 Tweet Sentiment Analysis API",
    description="API de prédiction de sentiment pour tweets avec modèles DagsHub/MLflow",
    version="1.0.0"
)

# Services globaux
dagshub_service = None
dash_ui_service = None

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage optimisée"""
    global dagshub_service, dash_ui_service
    
    try:
        # Affichage des informations (non dupliqué)
        config_ok = display_simple_startup_info()
        
        if not config_ok:
            print("[!] ATTENTION: Configuration incomplète!")
            print("   Vérifiez votre fichier .env")
        
        print("\nINITIALISATION:")
        
        # 1. Service DagsHub
        print("Chargement du service DagsHub...")
        dagshub_service = DagsHubService()
        
        print("Test de connexion...")
        model_loaded = dagshub_service.test_connection()
        
        if model_loaded:
            print("[✓] Modèle chargé avec succès")
            
            # Vérification du statut de configuration
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
        
        # 2. Interface Dash
        print("Démarrage de l'interface Dash...")
        dash_ui_service = DashUIService(api_base_url="http://localhost:8000")
        
        # Démarrage en arrière-plan
        dash_ui_service.run_in_thread(host='0.0.0.0', port=8050, debug=False)
        print("[✓] Interface Dash démarrée")
        
        # Résumé final
        print("\nSTATUT FINAL:")
        print(f"   Modèle: {'[✓] Chargé' if model_loaded else '[X] Échec'}")
        
        if dagshub_service:
            config_status = dagshub_service.get_config_status()
            status = config_status.get("status", "unknown")
            config_icon = "[✓]" if status == "success" else "[-]" if status == "loading" else "[!]"
            print(f"   Configuration: {config_icon} {status}")
        
        print("\nAPI prête!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"[X] Erreur initialisation: {e}")
        print(f"[X] ERREUR: {e}")
        print("=" * 60)
        # Ne pas faire raise pour éviter de casser le démarrage

# Modèles Pydantic pour la validation des données
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

class RootResponse(BaseModel):
    message: str
    status: str
    version: str
    docs: str
    dash_ui: str
    model_loaded: bool
    config_status: Dict[str, Any]

# Endpoints principaux
@app.get("/", response_model=RootResponse)
async def root():
    """Endpoint racine - informations générales de l'API"""
    model_loaded = False
    config_status = {"status": "unknown"}
    
    try:
        if dagshub_service:
            model_loaded = dagshub_service.model is not None
            config_status = dagshub_service.get_config_status()
    except:
        pass
        
    return RootResponse(
        message="P7 Tweet Sentiment Analysis API",
        status="running",
        version="1.0.0",
        docs="/docs",
        dash_ui="http://localhost:8050",
        model_loaded=model_loaded,
        config_status=config_status
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check de l'API - statut complet des services"""
    if not dagshub_service:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    
    try:
        # Utiliser la méthode health_check() du service DagsHub
        health_data = dagshub_service.health_check()
        config_status = health_data.get("config_status", {})
        
        model_loaded = health_data.get("model_loaded", False)
        config_loaded = health_data.get("config_loaded", False)
        
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
        
        # Retourner toutes les données de health_check()
        return HealthResponse(
            status=status,
            message=message,
            model_loaded=model_loaded,
            config_loaded=config_loaded,
            config_status=config_status,
            # Données additionnelles pour l'interface d'administration
            tokenizer_loaded=health_data.get("tokenizer_loaded", False),
            vocab_size=health_data.get("vocab_size", None),
            input_shape=health_data.get("input_shape", None),
            version_compatibility=health_data.get("version_compatibility", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur health check: {str(e)}")

@app.post("/predict", response_model=PredictResponse)
async def predict_sentiment(request: PredictRequest):
    """Prédiction de sentiment pour un texte donné"""
    if not dagshub_service or not dagshub_service.model:
        raise HTTPException(status_code=503, detail="Modèle non disponible")
    
    try:
        result = dagshub_service.predict(request.text)
        
        return PredictResponse(
            text=result["text"],
            processed_text=result["processed_text"],
            sentiment=result["sentiment"],
            confidence=result["confidence"],
            model_info=result["model_info"],
            user_id=request.user_id,
            preprocessing_info=result.get("preprocessing_info"),
            config_status=result.get("config_status")
        )
        
    except Exception as e:
        logger.error(f"Erreur prédiction: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/model/info")
async def get_model_info():
    """Informations détaillées du modèle et métadonnées"""
    if not dagshub_service:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    
    try:
        return {
            "model_info": dagshub_service.model_info,
            "metadata": dagshub_service.get_model_metadata(),
            "model_loaded": dagshub_service.model is not None,
            "config_status": dagshub_service.get_config_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/debug/config", include_in_schema=False)
async def get_debug_config():
    """Configuration de debug - informations internes"""
    if not dagshub_service:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    
    return {
        "config_loaded": dagshub_service.model_config is not None,
        "config_status": dagshub_service.get_config_status(),
        "config_data": dagshub_service.model_config,
        "run_id": dagshub_service.model_run_id,
        "model_info": dagshub_service.model_info
    }

@app.post("/admin/reload-config", include_in_schema=False)
async def reload_config():
    """Relance le chargement de configuration"""
    if not dagshub_service:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    
    try:
        success = dagshub_service.retry_config_loading()
        config_status = dagshub_service.get_config_status()
        
        return {
            "success": success,
            "message": "Configuration rechargée" if success else "Échec du rechargement",
            "config_status": config_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/debug/tokenizer", include_in_schema=False)
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
                "sequences": sequences[0][:10] if sequences[0] else []  # Premiers 10 tokens
            })
        
        return {
            "tokenizer_status": "loaded",
            "vocab_size": len(dagshub_service.tokenizer.word_index),
            "oov_token": dagshub_service.tokenizer.oov_token,
            "test_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur test tokenizer: {str(e)}")
        
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
