# Actions Docker - Sentiment Analysis Platform

## Résumé des opérations Docker pour le projet d'analyse de sentiments

---

## 1. Préparation de l'environnement Docker

### Création de la structure de répertoire
```bash
# Créer le répertoire principal pour l'image Docker
mkdir -p ~/docker-images/sentiment-analysis-platform
cd ~/docker-images/sentiment-analysis-platform

# Créer la structure complète du projet
mkdir -p {api,dashboard,services,utils,models,tests,data,logs,tensorboard_logs}
```

### Vérification des prérequis
```bash
# Vérifier que Docker est installé et fonctionne
docker --version
docker info

# Vérifier l'espace disque disponible
df -h
```

---

## 2. Fichiers Docker essentiels

### 2.1 Dockerfile optimisé

**Caractéristiques :**
- Base image : `python:3.12-slim-bookworm`
- Taille finale : ~800MB
- Optimisations : cache layers, exclusion fichiers inutiles

**Commande de création :**
```bash
cat > Dockerfile << 'EOF'
FROM python:3.12-slim-bookworm
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y curl gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY api/ ./api/
COPY dashboard/ ./dashboard/
COPY services/ ./services/
COPY utils/ ./utils/
COPY models/ ./models/

RUN mkdir -p data models reports tensorboard_logs

EXPOSE 8000
CMD ["python", "main.py"]
EOF
```

### 2.2 .dockerignore pour optimiser la taille
```bash
cat > .dockerignore << 'EOF'
__pycache__/
*.py[cod]
.git
.env
.venv
*.log
tests/
docs/
*.md
data/raw/
models/*.h5
models/*.pb
EOF
```

### 2.3 requirements.txt
```bash
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
dash==2.14.2
tensorflow==2.15.0
scikit-learn==1.3.2
mlflow==2.8.1
dagshub==0.3.1
nltk==3.8.1
requests==2.31.0
EOF
```

---

## 3. Construction de l'image Docker

### 3.1 Build manuel
```bash
# Construction de base
docker build -t sentiment-platform .

# Construction avec tag spécifique
docker build -t sentiment-platform:v1.0 .

# Construction avec contexte spécifique
docker build -t sentiment-platform -f Dockerfile .
```

### 3.2 Script de build automatisé
```bash
# Créer le script build.sh
cat > build.sh << 'EOF'
#!/bin/bash
set -e

IMAGE_NAME="P7_tweet_azure_api"
TAG=${1:-latest}

echo "Construction de l'image Docker: $IMAGE_NAME:$TAG"
docker build -t $IMAGE_NAME:$TAG .
echo "Image construite avec succès: $IMAGE_NAME:$TAG"
docker images $IMAGE_NAME:$TAG
EOF

chmod +x build.sh

# Utilisation
./build.sh              # Build avec tag 'latest'
./build.sh v1.0         # Build avec tag 'v1.0'
```

### 3.3 Vérifications post-build
```bash
# Lister les images créées
docker images sentiment-platform

# Inspecter l'image
docker inspect sentiment-platform:latest

# Vérifier les layers
docker history sentiment-platform:latest

# Vérifier la taille
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

---

## 4. Tests de l'image Docker

### 4.1 Test basique
```bash
# Lancement simple
docker run --rm -p 8000:8000 sentiment-platform

# Lancement avec variables d'environnement
docker run --rm -p 8000:8000 \
  -e DAGSHUB_USERNAME=your-username \
  -e DAGSHUB_REPO=your-repo \
  -e DAGSHUB_TOKEN=your-token \
  sentiment-platform
```

### 4.2 Test avec fichier .env
```bash
# Créer le fichier .env
cp .env.example .env
# Éditer avec vos paramètres

# Lancer avec le fichier .env
docker run --rm -p 8000:8000 --env-file .env sentiment-platform
```

### 4.3 Script de test automatisé
```bash
# Créer le script test-docker.sh
cat > test-docker.sh << 'EOF'
#!/bin/bash
set -e

IMAGE_NAME="sentiment-platform"
CONTAINER_NAME="test-sentiment-platform"

# Lancement du container de test
docker run -d --name $CONTAINER_NAME -p 8001:8000 \
    -e DAGSHUB_USERNAME=test-user \
    $IMAGE_NAME:latest

# Tests des endpoints
sleep 10
curl -f http://localhost:8001/health
curl -f http://localhost:8001/api/v1/docs

# Nettoyage
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME
echo "Tests réussis !"
EOF

chmod +x test-docker.sh
./test-docker.sh
```

### 4.4 Vérifications fonctionnelles
```bash
# Health check
curl http://localhost:8000/health

# Test API
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'

# Accès au dashboard
curl http://localhost:8000/dashboard/

# Documentation API
curl http://localhost:8000/api/v1/docs
```

---

## 5. Docker Compose pour l'environnement de développement

### 5.1 Fichier docker-compose.yml
```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  sentiment-platform:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - PORT=8000
      - DAGSHUB_USERNAME=${DAGSHUB_USERNAME}
      - DAGSHUB_REPO=${DAGSHUB_REPO}
      - DAGSHUB_TOKEN=${DAGSHUB_TOKEN}
    volumes:
      - ./models:/app/models:ro
      - ./data:/app/data:ro
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF
```

### 5.2 Commandes Docker Compose
```bash
# Construction et lancement
docker-compose up --build

# Lancement en arrière-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêt des services
docker-compose down

# Arrêt avec suppression des volumes
docker-compose down -v

# Reconstruction forcée
docker-compose build --no-cache
```

---

## 6. Gestion des containers

### 6.1 Opérations de base
```bash
# Lister les containers actifs
docker ps

# Lister tous les containers
docker ps -a

# Arrêter un container
docker stop <container_id>

# Redémarrer un container
docker restart <container_id>

# Supprimer un container
docker rm <container_id>

# Forcer la suppression
docker rm -f <container_id>
```

### 6.2 Logs et debugging
```bash
# Voir les logs en temps réel
docker logs -f <container_id>

# Voir les dernières lignes
docker logs --tail 50 <container_id>

# Se connecter au container
docker exec -it <container_id> /bin/bash

# Exécuter une commande dans le container
docker exec <container_id> ls -la /app/

# Copier des fichiers depuis/vers le container
docker cp <container_id>:/app/logs ./local-logs
docker cp ./local-file <container_id>:/app/
```

### 6.3 Monitoring des ressources
```bash
# Statistiques en temps réel
docker stats <container_id>

# Informations détaillées
docker inspect <container_id>

# Utilisation des ressources
docker system df

# Processus dans le container
docker top <container_id>
```

---

## 7. Optimisation et nettoyage

### 7.1 Nettoyage des ressources
```bash
# Supprimer les containers arrêtés
docker container prune

# Supprimer les images non utilisées
docker image prune

# Supprimer les volumes non utilisés
docker volume prune

# Nettoyage complet
docker system prune -a

# Nettoyage avec confirmation
docker system prune -a --volumes
```

### 7.2 Optimisation de l'image
```bash
# Analyser la taille des layers
docker history sentiment-platform:latest

# Construire sans cache pour optimiser
docker build --no-cache -t sentiment-platform .

# Utiliser multi-stage build (avancé)
docker build -t sentiment-platform:optimized -f Dockerfile.multi .
```

---

## 8. Déploiement vers un registry

### 8.1 Tag et push vers Docker Hub
```bash
# Tagger l'image
docker tag sentiment-platform:latest username/sentiment-platform:latest

# Se connecter à Docker Hub
docker login

# Pousser l'image
docker push username/sentiment-platform:latest
```

### 8.2 Tag et push vers Azure Container Registry
```bash
# Se connecter à Azure
az acr login --name your-registry

# Tagger pour Azure
docker tag sentiment-platform:latest your-registry.azurecr.io/sentiment-platform:v1.0

# Pousser vers Azure
docker push your-registry.azurecr.io/sentiment-platform:v1.0
```

### 8.3 Script de déploiement
```bash
cat > deploy-image.sh << 'EOF'
#!/bin/bash
set -e

REGISTRY=${1:-"your-registry.azurecr.io"}
IMAGE_NAME="sentiment-platform"
TAG=${2:-"latest"}

echo "Déploiement vers $REGISTRY..."

# Tag pour le registry
docker tag $IMAGE_NAME:latest $REGISTRY/$IMAGE_NAME:$TAG

# Push vers le registry
docker push $REGISTRY/$IMAGE_NAME:$TAG

echo "Image déployée: $REGISTRY/$IMAGE_NAME:$TAG"
EOF

chmod +x deploy-image.sh
./deploy-image.sh your-registry.azurecr.io v1.0
```

---

## 9. Troubleshooting Docker

### 9.1 Problèmes de build
```bash
# Build avec logs détaillés
docker build --progress=plain -t sentiment-platform .

# Build sans cache pour debugger
docker build --no-cache -t sentiment-platform .

# Vérifier l'espace disque
df -h
docker system df
```

### 9.2 Problèmes de runtime
```bash
# Vérifier les logs d'erreur
docker logs <container_id>

# Vérifier les variables d'environnement
docker exec <container_id> env

# Vérifier les processus
docker exec <container_id> ps aux

# Tester la connectivité réseau
docker exec <container_id> curl localhost:8000/health
```

### 9.3 Problèmes de performance
```bash
# Monitorer les ressources
docker stats <container_id>

# Limiter les ressources
docker run --memory=2g --cpus=1.5 sentiment-platform

# Analyser l'utilisation
docker exec <container_id> top
docker exec <container_id> df -h
```

---

## 10. Scripts utilitaires

### 10.1 Script complet de gestion
```bash
cat > docker-manager.sh << 'EOF'
#!/bin/bash

IMAGE_NAME="sentiment-platform"
CONTAINER_NAME="sentiment-platform-app"

case "$1" in
    build)
        echo "Construction de l'image..."
        docker build -t $IMAGE_NAME .
        ;;
    run)
        echo "Lancement du container..."
        docker run -d --name $CONTAINER_NAME -p 8000:8000 --env-file .env $IMAGE_NAME
        ;;
    stop)
        echo "Arrêt du container..."
        docker stop $CONTAINER_NAME
        ;;
    remove)
        echo "Suppression du container..."
        docker rm -f $CONTAINER_NAME
        ;;
    logs)
        docker logs -f $CONTAINER_NAME
        ;;
    shell)
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    clean)
        echo "Nettoyage complet..."
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        docker system prune -f
        ;;
    *)
        echo "Usage: $0 {build|run|stop|remove|logs|shell|clean}"
        exit 1
        ;;
esac
EOF

chmod +x docker-manager.sh
```

### 10.2 Utilisation du script de gestion
```bash
./docker-manager.sh build    # Construire l'image
./docker-manager.sh run      # Lancer le container
./docker-manager.sh logs     # Voir les logs
./docker-manager.sh shell    # Se connecter au container
./docker-manager.sh stop     # Arrêter le container
./docker-manager.sh clean    # Nettoyer tout
```

---

## 11. Checklist Docker

### Avant le build
- [ ] Dockerfile présent et configuré
- [ ] .dockerignore créé pour optimiser la taille
- [ ] requirements.txt à jour
- [ ] Variables d'environnement définies
- [ ] Structure de dossiers correcte

### Après le build
- [ ] Image construite sans erreur
- [ ] Taille d'image acceptable (~800MB)
- [ ] Test de lancement réussi
- [ ] Endpoints accessibles (health, API, dashboard)
- [ ] Logs sans erreurs critiques

### Pour le déploiement
- [ ] Image taguée correctement
- [ ] Registry configuré et accessible
- [ ] Variables d'environnement de production définies
- [ ] Tests de charge effectués
- [ ] Monitoring configuré

---

## 12. Commandes de référence rapide

```bash
# Construction
docker build -t sentiment-platform .

# Lancement simple
docker run --rm -p 8000:8000 --env-file .env sentiment-platform

# Lancement avec Docker Compose
docker-compose up -d

# Voir les logs
docker logs -f <container_id>

# Se connecter au container
docker exec -it <container_id> /bin/bash

# Nettoyage
docker system prune -a

# Statistiques
docker stats <container_id>

# Informations système
docker system df
docker system info
```

Cette documentation couvre toutes les actions Docker nécessaires pour construire, tester, déployer et maintenir l'image du projet Sentiment Analysis Platform.