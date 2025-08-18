#!/bin/bash
# Déploiement Azure manuel - Partie Container seulement
# À utiliser quand GitHub Actions échoue sur le registry Docker

echo "=== DÉPLOIEMENT AZURE MANUEL ==="

# Chargement des variables depuis .env
if [ -f ".env" ]; then
    source .env
    echo "[✓] Variables chargées depuis .env"
else
    echo "[X] Fichier .env non trouvé"
    exit 1
fi

# Configuration du container (depuis votre .env)
RESOURCE_GROUP="$AZ_RESOURCE_GROUP"
CONTAINER_NAME="$AZ_CONTAINER" 
IMAGE_NAME="docker.io/p4x639/p7-tweet-api:latest"
LOCATION="$AZ_REGION"

echo "Configuration extraite de votre script :"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Container Name: $CONTAINER_NAME"
echo "   Image: $IMAGE_NAME"
echo "   Location: $LOCATION"

# CONNEXION AZURE (partie extraite de votre script)
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

# SUPPRESSION CONTAINER EXISTANT (partie extraite)
echo ""
echo "=== NETTOYAGE CONTAINER EXISTANT ==="

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
else
    echo "Aucun container existant trouvé"
fi

# DÉPLOIEMENT CONTAINER (partie extraite + variables DagsHub ajoutées)
echo ""
echo "=== DÉPLOIEMENT DU CONTAINER ==="

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
        'API_HOST=0.0.0.0' \
        'API_PORT=8000' \
        'DASH_PORT=8050' \
        "MODEL_RUN_ID=$MODEL_RUN_ID" \
        "DAGSHUB_TOKEN=$DAGSHUB_TOKEN" \
        "DAGSHUB_USERNAME=$DAGSHUB_USERNAME" \
        "DAGSHUB_REPO=$DAGSHUB_REPO" \
        "MLFLOW_TRACKING_URI=$MLFLOW_TRACKING_URI" \
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
        echo "  - Health check: http://$IP:8000/health"
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