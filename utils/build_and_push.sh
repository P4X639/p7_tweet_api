#!/bin/bash

# Script de build et push de l'image Docker pour Azure
# Usage: ./build_and_push.sh [tag]

set -e

# Variables de configuration
REGISTRY_NAME="your-registry.azurecr.io"  # À remplacer par votre registry Azure
IMAGE_NAME="sentiment-platform"
TAG=${1:-latest}
FULL_IMAGE_NAME="$REGISTRY_NAME/$IMAGE_NAME:$TAG"

echo " Construction de l'image Docker..."
docker build -t $FULL_IMAGE_NAME .

echo " Taille de l'image construite:"
docker images $FULL_IMAGE_NAME

echo " Test rapide de l'image..."
docker run --rm -d --name test-api -p 8001:8000 $FULL_IMAGE_NAME
sleep 10

# Vérification que l'API répond
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "[[X]] API fonctionne correctement"
else
    echo "[X] Erreur: API ne répond pas"
    docker logs test-api
    docker stop test-api
    exit 1
fi

docker stop test-api

echo " Push vers Azure Container Registry..."
echo "Assurez-vous d'être connecté avec: az acr login --name your-registry"

# Décommentez la ligne suivante après avoir configuré votre registry
# docker push $FULL_IMAGE_NAME

echo "[[X]] Image prête pour le déploiement sur Azure"
echo "Image: $FULL_IMAGE_NAME"

# Commandes pour déployer sur Azure Container Instances
echo ""
echo " Commandes pour déployer sur Azure Container Instances:"
echo "az container create \\"
echo "  --resource-group your-resource-group \\"
echo "  --name sentiment-platform \\"
echo "  --image $FULL_IMAGE_NAME \\"
echo "  --ports 80 \\"
echo "  --environment-variables PORT=80 DAGSHUB_USERNAME=dev.nono.stargate DAGSHUB_REPO=P7_tweet \\"
echo "  --cpu 1 --memory 2"