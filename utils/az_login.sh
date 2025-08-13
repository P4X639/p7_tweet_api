
#!/bin/bash

echo "=== VALIDATION LOGIN AZURE ==="

# Chargement des variables depuis .env
if [ -f ".env" ]; then
    source .env
    echo "[✓] Variables chargees depuis .env"
else
    echo "[X] Fichier .env non trouve"
    exit 1
fi

ERRORS=0

# Fonction de verification
check_item() {
    if [ $1 -eq 0 ]; then
        echo "[✓] $2"
        return 0
    else
        echo "[X] $2"
        return 1
    fi
}

warn_item() {
    echo "[!] $1"
}

echo ""
echo "VERIFICATION DU CONTENU .ENV"
echo "==============================="

# Variables Azure
check_item $([ -n "$AZ_CLIENT_ID" ] && echo 0 || echo 1) "AZ_CLIENT_ID defini (${AZ_CLIENT_ID})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$AZ_CLIENT_SECRET" ] && echo 0 || echo 1) "AZ_CLIENT_SECRET defini (${AZ_CLIENT_SECRET})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$AZ_TENANT_ID" ] && echo 0 || echo 1) "AZ_TENANT_ID defini (${AZ_TENANT_ID})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$AZ_SUBSCRIPTION_ID" ] && echo 0 || echo 1) "AZ_SUBSCRIPTION_ID defini (${AZ_SUBSCRIPTION_ID})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$AZ_RG" ] && echo 0 || echo 1) "AZ_RG defini (${AZ_RG})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$AZ_APP" ] && echo 0 || echo 1) "AZ_APP defini (${AZ_APP})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

echo "Test 1 : de connexion Azure avec service principal..."

if az login --service-principal \
    --username "$AZ_CLIENT_ID" \
    --password="$AZ_CLIENT_SECRET" \
    --tenant "$AZ_TENANT_ID" \
    --output none >/dev/null 2>&1; then
    
    check_item 0 "Connexion Azure reussie"
    
    # Test de definition de subscription
    if az account set --subscription "$AZ_SUBSCRIPTION_ID" >/dev/null 2>&1; then
        check_item 0 "Subscription Azure definie"
        
        # Verification du resource group
        if az group show --name "$AZ_RG" >/dev/null 2>&1; then
            check_item 0 "Resource Group existe (${AZ_RG})"
        else
            check_item 1 "Resource Group '${AZ_RG}' non trouve"
            warn_item "Creez le resource group ou modifiez le nom dans le workflow"
            warn_item "Commande: az group create --name ${AZ_RG} --location ${LOCATION}"
            ERRORS=$((ERRORS+1))
        fi
    else
        check_item 1 "Impossible de definir la subscription"
        ERRORS=$((ERRORS+1))
    fi
else
    check_item 1 "Connexion Azure echouee"
    warn_item "Verifiez vos credentials Azure dans .env"
    ERRORS=$((ERRORS+1))
fi



echo "Test 2 : de connexion Azure avec service principal..."
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
else
    echo "Connexion Azure réussie"
fi
