# Service pour l'interface utilisateur Dash
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import pandas as pd
from datetime import datetime
import uuid
import threading
import logging
import os

logger = logging.getLogger(__name__)

class DashUIService:
    """Service pour gérer l'interface utilisateur Dash avec design professionnel"""
    
    # constructeur de DashUIService
    def __init__(self, api_base_url="http://localhost:8000", azure_insights_service=None):
        self.api_base_url = api_base_url
        self.api_base = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
        self.azure_insights_service = azure_insights_service
        self.prediction_history = []
        self.feedback_history = []
        self._http = requests.Session()
        self._http.headers.update({"Content-Type": "application/json"})
        
        # Initialisation de l'app Dash avec thème Bootstrap
        self.app = dash.Dash(
            __name__, 
            external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
            suppress_callback_exceptions=True,
            title="P7 Tweet Sentiment Analysis"
        )
        
        self._setup_layout()
        self._setup_callbacks()
    
    def _send_feedback_to_api(self, feedback_payload: dict) -> dict:
        """
        Envoie le feedback à l’API FastAPI /feedback
        """
        url = f"{self.api_base}/feedback"
        resp = self._http.post(url, json=feedback_payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    # Si vous avez déjà une méthode publique qui construit le payload, gardez-la.
    # Exemple minimal où l’on construit et envoie le feedback puis logge Azure.
    def send_feedback(self, user_id: str, prediction_id: str, label: str, comment: str = "") -> dict:
        payload = {
            "user_id": user_id,
            "prediction_id": prediction_id,
            "label": label,
            "comment": comment or "",
        }
        try:
            api_resp = self._send_feedback_to_api(payload)
            if self.azure:
                try:
                    self.azure.log_feedback(payload)  # voir §2
                    logger.info("[AZURE] Feedback loggé pour user %s", user_id)
                except Exception as az_err:
                    logger.warning("Feedback envoyé à l'API mais échec log Azure: %s", az_err)
            return api_resp
        except Exception as e:
            logger.error("Erreur envoi feedback: %s", e, exc_info=True)
            raise
    
    
    def _get_professional_styles(self):
        """Définit les styles CSS professionnels en tons bleus"""
        return {
            'colors': {
                'primary': '#1e3a5f',        # Bleu marine foncé
                'secondary': '#2c5aa0',      # Bleu professionnel
                'accent': '#4a90e2',         # Bleu clair
                'light': '#f8fafc',          # Gris très clair
                'background': '#ffffff',     # Blanc pur
                'text_primary': '#1a202c',   # Gris foncé
                'text_secondary': '#4a5568', # Gris moyen
                'success': '#38a169',        # Vert professionnel
                'warning': '#d69e2e',        # Orange professionnel
                'danger': '#e53e3e',         # Rouge professionnel
                'border': '#e2e8f0'          # Bordure gris clair
            },
            'main_container': {
                'fontFamily': '"Inter", "Segoe UI", Roboto, sans-serif',
                'backgroundColor': '#f8fafc',
                'minHeight': '100vh',
                'padding': '0'
            },
            'header': {
                'backgroundColor': '#1e3a5f',
                'color': 'white',
                'padding': '1.5rem 0',
                'marginBottom': '0',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            },
            'content_section': {
                'backgroundColor': '#ffffff',
                'padding': '2rem',
                'marginBottom': '1.5rem',
                'border': '1px solid #e2e8f0',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
            },
            'card_header': {
                'backgroundColor': '#f7fafc',
                'borderBottom': '1px solid #e2e8f0',
                'padding': '1rem',
                'fontWeight': '600',
                'color': '#1a202c'
            },
            'primary_button': {
                'backgroundColor': '#2c5aa0',
                'border': 'none',
                'padding': '0.75rem 1.5rem',
                'fontWeight': '500',
                'transition': 'all 0.2s ease'
            },
            'metric_card': {
                'backgroundColor': '#ffffff',
                'border': '1px solid #e2e8f0',
                'padding': '1.5rem',
                'textAlign': 'center',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
            },
            'status_indicator': {
                'padding': '0.5rem 1rem',
                'fontSize': '0.875rem',
                'fontWeight': '500',
                'border': '1px solid #e2e8f0'
            }
        }
    
    def _create_navbar(self):
        """Création de la barre de navigation"""
        styles = self._get_professional_styles()
        
        return dbc.Navbar([
            dbc.Container([
                dbc.NavbarBrand([
                    html.I(className="fas fa-chart-line me-3"),
                    "P7 Tweet Sentiment Analysis"
                ], style={'fontSize': '1.5rem', 'fontWeight': '600'}),
                
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Analyse", href="/", id="nav-analyse", active=True)),
                    dbc.NavItem(dbc.NavLink("Administration", href="/admin", id="nav-admin")),
                ], navbar=True, className="ms-auto")
            ], fluid=True)
        ], color="primary", dark=True, sticky="top", style=styles['header'])
    
    def _setup_layout(self):
        """Configuration du layout principal"""
        styles = self._get_professional_styles()
        
        self.app.layout = html.Div([
            dcc.Location(id='url', refresh=False),
            self._create_navbar(),
            html.Div(id='page-content')
        ], style=styles['main_container'])
    
    def _create_analysis_page(self):
        """Page d'analyse principale avec métriques de feedback"""
        styles = self._get_professional_styles()
        
        return dbc.Container([
            # Section principale d'analyse
            html.Div([
                html.Div([
                    html.H4("Analyse de Sentiment", className="mb-0", 
                           style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                    html.P("Analysez le sentiment des tweets en temps réel", 
                           className="text-muted mb-0")
                ], style=styles['card_header']),
                
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Texte du tweet à analyser", 
                                     style={'fontWeight': '500', 'color': styles['colors']['text_primary']}),
                            dbc.Textarea(
                                id="tweet-input",
                                placeholder="Exemple: Le service d'Air Paradis était exceptionnel! Vol confortable et équipage professionnel.",
                                style={
                                    'minHeight': '120px',
                                    'border': f"1px solid {styles['colors']['border']}",
                                    'borderRadius': '4px',
                                    'fontSize': '0.95rem'
                                },
                                className="mb-3"
                            ),
                            
                            # Boutons d'action
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-search me-2"), "Analyser"],
                                        id="predict-btn",
                                        style=styles['primary_button'],
                                        className="w-100"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-eraser me-2"), "Effacer"],
                                        id="clear-btn",
                                        color="light",
                                        className="w-100",
                                        style={'border': f"1px solid {styles['colors']['border']}"}
                                    )
                                ], width=6)
                            ])
                        ], width=12)
                    ]),
                    
                    # Zone de résultat et feedback
                    html.Div(id="prediction-result", className="mt-4"),
                    html.Div(id="feedback-section", style={'display': 'none'}, className="mt-3")
                ], style={'padding': '2rem'})
            ], style=styles['content_section']),
            
            dbc.Row([
                # Métriques avec 4 indicateurs
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.H5("Statistiques", className="mb-0", 
                                   style={'color': styles['colors']['text_primary'], 'fontWeight': '600'})
                        ], style=styles['card_header']),
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.I(className="fas fa-chart-line", 
                                               style={'fontSize': '2rem', 'color': styles['colors']['secondary'], 'marginBottom': '0.5rem'}),
                                        html.H3(id="total-predictions", children="0", className="mb-1",
                                               style={'color': styles['colors']['text_primary'], 'fontWeight': '700'}),
                                        html.P("Total analyses", className="mb-0 text-muted", style={'fontSize': '0.9rem'})
                                    ], style=styles['metric_card'])
                                ], width=6),
                                dbc.Col([
                                    html.Div([
                                        html.I(className="fas fa-thumbs-up", 
                                               style={'fontSize': '2rem', 'color': styles['colors']['success'], 'marginBottom': '0.5rem'}),
                                        html.H3(id="positive-percentage", children="0%", className="mb-1",
                                               style={'color': styles['colors']['text_primary'], 'fontWeight': '700'}),
                                        html.P("Tweet positif", className="mb-0 text-muted", style={'fontSize': '0.9rem'})
                                    ], style=styles['metric_card'])
                                ], width=6)
                            ], className="g-3 mb-3"),
                            
                            # SÉPARATION VISUELLE
                            html.Hr(style={'margin': '1.5rem 0', 'borderColor': styles['colors']['border'], 'borderWidth': '2px'}),
                            
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.I(className="fas fa-check-circle", 
                                               style={'fontSize': '2rem', 'color': styles['colors']['accent'], 'marginBottom': '0.5rem'}),
                                        html.H3(id="accuracy-score", children="N/A", className="mb-1",
                                               style={'color': styles['colors']['text_primary'], 'fontWeight': '700'}),
                                        html.P('"Accuracy utilisateur"', className="mb-0 text-muted", style={'fontSize': '0.9rem'})  # CHANGÉ
                                    ], style=styles['metric_card'])
                                ], width=6),
                                dbc.Col([
                                    html.Div([
                                        html.I(className="fas fa-comments", 
                                               style={'fontSize': '2rem', 'color': styles['colors']['warning'], 'marginBottom': '0.5rem'}),
                                        html.H3(id="feedback-count", children="0", className="mb-1",
                                               style={'color': styles['colors']['text_primary'], 'fontWeight': '700'}),
                                        html.P("Validation utilisateur", className="mb-0 text-muted", style={'fontSize': '0.9rem'})  # CHANGÉ
                                    ], style=styles['metric_card'])
                                ], width=6)
                            ], className="g-3")
                        ], style={'padding': '1.5rem'})
                    ], style=styles['content_section'])
                ], width=4),
                
                # Graphique de répartition des sentiments
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.H5("Répartition des Sentiments", className="mb-0", 
                                   style={'color': styles['colors']['text_primary'], 'fontWeight': '600'})
                        ], style=styles['card_header']),
                        
                        html.Div([
                            dcc.Graph(id="sentiment-chart", style={'height': '300px'})
                        ], style={'padding': '1rem'})
                    ], style=styles['content_section'])
                ], width=8)
            ], className="mb-4"),
            
            # Historique des analyses
            html.Div([
                html.Div([
                    html.H5("Historique des Analyses", className="mb-0", 
                           style={'color': styles['colors']['text_primary'], 'fontWeight': '600'})
                ], style=styles['card_header']),
                
                html.Div([
                    html.Div(id="prediction-history")
                ], style={'padding': '1.5rem'})
            ], style=styles['content_section']),
            
            # Exemples de tweets pour test
            html.Div([
                html.Div([
                    html.H5("Exemples de Tweets", className="mb-0", 
                           style={'color': styles['colors']['text_primary'], 'fontWeight': '600'})
                ], style=styles['card_header']),
                
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-smile me-2", style={'color': styles['colors']['success']}),
                                "Amazing crew! They were so helpful and friendly."
                            ], id="example-positive", color="light", className="w-100 mb-2 text-start",
                               style={'border': f"1px solid {styles['colors']['border']}", 'padding': '0.75rem'})
                        ], width=4),
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-frown me-2", style={'color': styles['colors']['danger']}),
                                "Disappointed with the service. Will not fly again."
                            ], id="example-negative", color="light", className="w-100 mb-2 text-start",
                               style={'border': f"1px solid {styles['colors']['border']}", 'padding': '0.75rem'})
                        ], width=4),
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-plane me-2", style={'color': styles['colors']['secondary']}),
                                "le vol était en retard, mais j'ai fais de belles rencontres."
                            ], id="example-neutral", color="light", className="w-100 mb-2 text-start",
                               style={'border': f"1px solid {styles['colors']['border']}", 'padding': '0.75rem'})
                        ], width=4)
                    ])
                ], style={'padding': '1.5rem'})
            ], style=styles['content_section'])
        ], fluid=True, style={'padding': '2rem 0'})
    
    def _create_admin_page(self):
        """Page d'administration pour les informations système et modèle"""
        styles = self._get_professional_styles()
        
        return dbc.Container([
            html.Div([
                html.Div([
                    html.H4("Administration", className="mb-0", 
                           style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                    html.P("Informations détaillées sur le système et les modèles", 
                           className="text-muted mb-0")
                ], style=styles['card_header']),
                
                html.Div([
                    # Statut du système
                    dbc.Row([
                        dbc.Col([
                            html.H5("Statut du système", style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                            html.Div(id="admin-system-status")
                        ], width=6),
                        dbc.Col([
                            html.H5("Compatibilité des versions", style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                            html.Div(id="admin-version-compatibility")
                        ], width=6)
                    ], className="mb-4"),
                    
                    # Informations du modèle
                    html.H5("Informations du modèle", style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                    html.Div(id="admin-model-info", className="mb-4"),
                    
                    # Configuration détaillée
                    html.H5("Configuration détaillée", style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                    html.Div(id="admin-detailed-config", className="mb-4"),
                    
                    # Version et Déploiement
                    html.H5("Version et Déploiement", style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                    html.Div(id="admin-version-deployment", className="mb-4"),
                    
                    # Azure Application Insights
                    html.H5("Azure Application Insights", style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                    html.Div(id="admin-azure-insights", className="mb-4"),
                    
                    # Tests et diagnostics
                    html.H5("Actions", style={'color': styles['colors']['text_primary'], 'fontWeight': '600'}),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-2"),
                                "Actualiser Stats"
                            ], id="refresh-stats-btn", color="primary", className="w-100 mb-2")
                        ], width=3)
                    ]),
                  
                    html.Div(id="admin-test-results", className="mt-3")
                ], style={'padding': '2rem'})
            ], style=styles['content_section'])
        ], fluid=True, style={'padding': '2rem 0'})
       
    def _setup_callbacks(self):
        """Configuration des callbacks Dash avec gestion du feedback utilisateur"""
        
        # Navigation entre pages
        @self.app.callback(
            [Output('page-content', 'children'),
             Output('nav-analyse', 'active'),
             Output('nav-admin', 'active')],
            Input('url', 'pathname')
        )
        def display_page(pathname):
            if pathname == '/admin':
                return self._create_admin_page(), False, True
            else:
                return self._create_analysis_page(), True, False
        
        # Callbacks pour les exemples de tweets
        @self.app.callback(
            Output('tweet-input', 'value'),
            [Input('example-positive', 'n_clicks'),
             Input('example-negative', 'n_clicks'),
             Input('example-neutral', 'n_clicks')]
        )
        def set_example_text(pos_clicks, neg_clicks, neu_clicks):
            ctx = callback_context
            if not ctx.triggered:
                return ""
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            examples = {
                'example-positive': "Amazing crew! They were so helpful and friendly.",
                'example-negative': "Disappointed with the service. Will not fly again.",
                'example-neutral': "le vol était en retard, mais j'ai fais de belles rencontres."
            }
            
            return examples.get(button_id, "")
        
        # Callback pour effacer le champ de saisie
        @self.app.callback(
            Output('tweet-input', 'value', allow_duplicate=True),
            Input('clear-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def clear_input(n_clicks):
            if n_clicks:
                return ""
            return dash.no_update
        
        # Callback principal pour la prédiction avec nouvelles métriques
        @self.app.callback(
            [Output('prediction-result', 'children'),
             Output('feedback-section', 'children'),
             Output('feedback-section', 'style'),
             Output('prediction-history', 'children'),
             Output('total-predictions', 'children'),
             Output('positive-percentage', 'children'),
             Output('accuracy-score', 'children'),
             Output('feedback-count', 'children'),
             Output('sentiment-chart', 'figure')],
            Input('predict-btn', 'n_clicks'),
            State('tweet-input', 'value'),
            prevent_initial_call=True
        )
        def make_prediction(n_clicks, text):
            if not n_clicks or not text:
                return dash.no_update
            
            success, result = self._predict_sentiment(text)
            
            if not success:
                styles = self._get_professional_styles()
                error_result = html.Div([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Erreur: {result.get('error', 'Erreur inconnue')}"
                ], style={
                    'padding': '1rem',
                    'backgroundColor': '#fed7d7',
                    'color': '#c53030',
                    'border': '1px solid #feb2b2'
                })
                return error_result, "", {'display': 'none'}, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            return self._process_prediction_result(text, result)
        
        # traitement du feedback pour appeler l'API
        def _send_feedback_to_api(self, feedback_data):
            """Envoyer le feedback à l'API pour logging Azure"""
            try:
                response = requests.post(
                    f"{self.api_base_url}/feedback",
                    json=feedback_data,
                    timeout=5
                )
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Erreur envoi feedback API: {e}")
                return False

        # Callback pour gérer le feedback utilisateur
        @self.app.callback(
            [Output('accuracy-score', 'children', allow_duplicate=True),
             Output('feedback-count', 'children', allow_duplicate=True)],
            [Input({'type': 'feedback-correct', 'index': dash.dependencies.ALL}, 'n_clicks'),
             Input({'type': 'feedback-incorrect', 'index': dash.dependencies.ALL}, 'n_clicks')],
            prevent_initial_call=True
        )
        def handle_feedback(correct_clicks, incorrect_clicks):
            ctx = callback_context
            if not ctx.triggered:
                return dash.no_update, dash.no_update
            
            # Vérifier qu'il y a eu un vrai clic (pas juste l'initialisation)
            trigger_info = ctx.triggered[0]
            prop_id = trigger_info['prop_id']
            new_value = trigger_info['value']
            
            # Si la valeur est None ou 0, pas de nouveau clic
            if not new_value:
                return dash.no_update, dash.no_update
            
            # Déterminer le type de feedback depuis l'ID du bouton cliqué
            if 'feedback-correct' in prop_id:
                feedback_type = 'correct'
            elif 'feedback-incorrect' in prop_id:
                feedback_type = 'incorrect'
            else:
                return dash.no_update, dash.no_update
            
            # Extraire prediction_id depuis l'ID du bouton
            try:
                import json
                button_info = json.loads(prop_id.split('.')[0])
                prediction_id = button_info.get('index', 'unknown')
            except:
                prediction_id = 'unknown'
            
            # Trouver la prédiction correspondante pour enrichir les données
            prediction_info = None
            for pred in self.prediction_history:
                if pred.get('prediction_id') == prediction_id:
                    prediction_info = pred
                    break
            
            # Enregistrer le feedback localement
            feedback_record = {
                'timestamp': datetime.now(),
                'feedback': feedback_type,
                'prediction_id': prediction_id
            }
            self.feedback_history.append(feedback_record)
            
            # Préparer les données pour l'API
            feedback_data = {
                'feedback_type': feedback_type,
                'prediction_id': prediction_id,
                'timestamp': datetime.now().isoformat(),
                'user_id': 'dash_user'
            }
            
            # Ajouter les informations de la prédiction originale si disponibles
            if prediction_info:
                feedback_data.update({
                    'original_sentiment': prediction_info.get('sentiment'),
                    'original_confidence': prediction_info.get('confidence'),
                    'original_text': prediction_info.get('text', '')
                })
            
            # Envoyer à l'API pour logging Azure (non bloquant)
            try:
                self._send_feedback_to_api(feedback_data)
            except Exception as e:
                logger.error(f"Erreur envoi feedback: {e}")
            
            # Calculer les nouvelles métriques
            total_feedback = len(self.feedback_history)
            correct_feedback = sum(1 for f in self.feedback_history if f['feedback'] == 'correct')
            accuracy_percentage = (correct_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            return f"{accuracy_percentage:.0f}%", str(total_feedback)
        
        # Callbacks pour l'administration
        @self.app.callback(
            [Output('admin-system-status', 'children'),
             Output('admin-version-compatibility', 'children'),
             Output('admin-model-info', 'children'),
             Output('admin-detailed-config', 'children'),
             Output('admin-version-deployment', 'children'),
             Output('admin-azure-insights', 'children')],
            Input('url', 'pathname')
        )
        def update_admin_info(pathname):
            if pathname != '/admin':
                return dash.no_update
            
            admin_info = self._get_admin_info()
            styles = self._get_professional_styles()
            version_deployment = self._create_version_deployment_card(styles)
            azure_insights = self._create_azure_insights_card(styles)
            
            return (admin_info[0], admin_info[1], admin_info[2], admin_info[3], 
                    version_deployment, azure_insights)
        
        # Callbacks pour le/les Actions - page admin
        @self.app.callback(
            [Output('admin-test-results', 'children'),
             Output('admin-azure-insights', 'children', allow_duplicate=True)],
            Input('refresh-stats-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def handle_admin_tests(refresh):

            if not refresh:
                return "", dash.no_update
            # Rafraîchir uniquement la carte Azure
            styles = self._get_professional_styles()
            refreshed_azure = self._create_azure_insights_card(styles)
            return "Statistiques Azure rafraîchies avec succès!", refreshed_azure

    
    def _check_api_status(self):
        """Vérifier le statut de l'API"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"error": f"Status {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def _predict_sentiment(self, text):
        """Appeler l'API de prédiction de sentiment"""
        try:
            response = requests.post(
                f"{self.api_base_url}/predict",
                json={"text": text, "user_id": "dash_user"},
                timeout=10
            )
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"error": f"Status {response.status_code}: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}
            
    def _process_prediction_result(self, text, result):
        """Traiter et formater le résultat de prédiction"""
        styles = self._get_professional_styles()
        sentiment = result['sentiment']
        confidence = result['confidence']
        
        # Générer un ID unique pour cette prédiction
        prediction_id = str(uuid.uuid4())
        
        # Style en fonction du sentiment
        if sentiment == "positive":
            result_style = {
                'background': f"linear-gradient(135deg, {styles['colors']['success']} 0%, #48bb78 100%)",
                'color': 'white',
                'padding': '2rem',
                'textAlign': 'center',
                'border': 'none'
            }
            icon = "fas fa-thumbs-up fa-3x mb-3"
        else:
            result_style = {
                'background': f"linear-gradient(135deg, {styles['colors']['danger']} 0%, #f56565 100%)",
                'color': 'white',
                'padding': '2rem',
                'textAlign': 'center',
                'border': 'none'
            }
            icon = "fas fa-thumbs-down fa-3x mb-3"
        
        # Affichage du résultat
        prediction_display = html.Div([
            html.I(className=icon),
            html.H3(f"Sentiment: {sentiment.title()}", className="mb-2", style={'fontWeight': '600'}),
            html.H5(f"Confiance: {confidence:.1%}", className="mb-3"),
            html.Hr(style={'borderColor': 'white', 'opacity': '0.3', 'margin': '1rem 0'}),
            html.P(f"Texte analysé: \"{text[:100]}{'...' if len(text) > 100 else ''}\"", 
                   style={'fontStyle': 'italic', 'opacity': '0.9'})
        ], style=result_style)
        
        # Section de feedback avec IDs uniques
        feedback_section = html.Div([
            html.Div([
                html.H6("Cette prédiction est-elle correcte ?", 
                       style={'color': styles['colors']['text_primary'], 'fontWeight': '600'})
            ], style=styles['card_header']),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-check me-2"),
                            "Correct"
                        ], 
                        id={'type': 'feedback-correct', 'index': prediction_id},
                        color="success", outline=True, className="w-100")
                    ], width=6),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-times me-2"),
                            "Incorrect"
                        ], 
                        id={'type': 'feedback-incorrect', 'index': prediction_id},
                        color="danger", outline=True, className="w-100")
                    ], width=6)
                ])
            ], style={'padding': '1rem'})
        ], style=styles['content_section'])
        
        # Ajouter à l'historique avec prediction_id
        prediction_record = {
            'timestamp': datetime.now(),
            'text': text,
            'sentiment': sentiment,
            'confidence': confidence,
            'prediction_id': prediction_id
        }
        self.prediction_history.append(prediction_record)
        
        # Mise à jour des statistiques
        total_preds = len(self.prediction_history)
        positive_count = sum(1 for p in self.prediction_history if p['sentiment'] == 'positive')
        positive_pct = (positive_count / total_preds * 100) if total_preds > 0 else 0
        
        # Calcul des métriques de feedback
        total_feedback = len(self.feedback_history)
        correct_feedback = sum(1 for f in self.feedback_history if f['feedback'] == 'correct')
        accuracy_percentage = (correct_feedback / total_feedback * 100) if total_feedback > 0 else 0
        
        # Historique des prédictions (10 dernières)
        history_items = []
        for i, pred in enumerate(reversed(self.prediction_history[-10:])):
            sentiment_icon = "fas fa-thumbs-up" if pred['sentiment'] == 'positive' else "fas fa-thumbs-down"
            sentiment_color = styles['colors']['success'] if pred['sentiment'] == 'positive' else styles['colors']['danger']
            
            item = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.I(className=sentiment_icon, style={'color': sentiment_color, 'marginRight': '0.5rem'}),
                        html.Strong(f"{pred['sentiment'].title()} ({pred['confidence']:.1%})")
                    ], width=8),
                    dbc.Col([
                        html.Small(pred['timestamp'].strftime("%H:%M"), 
                                  style={'color': styles['colors']['text_secondary']})
                    ], width=4, className="text-end")
                ]),
                html.P(pred['text'][:80] + "..." if len(pred['text']) > 80 else pred['text'], 
                      className="mb-0 mt-2", 
                      style={'fontSize': '0.9rem', 'color': styles['colors']['text_secondary']})
            ], style={
                'padding': '1rem',
                'borderBottom': f"1px solid {styles['colors']['border']}"
            })
            history_items.append(item)
        
        history_display = html.Div(history_items) if history_items else html.P(
            "Aucune analyse effectuée", 
            className="text-muted text-center",
            style={'padding': '2rem'}
        )
        
        # Graphique des sentiments
        if self.prediction_history:
            import pandas as pd
            sentiment_counts = pd.Series([p['sentiment'] for p in self.prediction_history]).value_counts()
            colors = [styles['colors']['success'] if s == 'positive' else styles['colors']['danger'] for s in sentiment_counts.index]
            
            fig = px.pie(
                values=sentiment_counts.values,
                names=[s.title() for s in sentiment_counts.index],
                color_discrete_sequence=colors,
                title=""
            )
            fig.update_layout(
                showlegend=True,
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
                font=dict(family="Inter, sans-serif"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_traces(textfont_size=12, marker=dict(line=dict(color='#ffffff', width=2)))
        else:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(
                text="Aucune donnée", 
                showarrow=False, 
                x=0.5, y=0.5,
                font=dict(size=16, color=styles['colors']['text_secondary'])
            )
            fig.update_layout(
                height=300, 
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
        
        return (prediction_display, 
                feedback_section, 
                {'display': 'block'}, 
                history_display,
                str(total_preds),
                f"{positive_pct:.0f}%",
                f"{accuracy_percentage:.0f}%" if total_feedback > 0 else "N/A",
                str(total_feedback),
                fig)
    
    def _get_admin_info(self):
        """Récupère les informations d'administration depuis l'API"""
        styles = self._get_professional_styles()
        
        try:
            # Appels API pour récupérer les informations
            health_response = requests.get(f"{self.api_base_url}/health", timeout=5)
            model_response = requests.get(f"{self.api_base_url}/model/info", timeout=5)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
            else:
                health_data = {"error": "Impossible de récupérer les informations de santé"}
            
            if model_response.status_code == 200:
                model_data = model_response.json()
            else:
                model_data = {"error": "Impossible de récupérer les informations du modèle"}
            
            # Création des cartes d'information
            system_status = self._create_system_status_card(health_data, styles)
            version_compatibility = self._create_version_compatibility_card(model_data, styles)
            model_info = self._create_model_info_card(model_data, styles)
            detailed_config = self._create_detailed_config_card(model_data, styles)
            
            return system_status, version_compatibility, model_info, detailed_config
            
        except Exception as e:
            error_card = html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erreur lors de la récupération des informations: {str(e)}"
            ], style={
                'padding': '1rem',
                'backgroundColor': '#fed7d7',
                'color': '#c53030',
                'border': '1px solid #feb2b2'
            })
            return error_card, error_card, error_card, error_card
    
    def _create_system_status_card(self, health_data, styles):
        """Crée la carte de statut du système"""
        if 'error' in health_data:
            status_color = styles['colors']['danger']
            status_icon = "fas fa-times-circle"
            status_text = "Hors ligne"
        else:
            if health_data.get('model_loaded', False):
                status_color = styles['colors']['success']
                status_icon = "fas fa-check-circle"
                status_text = "Opérationnel"
            else:
                status_color = styles['colors']['warning']
                status_icon = "fas fa-exclamation-circle"
                status_text = "Dégradé"
        
        return html.Div([
            html.Div([
                html.I(className=status_icon, style={'color': status_color, 'fontSize': '1.5rem', 'marginRight': '0.5rem'}),
                html.Strong(status_text, style={'color': status_color})
            ], className="mb-3"),
            
            html.Table([
                html.Tbody([
                    html.Tr([
                        html.Td("Modèle chargé:", style={'fontWeight': '500', 'width': '50%'}),
                        html.Td(
                            "[✓] Oui" if health_data.get('model_loaded', False) else "[X] Non",
                            style={'color': styles['colors']['success'] if health_data.get('model_loaded', False) else styles['colors']['danger']}
                        )
                    ]),
                    html.Tr([
                        html.Td("Configuration chargée:", style={'fontWeight': '500'}),
                        html.Td(
                            "[✓] Oui" if health_data.get('config_loaded', False) else "[X] Non",
                            style={'color': styles['colors']['success'] if health_data.get('config_loaded', False) else styles['colors']['danger']}
                        )
                    ]),
                    html.Tr([
                        html.Td("Tokenizer chargé:", style={'fontWeight': '500'}),
                        html.Td(
                            "[✓] Oui" if health_data.get('tokenizer_loaded', False) else "[X] Non",
                            style={'color': styles['colors']['success'] if health_data.get('tokenizer_loaded', False) else styles['colors']['danger']}
                        )
                    ]),
                    html.Tr([
                        html.Td("Taille vocabulaire:", style={'fontWeight': '500'}),
                        html.Td(
                            f"{health_data.get('vocab_size', 0):,}" if health_data.get('vocab_size') else "N/A"
                        )
                    ])
                ])
            ], className="table table-sm", style={'marginBottom': '0'})
        ], style={
            'padding': '1.5rem',
            'backgroundColor': '#ffffff',
            'border': f"1px solid {styles['colors']['border']}",
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        })
    
    def _create_version_compatibility_card(self, model_data, styles):
        """Crée la carte de compatibilité des versions"""
        if 'error' in model_data:
            return html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Impossible de vérifier la compatibilité"
            ], style={
                'padding': '1rem',
                'backgroundColor': '#fed7d7',
                'color': '#c53030',
                'border': '1px solid #feb2b2'
            })
        
        metadata = model_data.get('metadata', {})
        version_compatibility = metadata.get('version_compatibility', {})
        current_env = metadata.get('current_environment', {})
        model_env = metadata.get('environment', {})
        
        if not version_compatibility and not current_env:
            return html.Div([
                html.P("Informations de compatibilité non disponibles", 
                       className="text-muted text-center", style={'padding': '2rem'})
            ])
        
        overall_status = version_compatibility.get('overall_status', 'UNKNOWN')
        
        if overall_status == 'COMPATIBLE':
            status_color = styles['colors']['success']
            status_icon = "fas fa-check-circle"
        elif overall_status == 'INCOMPATIBLE':
            status_color = styles['colors']['danger']
            status_icon = "fas fa-times-circle"
        else:
            status_color = styles['colors']['warning']
            status_icon = "fas fa-exclamation-circle"
        
        compatibility_items = []
        
        # Statut global
        compatibility_items.append(
            html.Div([
                html.I(className=status_icon, style={'color': status_color, 'marginRight': '0.5rem'}),
                html.Strong(f"Statut: {overall_status}", style={'color': status_color})
            ], className="mb-3")
        )
        
        # Tableau des versions pour tous les packages
        packages_to_check = [
            'tensorflow_version', 'python_version', 'numpy_version', 
            'pandas_version', 'scikit_learn_version', 'mlflow_version', 
            'fastapi_version'
        ]
        
        version_table = []
        for package_key in packages_to_check:
            package_name = package_key.replace('_version', '').replace('_', '-').title()
            model_version = model_env.get(package_key, 'N/A')
            current_version = current_env.get(package_key, 'N/A')
            
            # Déterminer la compatibilité
            if model_version == 'N/A' or current_version == 'N/A':
                compatible = None
                status_text = "N/A"
            elif model_version == current_version:
                compatible = True
                status_text = "[✓]"
            else:
                # Comparaison simple des versions
                compatible = True  # Par défaut compatible sauf pour les cas majeurs
                if package_key == 'tensorflow_version':
                    try:
                        model_major = int(model_version.split('.')[0])
                        current_major = int(current_version.split('.')[0])
                        compatible = model_major == current_major
                    except:
                        compatible = None
                status_text = "[✓]" if compatible else "[X]" if compatible is False else "[!]"
            
            version_table.append(
                html.Tr([
                    html.Td(package_name, style={'fontWeight': '500'}),
                    html.Td(model_version),
                    html.Td(current_version),
                    html.Td(
                        status_text,
                        style={
                            'color': styles['colors']['success'] if status_text == "[✓]" 
                                   else styles['colors']['danger'] if status_text == "[X]"
                                   else styles['colors']['warning']
                        }
                    )
                ])
            )
        
        compatibility_items.append(
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Package"),
                        html.Th("Version du modèle"),
                        html.Th("Version API"),
                        html.Th("Compatible")
                    ])
                ]),
                html.Tbody(version_table)
            ], className="table table-sm")
        )
        
        # Problèmes critiques
        critical_issues = version_compatibility.get('critical_issues', [])
        if critical_issues:
            compatibility_items.append(
                html.Div([
                    html.H6("Problèmes critiques:", style={'color': styles['colors']['danger'], 'fontWeight': '600'}),
                    html.Ul([
                        html.Li(issue, style={'color': styles['colors']['danger']}) 
                        for issue in critical_issues
                    ])
                ])
            )
        
        # Avertissements
        warnings = version_compatibility.get('warnings', [])
        if warnings:
            compatibility_items.append(
                html.Div([
                    html.H6("Avertissements:", style={'color': styles['colors']['warning'], 'fontWeight': '600'}),
                    html.Ul([
                        html.Li(warning, style={'color': styles['colors']['warning']}) 
                        for warning in warnings
                    ])
                ])
            )
        
        return html.Div(compatibility_items, style={
            'padding': '1.5rem',
            'backgroundColor': '#ffffff',
            'border': f"1px solid {styles['colors']['border']}",
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        })
    
    def _create_model_info_card(self, model_data, styles):
        """Crée la carte d'informations du modèle"""
        if 'error' in model_data:
            return html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Impossible de récupérer les informations du modèle"
            ], style={
                'padding': '1rem',
                'backgroundColor': '#fed7d7',
                'color': '#c53030',
                'border': '1px solid #feb2b2'
            })
        
        model_info = model_data.get('model_info', {})
        metadata = model_data.get('metadata', {})
        
        if not model_info and not metadata:
            return html.Div([
                html.P("Informations du modèle non disponibles", 
                       className="text-muted text-center", style={'padding': '2rem'})
            ])
        
        # Informations générales du modèle
        general_info = metadata.get('metadata', {}) if 'metadata' in metadata else model_info
        
        info_rows = []
        
        # Informations de base
        basic_info = [
            ("Nom du modèle", general_info.get('name', general_info.get('model_name', 'N/A'))),
            ("Type", general_info.get('type', general_info.get('model_type', 'N/A'))),
            ("Version", general_info.get('version', 'N/A')),
            ("Run ID", general_info.get('run_id', 'N/A')),
            ("Architecture", general_info.get('architecture', 'N/A')),
            ("Accuracy", f"{general_info.get('accuracy', 0):.1%}" if general_info.get('accuracy') else 'N/A')
        ]
        
        for label, value in basic_info:
            info_rows.append(
                html.Tr([
                    html.Td(label + ":", style={'fontWeight': '500', 'width': '40%'}),
                    html.Td(str(value))
                ])
            )
        
        # Informations d'entraînement
        training_info = metadata.get('training', {})
        if training_info:
            info_rows.append(
                html.Tr([
                    html.Td(html.Strong("Entraînement", style={'color': styles['colors']['primary']}), colSpan=2)
                ])
            )
            
            training_metrics = [
                ("Époques", training_info.get('epochs_trained', 'N/A')),
                ("F1-Score", f"{training_info.get('f1_score', 0):.3f}" if training_info.get('f1_score') else 'N/A'),
                ("Précision", f"{training_info.get('precision', 0):.3f}" if training_info.get('precision') else 'N/A'),
                ("Rappel", f"{training_info.get('recall', 0):.3f}" if training_info.get('recall') else 'N/A'),
                ("ROC AUC", f"{training_info.get('roc_auc', 0):.3f}" if training_info.get('roc_auc') else 'N/A')
            ]
            
            for label, value in training_metrics:
                info_rows.append(
                    html.Tr([
                        html.Td("  " + label + ":", style={'paddingLeft': '2rem'}),
                        html.Td(str(value))
                    ])
                )
        
        # Hyperparamètres
        hyperparams = metadata.get('hyperparameters', {})
        if hyperparams:
            info_rows.append(
                html.Tr([
                    html.Td(html.Strong("Hyperparamètres", style={'color': styles['colors']['primary']}), colSpan=2)
                ])
            )
            
            hyperparam_list = [
                ("Dimension embedding", hyperparams.get('embedding_dim', 'N/A')),
                ("Unités LSTM", hyperparams.get('lstm_units', 'N/A')),
                ("Unités dense", hyperparams.get('dense_units', 'N/A')),
                ("Taux de dropout", hyperparams.get('dropout_rate', 'N/A')),
                ("Longueur max", hyperparams.get('max_len', 'N/A')),
                ("Features max", f"{hyperparams.get('max_features', 'N/A'):,}" if hyperparams.get('max_features') else 'N/A'),
                ("Taux d'apprentissage", hyperparams.get('learning_rate', 'N/A')),
                ("Taille de batch", f"{hyperparams.get('batch_size', 'N/A'):,}" if hyperparams.get('batch_size') else 'N/A')
            ]
            
            for label, value in hyperparam_list:
                info_rows.append(
                    html.Tr([
                        html.Td("  " + label + ":", style={'paddingLeft': '2rem'}),
                        html.Td(str(value))
                    ])
                )
        
        return html.Div([
            html.Table([
                html.Tbody(info_rows)
            ], className="table table-sm", style={'marginBottom': '0'})
        ], style={
            'padding': '1.5rem',
            'backgroundColor': '#ffffff',
            'border': f"1px solid {styles['colors']['border']}",
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        })
    
    def _load_version_info(self):
        """Charger les informations de version depuis le fichier JSON"""
        try:
            with open('/app/version_info.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {
                "error": f"Impossible de charger version_info.json: {str(e)}",
                "fetch_info": {"github_repo": {"owner": "N/A", "repo": "N/A"}, "branch": "N/A"},
                "commit_id": "N/A",
                "commit_date": "N/A",
                "files": []
            }

    def _create_version_deployment_card(self, styles):
        """Créer la carte Version et Déploiement"""
        version_info = self._load_version_info()
        
        # Variables d'environnement Azure
        env_vars = {
            'AZ_RESOURCE_GROUP': os.getenv('AZ_RESOURCE_GROUP', 'N/A'),
            'AZ_CONTAINER': os.getenv('AZ_CONTAINER', 'N/A'),
            'AZ_REGION': os.getenv('AZ_REGION', 'N/A'),
            'IMAGE': os.getenv('IMAGE', 'N/A'),
            'ENVIRONMENT': os.getenv('ENVIRONMENT', 'production')
        }
        
        github_info = version_info.get('fetch_info', {}).get('github_repo', {})
        
        deployment_rows = []
        
        # Informations GitHub
        deployment_rows.extend([
            html.Tr([
                html.Td(html.Strong("Repository GitHub", style={'color': styles['colors']['primary']}), colSpan=2)
            ]),
            html.Tr([
                html.Td("Owner:", style={'paddingLeft': '2rem', 'fontWeight': '500', 'width': '40%'}),
                html.Td(github_info.get('owner', 'N/A'))
            ]),
            html.Tr([
                html.Td("Repository:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(github_info.get('repo', 'N/A'))
            ]),
            html.Tr([
                html.Td("Branch:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(version_info.get('fetch_info', {}).get('branch', 'N/A'))
            ]),
            html.Tr([
                html.Td("Commit ID:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(version_info.get('commit_id', 'N/A'))
            ]),
            html.Tr([
                html.Td("Date commit:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(version_info.get('commit_date', 'N/A'))
            ])
        ])
        
        # Informations Azure
        deployment_rows.extend([
            html.Tr([
                html.Td(html.Strong("Déploiement Azure", style={'color': styles['colors']['primary']}), colSpan=2)
            ]),
            html.Tr([
                html.Td("Resource Group:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(env_vars['AZ_RESOURCE_GROUP'])
            ]),
            html.Tr([
                html.Td("Container:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(env_vars['AZ_CONTAINER'])
            ]),
            html.Tr([
                html.Td("Region:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(env_vars['AZ_REGION'])
            ]),
            html.Tr([
                html.Td("Image Docker:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(env_vars['IMAGE'])
            ]),
            html.Tr([
                html.Td("Environment:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                html.Td(env_vars['ENVIRONMENT'])
            ])
        ])
        
        # Fichiers modifiés (derniers 5)
        files = version_info.get('files', [])[:5]
        if files:
            deployment_rows.append(
                html.Tr([
                    html.Td(html.Strong("Fichiers modifiés (derniers commits)", style={'color': styles['colors']['primary']}), colSpan=2)
                ])
            )
            
            for file_info in files:
                status_color = {
                    'A': styles['colors']['success'],  # Ajouté
                    'M': styles['colors']['warning'],  # Modifié
                    'D': styles['colors']['danger']    # Supprimé
                }.get(file_info.get('status', 'M'), styles['colors']['text_secondary'])
                
                deployment_rows.append(
                    html.Tr([
                        html.Td(
                            f"[{file_info.get('status', '?')}] {file_info.get('file', 'unknown')}",
                            style={'paddingLeft': '2rem', 'fontSize': '0.85rem', 'fontFamily': 'monospace'}
                        ),
                        html.Td(
                            file_info.get('date', 'N/A'),
                            style={'fontSize': '0.85rem', 'color': status_color}
                        )
                    ])
                )
        
        return html.Div([
            html.Table([
                html.Tbody(deployment_rows)
            ], className="table table-sm", style={'marginBottom': '0'})
        ], style={
            'padding': '1.5rem',
            'backgroundColor': '#ffffff',
            'border': f"1px solid {styles['colors']['border']}",
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        })

    def _create_azure_insights_card(self, styles):
        """Créer la carte Azure Application Insights avec statistiques"""
        # Variables d'environnement Azure Insights
        insights_vars = {
            'AZ_INSTRUMENTATION_KEY': os.getenv('AZ_INSTRUMENTATION_KEY', 'N/A'),
            'AZ_CONNECTION_STRING': bool(os.getenv('AZ_CONNECTION_STRING')),
            'AZ_WORKPLACE': os.getenv('AZ_WORKPLACE', 'N/A')
        }
        
        # Récupérer les statistiques depuis l'API
        try:
            response = requests.get(f"{self.api_base_url}/admin/azure-insights", timeout=5)
            if response.status_code == 200:
                insights_status = response.json()
            else:
                insights_status = {'enabled': False, 'error': 'API non disponible'}
        except Exception as e:
            insights_status = {'enabled': False, 'error': str(e)}
        
        # Statut de la connexion
        insights_configured = insights_status.get('enabled', False)
        
        if insights_configured:
            status_color = styles['colors']['success']
            status_icon = "fas fa-check-circle"
            status_text = "Configuré"
        else:
            status_color = styles['colors']['danger']
            status_icon = "fas fa-times-circle"
            status_text = "Non configuré"
        
        insights_rows = [
            html.Tr([
                html.Td([
                    html.I(className=status_icon, style={'color': status_color, 'marginRight': '0.5rem'}),
                    html.Strong(f"Statut: {status_text}", style={'color': status_color})
                ], colSpan=2)
            ]),
            html.Tr([
                html.Td("Instrumentation Key:", style={'fontWeight': '500', 'width': '40%'}),
                html.Td(
                    "Configurée" if insights_vars['AZ_INSTRUMENTATION_KEY'] != 'N/A' else "Non configurée",
                    style={'color': styles['colors']['success'] if insights_vars['AZ_INSTRUMENTATION_KEY'] != 'N/A' else styles['colors']['danger']}
                )
            ]),
            html.Tr([
                html.Td("Connection String:", style={'fontWeight': '500'}),
                html.Td(
                    "Configurée" if insights_vars['AZ_CONNECTION_STRING'] else "Non configurée",
                    style={'color': styles['colors']['success'] if insights_vars['AZ_CONNECTION_STRING'] else styles['colors']['danger']}
                )
            ]),
            html.Tr([
                html.Td("Workspace:", style={'fontWeight': '500'}),
                html.Td(insights_vars['AZ_WORKPLACE'])
            ])
        ]
        
        # Ajouter les statistiques si le service est activé
        if insights_configured and 'predictions_count' in insights_status:
            insights_rows.extend([
                html.Tr([
                    html.Td(html.Strong("Statistiques d'utilisation", style={'color': styles['colors']['primary']}), colSpan=2)
                ]),
                html.Tr([
                    html.Td("Prédictions enregistrées:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                    html.Td(str(insights_status.get('predictions_count', 0)))
                ]),
                html.Tr([
                    html.Td("Feedbacks enregistrés:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                    html.Td(str(insights_status.get('feedback_count', 0)))
                ]),
                html.Tr([
                    html.Td("Dernière prédiction:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                    html.Td(
                        insights_status.get('last_prediction', 'Aucune'),
                        style={'fontSize': '0.9rem', 'fontFamily': 'monospace'}
                    )
                ]),
                html.Tr([
                    html.Td("Dernier feedback:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                    html.Td(
                        insights_status.get('last_feedback', 'Aucun'),
                        style={'fontSize': '0.9rem', 'fontFamily': 'monospace'}
                    )
                ]),
                html.Tr([
                    html.Td("Session démarrée:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                    html.Td(
                        insights_status.get('session_start', 'N/A'),
                        style={'fontSize': '0.9rem', 'fontFamily': 'monospace'}
                    )
                ]),
                html.Tr([
                    html.Td("Durée de session:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                    html.Td(
                        insights_status.get('session_duration', 'N/A'),
                        style={'fontSize': '0.9rem', 'fontFamily': 'monospace'}
                    )
                ])
            ])
        elif insights_configured:
            insights_rows.append(
                html.Tr([
                    html.Td("Statistiques:", style={'paddingLeft': '2rem', 'fontWeight': '500'}),
                    html.Td("En cours de chargement...", style={'fontStyle': 'italic'})
                ])
            )
        
        return html.Div([
            html.Table([
                html.Tbody(insights_rows)
            ], className="table table-sm", style={'marginBottom': '0'})
        ], style={
            'padding': '1.5rem',
            'backgroundColor': '#ffffff',
            'border': f"1px solid {styles['colors']['border']}",
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        })
    
    def _create_detailed_config_card(self, model_data, styles):
        """Crée la carte de configuration détaillée"""
        if 'error' in model_data:
            return html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Configuration non disponible"
            ], style={
                'padding': '1rem',
                'backgroundColor': '#fed7d7',
                'color': '#c53030',
                'border': '1px solid #feb2b2'
            })
        
        metadata = model_data.get('metadata', {})
        
        if not metadata:
            return html.Div([
                html.P("Configuration détaillée non disponible", 
                       className="text-muted text-center", style={'padding': '2rem'})
            ])
        
        # Configuration JSON formatée
        config_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        
        return html.Div([
            html.Pre(
                config_json,
                style={
                    'backgroundColor': '#f7fafc',
                    'padding': '1rem',
                    'border': f"1px solid {styles['colors']['border']}",
                    'borderRadius': '4px',
                    'fontSize': '0.85rem',
                    'maxHeight': '400px',
                    'overflowY': 'auto',
                    'fontFamily': '"Fira Code", "Courier New", monospace'
                }
            )
        ], style={
            'padding': '1.5rem',
            'backgroundColor': '#ffffff',
            'border': f"1px solid {styles['colors']['border']}",
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        })
    
    
    def _format_test_result(self, test_name, data, success):
        """Formate le résultat d'un test administratif"""
        styles = self._get_professional_styles()
        
        if success:
            card_style = {
                'backgroundColor': '#f0fff4',
                'border': f"1px solid {styles['colors']['success']}",
                'padding': '1rem',
                'marginTop': '1rem'
            }
            icon = "fas fa-check-circle"
            color = styles['colors']['success']
        else:
            card_style = {
                'backgroundColor': '#fff5f5',
                'border': f"1px solid {styles['colors']['danger']}",
                'padding': '1rem',
                'marginTop': '1rem'
            }
            icon = "fas fa-times-circle"
            color = styles['colors']['danger']
        
        return html.Div([
            html.H6([
                html.I(className=icon, style={'color': color, 'marginRight': '0.5rem'}),
                test_name
            ]),
            html.Pre(
                json.dumps(data, indent=2, ensure_ascii=False),
                style={
                    'backgroundColor': '#f7fafc',
                    'padding': '1rem',
                    'border': f"1px solid {styles['colors']['border']}",
                    'borderRadius': '4px',
                    'fontSize': '0.85rem',
                    'maxHeight': '300px',
                    'overflowY': 'auto',
                    'fontFamily': '"Fira Code", "Courier New", monospace',
                    'marginTop': '0.5rem'
                }
            )
        ], style=card_style)
    
    def run_server(self, host='0.0.0.0', port=8050, debug=False):
        """Démarrer le serveur Dash"""
        logger.info(f"Démarrage de l'interface Dash sur {host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug, threaded=True)
    
    def run_in_thread(self, host='0.0.0.0', port=8050, debug=False):
        """Démarrer le serveur Dash dans un thread séparé"""
        def run():
            self.run_server(host=host, port=port, debug=debug)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info(f"Interface Dash démarrée en arrière-plan sur {host}:{port}")
        return thread