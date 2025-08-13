# Sentiment Analysis Platform

Plateforme d'analyse de sentiments avec **FastAPI + Dash** connectée à **DagsHub/MLflow**.

##  Démarrage rapide

### Local avec Docker
```bash
# Construction de l'image
docker build -t sentiment-platform .

# Lancement avec variables d'environnement
docker run -p 8000:8000 \
  -e DAGSHUB_USERNAME=your-username \
  -e DAGSHUB_REPO=your-repo \
  -e DAGSHUB_TOKEN=your-token \
  sentiment-platform
```

### Développement local
```bash
# Installation des dépendances
pip install -r requirements.txt

# Configuration des variables d'environnement
export DAGSHUB_USERNAME=your-username
export DAGSHUB_REPO=your-repo  
export DAGSHUB_TOKEN=your-token

# Lancement
python main.py
```

### Docker Compose (recommandé pour le développement)
```bash
# Copier le fichier d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# Lancer avec Docker Compose
docker-compose up --build
```

##  URLs disponibles

Une fois l'application lancée :

- ** Page d'accueil** : http://localhost:8000
- ** API Documentation** : http://localhost:8000/api/v1/docs
- ** Dashboard interactif** : http://localhost:8000/dashboard/
- ** Health Check** : http://localhost:8000/health

## [[X]] Configuration

### Variables d'environnement nécessaires

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DAGSHUB_USERNAME` | Nom d'utilisateur DagsHub | `dev.nono.stargate` |
| `DAGSHUB_REPO` | Nom du repository DagsHub | `P7_tweet` |
| `DAGSHUB_TOKEN` | Token d'authentification DagsHub | `abc123...` |
| `PORT` | Port d'écoute (optionnel) | `8000` |
| `HOST` | Host d'écoute (optionnel) | `0.0.0.0` |

### Fichier `.env` (recommandé)
```bash
DAGSHUB_USERNAME=your-username
DAGSHUB_REPO=your-repo
DAGSHUB_TOKEN=your-token
PORT=8000
```

## [[X]] Architecture

```
sentiment-analysis-platform/
├── main.py                  #  Application principale (FastAPI + Dash)
├── api/                     #  API REST pour prédictions
│   ├── __init__.py
│   └── sentiment_api.py
├── dashboard/               #  Interface Dash interactive  
│   ├── __init__.py
│   └── sentiment_dashboard.py
├── services/                #  Services DagsHub/MLflow
│   ├── __init__.py
│   └── dagshub_service.py
├── utils/                   # [[X]] Utilitaires de prétraitement
│   ├── __init__.py
│   └── preprocessing.py
└── models/                  #  Modèles et configurations
    └── README.md
```

##  Déploiement Azure

### Azure Container Registry
```bash
# Se connecter à Azure
az acr login --name your-registry

# Build et push
chmod +x build_and_push.sh
./build_and_push.sh v1.0
```

### Azure Container Instances
```bash
az container create \
  --resource-group your-rg \
  --name sentiment-platform \
  --image your-registry.azurecr.io/sentiment-platform:v1.0 \
  --ports 80 \
  --environment-variables PORT=80 DAGSHUB_USERNAME=your-username DAGSHUB_REPO=your-repo \
  --secure-environment-variables DAGSHUB_TOKEN=your-token \
  --cpu 1 --memory 2
```

### Azure Container Apps
Voir le fichier `deploy.yml` pour la configuration complète.

##  Fonctionnalités

### API REST (`/api/v1/`)
- **POST `/predict`** : Prédiction de sentiment d'un tweet
- **POST `/feedback`** : Envoi de feedback utilisateur pour améliorer le modèle
- **GET `/health`** : État de santé de l'API
- **GET `/model/info`** : Informations sur le modèle chargé
- **GET `/experiments`** : Liste des expériences MLflow

### Dashboard interactif (`/dashboard/`)
- ** Test en temps réel** de l'API de prédiction
- ** Système de feedback** utilisateur avec boutons correcte/incorrecte
- ** Visualisation des expériences** MLflow depuis DagsHub
- ** Monitoring de l'état** du système et du modèle
- ** Graphiques de performance** des différents runs

### Intégration DagsHub/MLflow
- ** Chargement automatique** des modèles depuis le registre MLflow
- ** Téléchargement des données** directement depuis DagsHub
- ** Tracking des feedbacks** utilisateur dans MLflow
- ** Fallback automatique** si connexion DagsHub échoue

##  Tests et développement

```bash
# Installation des dépendances de développement
pip install pytest pytest-cov

# Lancement des tests
pytest tests/

# Tests avec couverture
pytest --cov=. tests/
```

##  Production

### Optimisations incluses
- [[X]] **Image Docker légère** (~800MB avec Python 3.12-slim)
- [[X]] **Cache layers optimisé** pour des rebuilds rapides  
- [[X]] **Health checks** intégrés pour Azure/Kubernetes
- [[X]] **Logging structuré** pour le monitoring
- [[X]] **Variables d'environnement** sécurisées
- [[X]] **Fallback robuste** en cas de problème DagsHub

### Monitoring et observabilité
- Logs structurés avec timestamps
- Métriques de performance exportées
- Health checks pour load balancers
- Feedback utilisateur tracké dans MLflow

##  Dépannage

### Problèmes courants

1. **Erreur de connexion DagsHub**
   ```bash
   # Vérifier les variables d'environnement
   echo $DAGSHUB_TOKEN
   
   # Tester la connexion
   curl -H "Authorization: token $DAGSHUB_TOKEN" https://dagshub.com/api/v1/user
   ```

2. **Modèle non trouvé**
   - L'application utilise un modèle de fallback automatiquement
   - Vérifier que le modèle existe dans MLflow sur DagsHub

3. **Dashboard ne se charge pas**
   ```bash
   # Vérifier que l'API répond
   curl http://localhost:8000/health
   ```

##  Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
