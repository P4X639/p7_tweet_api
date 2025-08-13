# Service DagsHub avec contrôle non-bloquant de la configuration
import os
import logging
import json
import pickle
import tempfile
import numpy as np
import time
import requests
from typing import Dict, Any, Union
import mlflow
from mlflow.tracking import MlflowClient
import pkg_resources
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)

class DagsHubService:
    """Service universel avec chargement non-bloquant de la configuration"""
    
    def __init__(self):
        # Configuration depuis les variables d'environnement
        self.username = os.getenv("DAGSHUB_USERNAME")
        self.repo = os.getenv("DAGSHUB_REPO") 
        self.token = os.getenv("DAGSHUB_TOKEN")
        self.model_run_id = os.getenv("MODEL_RUN_ID")
        
        self._setup_mlflow()
        
        # Variables du modèle TensorFlow et tokenizer
        self.model = None
        self.tokenizer = None
        self.model_config = None
        self.model_info = None
        self.model_type = "LSTM"
        self.version_compatibility = None
        
        # État de chargement de la configuration
        self.config_loading_status = "not_started"  # not_started, loading, success, failed
        self.config_loading_error = None
        self.config_load_attempts = 0
        self.max_config_attempts = 2
        
        # Configuration retry et timeouts
        self.max_retries = 3
        self.retry_delay = 5
        self.config_timeout = 30
        
    def _setup_mlflow(self):
        """Configuration MLflow pour connexion DagsHub"""
        os.environ["MLFLOW_TRACKING_USERNAME"] = self.username
        os.environ["MLFLOW_TRACKING_PASSWORD"] = self.token
        os.environ["DAGSHUB_NO_BROWSER"] = "true"
        
        mlflow_uri = f"https://dagshub.com/{self.username}/{self.repo}.mlflow"
        mlflow.set_tracking_uri(mlflow_uri)
        logger.info(f"[✓] MLflow configuré: {mlflow_uri}")
    
    def _get_current_environment_versions(self) -> dict:
        """Récupère les versions actuelles de l'environnement d'exécution"""
        import tensorflow as tf
        import numpy as np
        import pandas as pd
        
        # Récupération sécurisée des versions des packages
        try:
            sklearn_version = pkg_resources.get_distribution("scikit-learn").version
        except:
            sklearn_version = "unknown"
            
        try:
            mlflow_version = pkg_resources.get_distribution("mlflow").version
        except:
            mlflow_version = "unknown"
            
        try:
            fastapi_version = pkg_resources.get_distribution("fastapi").version
        except:
            fastapi_version = "unknown"
            
        return {
            "tensorflow_version": tf.__version__,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "scikit_learn_version": sklearn_version,
            "mlflow_version": mlflow_version,
            "fastapi_version": fastapi_version,
            "platform": "Docker Container"
        }
    
    def _check_config_file_exists(self) -> bool:
        """Vérifie rapidement si le fichier de configuration existe dans les artifacts"""
        try:
            client = MlflowClient()
            
            # Liste rapide des artifacts pour vérifier l'existence
            artifacts = client.list_artifacts(self.model_run_id)
            
            # Recherche du fichier model_config.json
            config_exists = any(
                artifact.path == "model_config.json" 
                for artifact in artifacts
            )
            
            if config_exists:
                logger.info("[✓] Fichier model_config.json détecté")
                return True
            else:
                logger.warning("[!] Fichier model_config.json non trouvé dans les artifacts")
                return False
                
        except Exception as e:
            logger.warning(f"[!] Impossible de vérifier l'existence du fichier de config: {e}")
            return False
    
    def _download_config_with_timeout(self) -> dict:
        """Télécharge la configuration avec timeout et méthodes de fallback"""
        def download_via_mlflow():
            """Méthode de téléchargement via client MLflow"""
            try:
                client = MlflowClient()
                with tempfile.TemporaryDirectory() as temp_dir:
                    config_path = client.download_artifacts(
                        self.model_run_id, 
                        'model_config.json', 
                        temp_dir
                    )
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception as e:
                raise Exception(f"MLflow download failed: {e}")
        
        def download_via_requests():
            """Méthode de téléchargement via requête HTTP directe"""
            try:
                config_url = f"https://dagshub.com/{self.username}/{self.repo}.mlflow/api/2.0/mlflow-artifacts/artifacts/{self.model_run_id}/model_config.json"
                headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Accept': 'application/json'
                }
                response = requests.get(config_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                raise Exception(f"HTTP download failed: {e}")
        
        # Tentative avec timeout sur les deux méthodes en parallèle
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_mlflow = executor.submit(download_via_mlflow)
            future_http = executor.submit(download_via_requests)
            
            try:
                # Attendre le premier qui réussit
                result = future_mlflow.result(timeout=self.config_timeout)
                logger.info("[✓] Configuration téléchargée via MLflow client")
                return result
            except (FutureTimeoutError, Exception) as e:
                logger.warning(f"[!] MLflow timeout/error: {e}")
                
                try:
                    result = future_http.result(timeout=10)
                    logger.info("[✓] Configuration téléchargée via HTTP")
                    return result
                except (FutureTimeoutError, Exception) as e2:
                    logger.error(f"[X] HTTP timeout/error: {e2}")
                    raise Exception(f"Both methods failed: MLflow({e}), HTTP({e2})")
    
    def _load_config_async(self):
        """Charge la configuration de manière asynchrone en arrière-plan"""
        def load_config_thread():
            self.config_loading_status = "loading"
            self.config_load_attempts += 1
            
            try:
                logger.info(f"Tentative {self.config_load_attempts}/{self.max_config_attempts} de chargement de la configuration...")
                
                # Vérification rapide de l'existence
                if not self._check_config_file_exists():
                    raise Exception("Fichier model_config.json non trouvé dans les artifacts")
                
                # Téléchargement avec timeout
                config_data = self._download_config_with_timeout()
                
                # Traitement réussi
                self.model_config = config_data
                self.config_loading_status = "success"
                self.config_loading_error = None
                
                # Analyse de compatibilité des versions
                model_environment = config_data.get("environment", {})
                current_environment = self._get_current_environment_versions()
                
                self.version_compatibility = self._analyze_version_compatibility(
                    model_environment, current_environment
                )
                
                # Extraction des informations du modèle
                self.model_info = self._extract_model_info(config_data)
                
                logger.info(f"[✓] Configuration chargée avec succès")
                logger.info(f"   - Modèle: {self.model_info['name']}")
                logger.info(f"   - Type: {self.model_info['type']}")
                logger.info(f"   - Compatibilité: {self.model_info['compatibility_status']}")
                
            except Exception as e:
                self.config_loading_status = "failed"
                self.config_loading_error = str(e)
                logger.error(f"[X] Échec du chargement de la configuration: {e}")
                
                # Créer des informations par défaut
                self._create_default_model_info()
        
        # Lancement du thread en arrière-plan
        thread = threading.Thread(target=load_config_thread, daemon=True)
        thread.start()
        return thread
    
    def _extract_model_info(self, config_data):
        """Extrait les informations du modèle depuis la configuration chargée"""
        return {
            "name": config_data.get("metadata", {}).get("model_name", "unknown"),
            "type": config_data.get("metadata", {}).get("model_type", "LSTM"),
            "version": config_data.get("metadata", {}).get("version", "1.0.0"),
            "run_id": config_data.get("metadata", {}).get("run_id", self.model_run_id),
            "accuracy": config_data.get("training", {}).get("test_accuracy", 0),
            "source": "dagshub_config",
            "preprocessing": config_data.get("preprocessing", {}).get("mode", "unknown"),
            "vocab_size": config_data.get("hyperparameters", {}).get("max_features", 10000),
            "max_length": config_data.get("hyperparameters", {}).get("max_len", 100),
            "model_tf_version": config_data.get("environment", {}).get("tensorflow_version", "unknown"),
            "current_tf_version": self._get_current_environment_versions().get("tensorflow_version", "unknown"),
            "compatibility_status": self.version_compatibility.get("overall_status", "unknown") if self.version_compatibility else "unknown"
        }
    
    def _create_default_model_info(self):
        """Crée des informations par défaut si la configuration n'est pas disponible"""
        current_env = self._get_current_environment_versions()
        
        self.model_info = {
            "name": "model_without_config",
            "type": "LSTM",
            "version": "unknown",
            "run_id": self.model_run_id,
            "accuracy": 0,
            "source": "default_fallback",
            "preprocessing": "none",
            "vocab_size": 10000,
            "max_length": 100,
            "model_tf_version": "unknown",
            "current_tf_version": current_env.get("tensorflow_version", "unknown"),
            "compatibility_status": "unknown"
        }
        
        self.version_compatibility = {
            "overall_status": "UNKNOWN",
            "critical_issues": ["Configuration non disponible"],
            "warnings": ["Utilisation des paramètres par défaut"],
            "details": {}
        }
    
    def _analyze_version_compatibility(self, model_env: dict, current_env: dict) -> dict:
        """Analyse la compatibilité des versions entre le modèle et l'environnement actuel"""
        def parse_version(version_str):
            """Parse une version string en tuple d'entiers"""
            try:
                return tuple(map(int, version_str.split('.')[:3]))
            except:
                return (0, 0, 0)
        
        def compare_versions(v1, v2):
            """Compare deux versions"""
            if v1 == v2:
                return "EXACT"
            elif v1 > v2:
                return "NEWER_CURRENT"
            else:
                return "OLDER_CURRENT"
        
        compatibility_analysis = {
            "overall_status": "COMPATIBLE",
            "critical_issues": [],
            "warnings": [],
            "details": {}
        }
        
        # Analyse TensorFlow (critique pour la compatibilité)
        model_tf = model_env.get("tensorflow_version", "unknown")
        current_tf = current_env.get("tensorflow_version", "unknown")
        
        if model_tf != "unknown" and current_tf != "unknown":
            model_v = parse_version(model_tf)
            current_v = parse_version(current_tf)
            status = compare_versions(current_v, model_v)
            
            compatibility_analysis["details"]["tensorflow"] = {
                "model_version": model_tf,
                "current_version": current_tf,
                "status": status,
                "compatible": True
            }
            
            major_diff = abs(model_v[0] - current_v[0])
            minor_diff = abs(model_v[1] - current_v[1])
            
            if major_diff > 0:
                compatibility_analysis["critical_issues"].append(
                    f"TensorFlow major version mismatch: model={model_tf}, current={current_tf}"
                )
                compatibility_analysis["overall_status"] = "INCOMPATIBLE"
                compatibility_analysis["details"]["tensorflow"]["compatible"] = False
            elif minor_diff > 2:
                compatibility_analysis["warnings"].append(
                    f"TensorFlow minor version difference: model={model_tf}, current={current_tf}"
                )
        
        return compatibility_analysis
    
    def load_model_config(self) -> bool:
        """Lance le chargement de configuration de manière non-bloquante"""
        if self.config_loading_status == "loading":
            logger.info("[-] Chargement de configuration déjà en cours...")
            return False
        
        if self.config_loading_status == "success":
            logger.info("[✓] Configuration déjà chargée")
            return True
        
        if self.config_load_attempts >= self.max_config_attempts:
            logger.warning("[!] Nombre maximum de tentatives de chargement atteint")
            return False
        
        logger.info("=== CHARGEMENT CONFIGURATION MODÈLE (NON-BLOQUANT) ===")
        
        # Lancement asynchrone
        self._load_config_async()
        
        # Attente courte pour voir si ça se charge rapidement
        time.sleep(2)
        
        if self.config_loading_status == "success":
            return True
        elif self.config_loading_status == "failed":
            logger.warning(f"[!] Échec rapide du chargement: {self.config_loading_error}")
            self._create_default_model_info()
            return False
        else:
            logger.info("[-] Chargement en cours en arrière-plan...")
            self._create_default_model_info()
            return False
    
    def get_config_status(self) -> dict:
        """Retourne le statut de chargement de la configuration"""
        return {
            "status": self.config_loading_status,
            "error": self.config_loading_error,
            "attempts": self.config_load_attempts,
            "max_attempts": self.max_config_attempts,
            "config_available": self.model_config is not None
        }
    
    def retry_config_loading(self) -> bool:
        """Relance le chargement de la configuration"""
        if self.config_load_attempts >= self.max_config_attempts:
            logger.warning("[!] Nombre maximum de tentatives atteint, reset du compteur")
            self.config_load_attempts = 0
        
        self.config_loading_status = "not_started"
        self.config_loading_error = None
        
        return self.load_model_config()
    
    def _load_model_with_compatibility(self, model_path: str):
        """Charge le modèle TensorFlow avec gestion des incompatibilités"""
        import tensorflow as tf
        
        try:
            logger.info("Chargement du modèle...")
            model = tf.keras.models.load_model(model_path, compile=False)
            logger.info("[✓] Modèle chargé avec succès")
            return model
        except Exception as e:
            error_str = str(e)
            logger.warning(f"[!] Chargement standard échoué: {error_str}")
            
            # Tentative de chargement avec custom_objects pour certaines erreurs
            if "batch_shape" in error_str or "InputLayer" in error_str:
                try:
                    logger.info("Tentative avec custom_objects...")
                    model = tf.keras.models.load_model(
                        model_path, 
                        compile=False,
                        custom_objects={'InputLayer': tf.keras.layers.InputLayer}
                    )
                    logger.info("[✓] Chargement avec custom_objects réussi")
                    return model
                except Exception as e2:
                    logger.error(f"[X] Toutes les tentatives ont échoué: {e2}")
                    raise e
            else:
                raise e
    
    def load_model_from_artifacts(self) -> bool:
        """Chargement du modèle et tokenizer depuis les artifacts DagsHub"""
        logger.info("=== CHARGEMENT MODÈLE DEPUIS ARTIFACTS ===")
        
        # Chargement non-bloquant de la configuration
        self.load_model_config()
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Tentative {attempt + 1}/{self.max_retries} de chargement du modèle...")
                
                client = MlflowClient()
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Déterminer les noms de fichiers depuis la config ou utiliser les défauts
                    if self.model_config and self.config_loading_status == "success":
                        model_file = self.model_config.get("artifacts", {}).get("model_file", "model/nn_model_none_lstm.keras")
                        tokenizer_file = self.model_config.get("artifacts", {}).get("tokenizer_file", "model/nn_model_tokenizer_none_lstm.pkl")
                        logger.info("Utilisation des noms de fichiers depuis la configuration")
                    else:
                        model_file = "model/nn_model_none_lstm.keras"
                        tokenizer_file = "model/nn_model_tokenizer_none_lstm.pkl"
                        logger.info("Utilisation des noms de fichiers par défaut")
                    
                    # Chargement du modèle TensorFlow
                    logger.info(f"Téléchargement du modèle: {model_file}")
                    model_path = client.download_artifacts(self.model_run_id, model_file, temp_dir)
                    self.model = self._load_model_with_compatibility(model_path)
                    
                    # Chargement du tokenizer
                    logger.info(f"Téléchargement du tokenizer: {tokenizer_file}")
                    tokenizer_path = client.download_artifacts(self.model_run_id, tokenizer_file, temp_dir)
                    
                    with open(tokenizer_path, 'rb') as f:
                        self.tokenizer = pickle.load(f)
                    
                    logger.info(f"[✓] Tokenizer chargé - Vocab size: {len(self.tokenizer.word_index)}")
                    
                    # Validation si configuration disponible
                    if self.model_config and self.config_loading_status == "success":
                        config_vocab_size = self.model_config.get("preprocessing", {}).get("tokenizer", {}).get("vocabulary_size", 0)
                        actual_vocab_size = len(self.tokenizer.word_index)
                        
                        if config_vocab_size and abs(config_vocab_size - actual_vocab_size) > 100:
                            logger.warning(f"[!] Incohérence taille vocabulaire: config={config_vocab_size}, actual={actual_vocab_size}")
                    
                    logger.info("Modèle et tokenizer chargés avec succès !")
                    return True
                    
            except Exception as e:
                logger.warning(f"[X] Tentative {attempt + 1} échouée: {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"[-] Attente de {self.retry_delay}s avant nouvelle tentative...")
                    time.sleep(self.retry_delay)
        
        logger.error("[X] Échec de tous les chargements")
        return False
    
    def predict(self, text: str) -> Dict[str, Any]:
        """Prédiction de sentiment avec calcul correct de la confiance"""
        if not self.model or not self.tokenizer:
            raise ValueError("Modèle ou tokenizer non chargé")
        
        try:
            # Paramètres depuis la configuration ou valeurs par défaut
            if self.model_config and self.config_loading_status == "success":
                max_len = self.model_config.get("hyperparameters", {}).get("max_len", 100)
                preprocessing_mode = self.model_config.get("preprocessing", {}).get("mode", "none")
            else:
                max_len = 100
                preprocessing_mode = "none"
            
            # Tokenisation et padding
            sequences = self.tokenizer.texts_to_sequences([text])
            
            from tensorflow.keras.preprocessing.sequence import pad_sequences
            padded = pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')
            
            # Prédiction
            prediction = self.model.predict(padded, verbose=0)
            raw_score = float(prediction[0][0])  # Score brut entre 0 et 1
            
            # CORRECTION: Calcul correct du sentiment et de la confiance
            if raw_score > 0.5:
                sentiment = "positive"
                confidence = raw_score  # Confiance = probabilité positive
            else:
                sentiment = "negative"
                confidence = 1 - raw_score  # Confiance = probabilité négative (1 - prob_positive)
            
            result = {
                "text": text,
                "processed_text": f"Tokens: {len(sequences[0]) if sequences[0] else 0}, Padding: {max_len}",
                "sentiment": sentiment,
                "confidence": confidence,  # Maintenant cohérent avec le sentiment prédit
                "raw_score": raw_score,    # Score brut pour debug si nécessaire
                "model_info": self.model_info,
                "preprocessing_info": {
                    "mode": preprocessing_mode,
                    "original_length": len(text),
                    "tokens_count": len(sequences[0]) if sequences[0] else 0,
                    "padded_length": max_len,
                    "unknown_tokens": sum(1 for token in sequences[0] if token == 1) if sequences[0] else 0,
                    "max_len_from_config": max_len,
                    "config_status": self.config_loading_status
                },
                "config_status": self.get_config_status()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"[X] Erreur prédiction: {e}")
            return {
                "text": text,
                "processed_text": "Erreur de traitement",
                "sentiment": "neutral",
                "confidence": 0.5,
                "model_info": self.model_info,
                "config_status": self.get_config_status(),
                "error": str(e)
            }    
    def health_check(self) -> dict:
        """Vérification de santé avec statut de configuration"""
        return {
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,  
            "config_loaded": self.model_config is not None,
            "config_status": self.get_config_status(),
            "model_info": self.model_info,
            "input_shape": str(self.model.input_shape) if self.model else None,
            "vocab_size": len(self.tokenizer.word_index) if self.tokenizer else None,
            "version_compatibility": self.version_compatibility
        }
    
    def get_model_metadata(self) -> dict:
        """Retourne les métadonnées complètes avec statut de configuration"""
        base_metadata = {
            "config_status": self.get_config_status(),
            "current_environment": self._get_current_environment_versions()
        }
        
        if self.model_config and self.config_loading_status == "success":
            base_metadata.update({
                "config_loaded": True,
                "metadata": self.model_config.get("metadata", {}),
                "environment": self.model_config.get("environment", {}),
                "training": self.model_config.get("training", {}),
                "hyperparameters": self.model_config.get("hyperparameters", {}),
                "preprocessing": self.model_config.get("preprocessing", {}),
                "version_compatibility": self.version_compatibility
            })
        else:
            base_metadata.update({
                "config_loaded": False,
                "message": f"Configuration non chargée - Status: {self.config_loading_status}",
                "error": self.config_loading_error
            })
        
        return base_metadata
    
    def load_model(self) -> bool:
        """Point d'entrée principal non-bloquant pour le chargement du modèle"""
        logger.info("=== CHARGEMENT MODÈLE PRINCIPAL ===")
        
        success = self.load_model_from_artifacts()
        
        if not success:
            logger.warning("[!] Échec du chargement, création d'un modèle fallback")
            self._create_fallback_model()
            return False
        
        logger.info(f"Modèle chargé avec succès !")
        
        # Affichage du statut de configuration
        config_status = self.get_config_status()
        if config_status["status"] == "loading":
            logger.info("[-] Configuration en cours de chargement en arrière-plan")
        elif config_status["status"] == "failed":
            logger.warning(f"[!] Configuration non disponible: {config_status['error']}")
        elif config_status["status"] == "success":
            logger.info("[✓] Configuration chargée avec succès")
        
        return True
    
    def _create_fallback_model(self):
        """Crée un modèle de fallback minimal si le chargement principal échoue"""
        import tensorflow as tf
        from tensorflow.keras.preprocessing.text import Tokenizer
        
        logger.info("Création modèle fallback")
        
        # Modèle LSTM simple
        self.model = tf.keras.Sequential([
            tf.keras.layers.Embedding(1000, 64, input_length=100),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        self.model.compile(optimizer='adam', loss='binary_crossentropy')
        
        # Tokenizer basique
        self.tokenizer = Tokenizer(num_words=1000, oov_token="<OOV>")
        sample_texts = ["good", "bad", "excellent", "terrible", "okay"]
        self.tokenizer.fit_on_texts(sample_texts)
        
        self._create_default_model_info()
        self.model_info["type"] = "FALLBACK"
        
        logger.warning("[!] Modèle fallback créé - performances limitées")
    
    def test_connection(self) -> bool:
        """Test complet du service avec exemples de prédictions"""
        logger.info("=== TEST DE CONNEXION COMPLET ===")
        
        success = self.load_model()
        
        if success:
            test_texts = [
                "Service excellent d'Air Paradis!",
                "Vol retardé encore une fois!",
                "Vol parfait, équipage professionnel"
            ]
            
            logger.info("Test des prédictions...")
            for text in test_texts:
                try:
                    result = self.predict(text)
                    logger.info(f"[✓] '{text}' → {result['sentiment']} ({result['confidence']:.3f})")
                except Exception as e:
                    logger.error(f"[X] Erreur test '{text}': {e}")
        
        return success