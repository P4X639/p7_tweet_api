# P7_tweet_API

Service d'API d'analyse de sentiments de tweet :  
* Dev : Docker Desktop + Jupyter Lab
* Build : **Google Colab** + notebook
* Sauvegarde du modèle : **DagsHub/MLflow**
* Sauvegarde des données et notebooks : **Google drive** (stockage)
* **Dockerhub**
* **Github**
* **FastAPI** connecté à DagsHub/MLflow
* **Dash**

##  Démarrage rapide

### Local avec Docker
```bash
# Construction de l'image

```

### Développement local
```bash
# Installation des dépendances

```

### Docker Compose 
```bash
# todo
```

##  URLs disponibles 

Attention, l'URL publique change à chaque démarrage du cocker 
- ** Health Check** : http://localhost:8000/health

## [[X]] Configuration

### Variables d'environnement nécessaires

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DAGSHUB_REPO` | Nom du repository DagsHub | `P7_tweet` |


### Fichier `.env`
```bash
...
```

## [[X]] Architecture

```
p7_tweet_api/
├── main.py                  #  Application principale (FastAPI + Dash)
├── services/                #  Services DagsHub/MLflow
│   ├── ***
│   └── dagshub_service.py
├── utils/                   # [[X]] Utilitaires de prétraitement
│   ├── ***
│   └── ***
└── assets/                  #  CSS

```

##  Déploiement Azure

### Azure Container
```bash
#todo
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

### API REST 
- **POST `/predict`** : Prédiction de sentiment d'un tweet
- **GET `/health`** : État de santé de l'API
- ***

### Intégration DagsHub/MLflow
- ** Chargement automatique** du modèle depuis le registre MLflow

##  Tests et développement


##  Production

