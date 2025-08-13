#!/bin/bash
# Script de déploiement container avec docker-compose et authentification Azure

set -e  # Arrêter le script en cas d'erreur

echo "=== DÉPLOIEMENT CONTAINER AZURE AVEC DOCKER-COMPOSE ==="

# Vérification de l'existence du fichier .env
if [ ! -f ".env" ]; then
    echo "Erreur: Fichier .env non trouvé"
    echo "Créez un fichier .env avec vos variables Azure"
    exit 1
fi

# Chargement des variables d'environnement depuis .env
echo "Chargement des variables depuis .env..."
source .env

# Vérification des variables requises
check_var() {
    if [ -z "${!1}" ]; then
        echo "Variable $1 manquante"
        return 1
    else
        echo "$1: définie"
        return 0
    fi
}

echo "Vérification des variables d'environnement..."
VARS_OK=true

check_var "AZ_CLIENT_ID" || VARS_OK=false
check_var "AZ_CLIENT_SECRET" || VARS_OK=false  
check_var "AZ_TENANT_ID" || VARS_OK=false
check_var "AZ_SUBSCRIPTION_ID" || VARS_OK=false

if [ "$VARS_OK" = false ]; then
    echo "Variables d'environnement manquantes"
    exit 1
fi

# BUILD ET PUSH DE L'IMAGE
echo ""
echo "=== BUILD ET PUSH DE L'IMAGE ==="

# Variables pour docker-compose
export IMAGE="docker.io/p4x639/p7-tweet-api"
export TAG="latest"

# Build avec docker-compose
echo "Build de l'image avec docker-compose (sans cache) ..."
docker-compose build --no-cache

# Vérifier que l'image est créée
echo "Vérification de l'image créée..."
if docker images | grep -q "p4x639/p7-tweet-api"; then
    echo "Image créée avec succès"
else
    echo "Erreur: Image non créée"
    exit 1
fi

# Lancement en local pour test (si besoin)
echo "# si besoin lancement en local"
echo "# ... (si besoin) lancement de : docker-compose up -d"

# Push vers Docker Hub
echo "Push vers Docker Hub..."
docker push p4x639/p7-tweet-api:latest

if [ $? -ne 0 ]; then
    echo "Erreur lors du push vers Docker Hub"
    exit 1
fi

echo "Image pushée avec succès !"

# CONNEXION AZURE
echo ""
echo "=== CONNEXION AZURE ==="

# Connexion Azure avec le service principal
echo "Connexion Azure avec le service principal..."
az login --service-principal \
    --username "$AZ_CLIENT_ID" \
    --password="$AZ_CLIENT_SECRET" \
    --tenant "$AZ_TENANT_ID" \
    --output none

if [ $? -ne 0 ]; then
    echo "Erreur de connexion Azure"
    exit 1
fi

# Définition de la souscription active
echo "Définition de la souscription active..."
az account set --subscription "$AZ_SUBSCRIPTION_ID"

# Vérification de la connexion
echo "Vérification de la connexion..."
CURRENT_SUBSCRIPTION=$(az account show --query name --output tsv)
echo "Souscription active: $CURRENT_SUBSCRIPTION"

# Vérification de l'état du provider
echo "Vérification du provider Microsoft.ContainerInstance..."
PROVIDER_STATE=$(az provider show --namespace Microsoft.ContainerInstance --query registrationState --output tsv)
echo "État du provider: $PROVIDER_STATE"

if [ "$PROVIDER_STATE" != "Registered" ]; then
    echo "Le provider n'est pas enregistré. Veuillez attendre que l'enregistrement précédent se termine."
    exit 1
fi

# DÉPLOIEMENT DU CONTAINER
echo ""
echo "=== DÉPLOIEMENT DU CONTAINER ==="

# Configuration du container
RESOURCE_GROUP="tweet-api-group"
CONTAINER_NAME="tweet-api-container"
IMAGE_NAME="p4x639/p7-tweet-api:latest"
LOCATION="francecentral"

echo "Configuration du déploiement:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Container Name: $CONTAINER_NAME"
echo "   Image: $IMAGE_NAME"
echo "   Location: $LOCATION"

# Vérification de l'existence du groupe de ressources
echo "Vérification du groupe de ressources..."
if ! az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    echo "Groupe de ressources '$RESOURCE_GROUP' non trouvé"
    exit 1
fi

# Suppression du container existant s'il existe
echo "Nettoyage des containers existants..."
if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" &>/dev/null; then
    echo "Arrêt du container existant..."
    az container stop --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" || true
    sleep 10
    
    echo "Suppression du container existant..."
    az container delete --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --yes
    
    echo "Vérification de la suppression..."
    while az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" &>/dev/null; do
        echo "Attente de la suppression complète..."
        sleep 10
    done
    echo "Container supprimé avec succès"
fi

# Déploiement du container avec les bonnes variables d'environnement
echo "Déploiement du container $CONTAINER_NAME..."
az container create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_NAME" \
    --image "$IMAGE_NAME" \
    --cpu 1 \
    --memory 1 \
    --os-type Linux \
    --restart-policy Always \
    --ip-address Public \
    --ports 8000 8050 \
    --environment-variables \
        'PYTHONUNBUFFERED=1' \
        'TF_ENABLE_ONEDNN_OPTS=0' \
        'ENVIRONMENT=production' \
    --location "$LOCATION"

if [ $? -eq 0 ]; then
    echo "Container créé avec succès !"
    
    # Récupération des informations du container
    echo "Récupération de l'IP publique..."
    sleep 5
    IP=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query ipAddress.ip --output tsv)
    
    if [ -n "$IP" ]; then
        echo ""
        echo "=== DÉPLOIEMENT TERMINÉ ==="
        echo "Votre API Tweet est accessible à:"
        echo "  - Documentation (FastAPI): http://$IP:8000"
        echo "  - Documentation (Swagger): http://$IP:8000/docs"
        echo "  - Interface API: http://$IP:8050"
        echo "  - Admin: http://$IP:8050/admin"
        echo ""
        echo "État du container:"
        az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "{Name:name,State:containers[0].instanceView.currentState.state,IP:ipAddress.ip}" --output table
    else
        echo "IP publique non encore assignée, vérifiez dans quelques minutes"
    fi
    
    echo ""
    echo "Commandes utiles:"
    echo "  - Logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    echo "  - Shell: az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command '/bin/bash'"
    echo "  - Redémarrer: az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
else
    echo "Erreur lors de la création du container"
    exit 1
fi

echo ""
echo "=== DÉPLOIEMENT TERMINÉ ==="
