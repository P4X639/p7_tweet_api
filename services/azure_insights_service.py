# Version finale simplifiée de services/azure_insights_service.py
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Import avec gestion d'erreur
try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    AZURE_AVAILABLE = True
except ImportError as e:
    print(f"Erreur import Azure: {e}")
    AZURE_AVAILABLE = False

logger = logging.getLogger(__name__)

class AzureInsightsService:
    """Service Azure Insights avec debug complet"""
    
    def __init__(self):
        print("[DEBUG] Initialisation AzureInsightsServiceDebug")
        
        # Variables d'environnement avec debug
        self.connection_string = os.getenv("AZ_CONNECTION_STRING")
        self.instrumentation_key = os.getenv("AZ_INSTRUMENTATION_KEY")
        
        print(f"[DEBUG] Connection String présente: {bool(self.connection_string)}")
        print(f"[DEBUG] Instrumentation Key présente: {bool(self.instrumentation_key)}")
        
        if self.connection_string:
            # Masquer les infos sensibles mais afficher la structure
            masked_cs = self.connection_string[:20] + "..." + self.connection_string[-20:] if len(self.connection_string) > 40 else "SHORT"
            print(f"[DEBUG] Connection String (masquée): {masked_cs}")
        
        # État du service
        self.enabled = False
        self.logger = logging.getLogger(__name__)
        self.azure_logger = None
        
        # Statistiques avec timestamps détaillés
        self.usage_stats = {
            'predictions_count': 0,
            'feedback_count': 0,
            'last_prediction': None,
            'last_feedback': None,
            'session_start': datetime.utcnow(),
            'logs_sent': 0,
            'logs_failed': 0,
            'last_error': None,
            'initialization_time': datetime.utcnow().isoformat()
        }
        
        # Debug détaillé de l'initialisation
        if not AZURE_AVAILABLE:
            print("[ERROR] Bibliothèque Azure non disponible")
            self.usage_stats['last_error'] = "Azure library not available"
            return
            
        if self.connection_string or self.instrumentation_key:
            print("[DEBUG] Tentative de configuration Azure logging...")
            self._setup_azure_logging_debug()
        else:
            print("[ERROR] Aucune variable Azure configurée")
            self.usage_stats['last_error'] = "No Azure variables configured"
    
    def _setup_azure_logging_debug(self):
        """Configuration avec debug détaillé"""
        try:
            print("[DEBUG] Début configuration Azure handler")
            
            # Logger spécifique pour Azure
            self.azure_logger = logging.getLogger('azure_insights_data_debug')
            self.azure_logger.setLevel(logging.INFO)
            
            # Nettoyer les handlers existants
            for handler in self.azure_logger.handlers[:]:
                self.azure_logger.removeHandler(handler)
                print(f"[DEBUG] Handler supprimé: {type(handler)}")
            
            # Configuration du handler Azure
            if self.connection_string:
                print("[DEBUG] Configuration avec Connection String")
                handler = AzureLogHandler(connection_string=self.connection_string)
            else:
                print("[DEBUG] Configuration avec Instrumentation Key")
                handler = AzureLogHandler(instrumentation_key=self.instrumentation_key)
            
            # Configuration détaillée du handler
            handler.setLevel(logging.INFO)
            self.azure_logger.addHandler(handler)
            self.azure_logger.propagate = False
            
            self.enabled = True
            print("[DEBUG] Azure logging configuré avec succès")
            
            # Test immédiat de connexion
            print("[DEBUG] Test de connexion immédiat...")
            self._test_azure_connection_debug()
            
        except Exception as e:
            print(f"[ERROR] Erreur configuration Azure: {e}")
            self.enabled = False
            self.usage_stats['last_error'] = f"Setup failed: {str(e)}"
    
    def _test_azure_connection_debug(self):
        """Test de connexion avec debug complet"""
        try:
            print("[DEBUG] Envoi test de connexion...")
            
            test_data = {
                'event_type': 'debug_connection_test',
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Test de connexion Azure Insights DEBUG',
                'service_version': '1.0.0-debug',
                'test_id': f"test_{int(datetime.utcnow().timestamp())}"
            }
            
            print(f"[DEBUG] Données de test: {json.dumps(test_data, indent=2)}")
            
            # Envoi via azure_logger
            self.azure_logger.info(
                'Azure Insights Debug Connection Test',
                extra={'custom_dimensions': test_data}
            )
            
            self.usage_stats['logs_sent'] += 1
            print(f"[DEBUG] Test envoyé - Total logs: {self.usage_stats['logs_sent']}")
            
            # Force flush pour s'assurer de l'envoi
            for handler in self.azure_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
                    print("[DEBUG] Handler flushed")
            
        except Exception as e:
            print(f"[ERROR] Test connexion échoué: {e}")
            self.usage_stats['logs_failed'] += 1
            self.usage_stats['last_error'] = f"Connection test failed: {str(e)}"
    
    def log_prediction(self, prediction_data: Dict[str, Any]):
        """Log de prédiction avec debug complet"""
        print(f"[DEBUG] log_prediction appelé - enabled: {self.enabled}")
        print(f"[DEBUG] Données reçues: {json.dumps(prediction_data, indent=2, default=str)}")
        
        if not self.enabled or not self.azure_logger:
            print("[ERROR] Service non activé ou logger non disponible")
            return False
        
        try:
            # Mettre à jour les statistiques
            self.usage_stats['predictions_count'] += 1
            self.usage_stats['last_prediction'] = datetime.utcnow()
            
            # Enrichir les données avec debug
            log_data = {
                'event_type': 'prediction_debug',
                'sentiment': prediction_data.get('sentiment'),
                'confidence': float(prediction_data.get('confidence', 0)),
                'text_length': len(prediction_data.get('text', '')),
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': prediction_data.get('user_id', 'anonymous'),
                'model_name': prediction_data.get('model_info', {}).get('name', 'unknown'),
                'session_id': id(self),
                'debug_info': {
                    'predictions_count': self.usage_stats['predictions_count'],
                    'service_enabled': self.enabled,
                    'logger_available': self.azure_logger is not None
                }
            }
            
            print(f"[DEBUG] Données à envoyer: {json.dumps(log_data, indent=2, default=str)}")
            
            # Envoi avec debug
            self.azure_logger.info(
                'Debug Prediction Made',
                extra={'custom_dimensions': log_data}
            )
            
            # Force flush
            for handler in self.azure_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            self.usage_stats['logs_sent'] += 1
            print(f"[DEBUG] Prédiction envoyée - Total: {self.usage_stats['logs_sent']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Erreur log prediction: {e}")
            self.usage_stats['logs_failed'] += 1
            self.usage_stats['last_error'] = f"Log prediction failed: {str(e)}"
            return False
    
    def log_feedback_prev(self, feedback_data: Dict[str, Any]):
        """Log de feedback avec debug complet"""
        print(f"[DEBUG] log_feedback appelé - enabled: {self.enabled}")
        print(f"[DEBUG] Données feedback: {json.dumps(feedback_data, indent=2, default=str)}")
        
        if not self.enabled or not self.azure_logger:
            print("[ERROR] Service non activé pour feedback")
            return False
        
        try:
            # Mettre à jour les statistiques
            self.usage_stats['feedback_count'] += 1
            self.usage_stats['last_feedback'] = datetime.utcnow()
            
            log_data = {
                'event_type': 'user_feedback_debug',
                'feedback_type': feedback_data.get('feedback_type'),
                'prediction_id': feedback_data.get('prediction_id'),
                'original_sentiment': feedback_data.get('original_sentiment'),
                'original_confidence': float(feedback_data.get('original_confidence', 0)) if feedback_data.get('original_confidence') else None,
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': feedback_data.get('user_id', 'anonymous'),
                'session_id': id(self),
                'debug_info': {
                    'feedback_count': self.usage_stats['feedback_count'],
                    'service_enabled': self.enabled
                }
            }
            
            print(f"[DEBUG] Données feedback à envoyer: {json.dumps(log_data, indent=2, default=str)}")
            
            self.azure_logger.info(
                'Debug User Feedback Received',
                extra={'custom_dimensions': log_data}
            )
            
            # Force flush
            for handler in self.azure_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            self.usage_stats['logs_sent'] += 1
            print(f"[DEBUG] Feedback envoyé - Total: {self.usage_stats['logs_sent']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Erreur log feedback: {e}")
            self.usage_stats['logs_failed'] += 1
            self.usage_stats['last_error'] = f"Log feedback failed: {str(e)}"
            return False


    def log_feedback(self, feedback_data: Dict[str, Any]):
        """
        Enregistre un feedback utilisateur dans Azure Application Insights
        avec une structure de données optimisée pour la production et les requêtes.
        """
        if not self.enabled or not self.azure_logger:
            # Utiliser le logger standard pour tracer cette erreur interne
            logger.warning("Service Azure non activé ou logger non disponible pour le feedback.")
            return False
        
        try:
            # Mettre à jour les statistiques internes
            self.usage_stats['feedback_count'] += 1
            self.usage_stats['last_feedback'] = datetime.utcnow()
            
            # 1. Structure de données aplatie et enrichie pour les requêtes KQL
            log_data = {
                'event_type': 'user_feedback',  # Nom propre, sans "debug"
                'feedback_type': feedback_data.get('feedback_type'),  # 'correct' ou 'incorrect'
                'user_id': feedback_data.get('user_id', 'anonymous'),
                'prediction_id': feedback_data.get('prediction_id'),
                'original_sentiment': feedback_data.get('original_sentiment'),
                'original_confidence': float(feedback_data['original_confidence']) if feedback_data.get('original_confidence') is not None else None,
                
                # 2. Ajout crucial du texte du tweet
                'tweet_text': feedback_data.get('original_text', ''),

                'session_id': id(self),
                'feedback_count_session': self.usage_stats['feedback_count'], # Compteur de la session actuelle
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 3. Message de log plus sémantique
            log_message = f"Feedback Received: {log_data['feedback_type']}"
            
            self.azure_logger.info(
                log_message,
                extra={'custom_dimensions': log_data}
            )
            
            # Forcer l'envoi immédiat des logs
            for handler in self.azure_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            self.usage_stats['logs_sent'] += 1
            logger.info(f"Feedback '{log_data['feedback_type']}' pour la prédiction {log_data['prediction_id']} envoyé à Azure.")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du feedback à Azure: {e}", exc_info=True)
            self.usage_stats['logs_failed'] += 1
            self.usage_stats['last_error'] = f"Log feedback failed: {str(e)}"
            return False

    def get_service_status(self) -> Dict[str, Any]:
        """Statut détaillé avec debug"""
        status = {
            'enabled': self.enabled,
            'connection_string_configured': bool(self.connection_string),
            'instrumentation_key_configured': bool(self.instrumentation_key),
            'status': 'operational' if self.enabled else 'disabled',
            'azure_library_available': AZURE_AVAILABLE,
            'azure_logger_ready': self.azure_logger is not None,
            'debug_info': {
                'initialization_time': self.usage_stats['initialization_time'],
                'last_error': self.usage_stats['last_error'],
                'handler_count': len(self.azure_logger.handlers) if self.azure_logger else 0
            }
        }
        
        if self.enabled:
            status.update({
                'predictions_count': self.usage_stats['predictions_count'],
                'feedback_count': self.usage_stats['feedback_count'],
                'logs_sent': self.usage_stats['logs_sent'],
                'logs_failed': self.usage_stats['logs_failed'],
                'last_prediction': self.usage_stats['last_prediction'].isoformat() if self.usage_stats['last_prediction'] else None,
                'last_feedback': self.usage_stats['last_feedback'].isoformat() if self.usage_stats['last_feedback'] else None
            })
        
        return status
    
    def force_send_test_log(self):
        """Test forcé avec debug maximal"""
        print("[DEBUG] force_send_test_log appelé")
        
        if not self.enabled:
            return {"success": False, "error": "Service non activé"}
        
        try:
            test_data = {
                'event_type': 'forced_manual_test',
                'timestamp': datetime.utcnow().isoformat(),
                'test_message': 'Log de test forcé avec debug',
                'forced': True,
                'test_timestamp': int(datetime.utcnow().timestamp()),
                'debug_session': id(self)
            }
            
            print(f"[DEBUG] Test forcé - données: {json.dumps(test_data, indent=2)}")
            
            self.azure_logger.info(
                'Forced Manual Test Log',
                extra={'custom_dimensions': test_data}
            )
            
            # Force flush multiple
            for handler in self.azure_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
                    print(f"[DEBUG] Handler flushed: {type(handler)}")
            
            self.usage_stats['logs_sent'] += 1
            print(f"[DEBUG] Test forcé envoyé - Total: {self.usage_stats['logs_sent']}")
            
            return {"success": True, "message": "Log de test forcé envoyé avec debug"}
            
        except Exception as e:
            print(f"[ERROR] Test forcé échoué: {e}")
            self.usage_stats['logs_failed'] += 1
            self.usage_stats['last_error'] = f"Forced test failed: {str(e)}"
            return {"success": False, "error": str(e)}