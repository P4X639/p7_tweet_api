# Script de validation complete de la configuration GitHub Actions
# A executer avant le premier push pour s'assurer que tout est correct

echo "=== VALIDATION CONFIGURATION GITHUB ACTIONS ==="

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
echo "VERIFICATION DE LA STRUCTURE DE PROJET"
echo "============================================="

# Verification des fichiers essentiels
check_item $([ -f "Dockerfile" ] && echo 0 || echo 1) "Dockerfile present"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -f "docker-compose.yml" ] && echo 0 || echo 1) "docker-compose.yml present"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -f ".env" ] && echo 0 || echo 1) "Fichier .env present"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -f ".gitignore" ] && echo 0 || echo 1) "Fichier .gitignore present"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -d ".github/workflows" ] && echo 0 || echo 1) "Dossier .github/workflows cree"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -f ".github/workflows/deploy-api.yml" ] && echo 0 || echo 1) "Workflow deploy-api.yml present"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

echo ""
echo "VERIFICATION DES OUTILS LOCAUX"
echo "=================================="

# Verification des outils requis
check_item $(command -v git >/dev/null 2>&1 && echo 0 || echo 1) "Git installe"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $(command -v docker >/dev/null 2>&1 && echo 0 || echo 1) "Docker installe"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $(command -v docker-compose >/dev/null 2>&1 && echo 0 || echo 1) "Docker-compose installe"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $(command -v az >/dev/null 2>&1 && echo 0 || echo 1) "Azure CLI installe"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $(command -v curl >/dev/null 2>&1 && echo 0 || echo 1) "Curl installe"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

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

# Variables Docker Hub
check_item $([ -n "$DOCKERHUB_USER" ] && echo 0 || echo 1) "DOCKERHUB_USER defini (${DOCKERHUB_USER})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$DOCKERHUB_TOKEN" ] && echo 0 || echo 1) "DOCKERHUB_TOKEN defini (${DOCKERHUB_TOKEN})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

# Variables du projet
check_item $([ -n "$PROJECT_SLUG" ] && echo 0 || echo 1) "PROJECT_SLUG defini (${PROJECT_SLUG})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$AZ_RESOURCE_GROUP" ] && echo 0 || echo 1) "AZ_RESOURCE_GROUP defini (${AZ_RESOURCE_GROUP})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$AZ_CONTAINER" ] && echo 0 || echo 1) "AZ_CONTAINER defini (${AZ_CONTAINER})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

echo ""
echo "TEST DE BUILD DOCKER LOCAL"
echo "============================="

# Test de build sans cache
echo "[-] Test de build Docker (cela peut prendre quelques minutes)..."
if docker-compose build --no-cache >/dev/null 2>&1; then
    check_item 0 "Build Docker reussie"
else
    check_item 1 "Build Docker echouee"
    ERRORS=$((ERRORS+1))
    warn_item "Verifiez votre Dockerfile et docker-compose.yml"
fi

echo ""
echo "TEST CONNEXION AZURE"
echo "======================="

echo "[-] Test de connexion Azure avec service principal..."

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

echo ""
echo "VERIFICATION ENDPOINT HEALTH"
echo "==============================="

# Verification qu'un endpoint health existe dans le code de l'API
grep "/health" main.py > /dev/null 2>&1
if [ $? -ne 0 ]; then
    check_item 1 "Endpoint /health non trouvé"
else
	check_item 0 "Endpoint /health trouvé"
fi

echo ""
echo "VERIFICATION DU WORKFLOW"
echo "==========================="

if [ -f ".github/workflows/deploy-api.yml" ]; then
    # Verifications basiques du workflow
    if grep -q "DOCKERHUB_USER" .github/workflows/deploy-api.yml; then
        check_item 0 "Secrets Docker configures dans le workflow"
    else
        check_item 1 "Secrets Docker manquants dans le workflow"
        ERRORS=$((ERRORS+1))
    fi
    
    if grep -q "AZ_CLIENT_ID" .github/workflows/deploy-api.yml; then
        check_item 0 "Secrets Azure configures dans le workflow"
    else
        check_item 1 "Secrets Azure manquants dans le workflow"
        ERRORS=$((ERRORS+1))
    fi
    
    if grep -q "paths:" .github/workflows/deploy-api.yml; then
        check_item 0 "Declencheurs conditionnels configures"
    else
        warn_item "Declencheurs non conditionnels - le workflow se lancera a chaque push"
    fi
    
    # Verification des variables specifiques au projet
    if grep -q "$PROJECT_SLUG" .github/workflows/deploy-api.yml; then
        check_item 0 "Variables du projet configurees dans le workflow"
    else
        check_item 1 "Variables du projet manquantes dans le workflow"
        ERRORS=$((ERRORS+1))
    fi
else
    echo "[X] Fichier workflow non trouve"
    ERRORS=$((ERRORS+1))
fi

echo ""
echo "VERIFICATION DES PORTS"
echo "======================="

check_item $([ -n "$API_PORT" ] && echo 0 || echo 1) "API_PORT defini (${API_PORT})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$DASH_PORT" ] && echo 0 || echo 1) "DASH_PORT defini (${DASH_PORT})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

check_item $([ -n "$API_HOST" ] && echo 0 || echo 1) "API_HOST defini (${API_HOST})"
[ $? -ne 0 ] && ERRORS=$((ERRORS+1))

echo ""
echo "RECAPITULATIF"
echo "================"

if [ $ERRORS -eq 0 ]; then
    echo "[✓] VALIDATION REUSSIE !"
    echo ""
    echo "[✓] Votre configuration GitHub Actions est prete"
    echo "[✓] Vous pouvez committer et pousser en toute securite"
    echo ""
    echo "ETAPES SUIVANTES:"
    echo "1. [-] Configurez les secrets sur GitHub (si pas deja fait)"
    echo "2. [-] Committez et poussez:"
    echo "   git add ."
    echo "   git commit -m 'Add complete CI/CD pipeline'"
    echo "   git push origin main"
    echo "3. [-] Surveillez l'execution sur GitHub Actions"
    echo ""
    echo "URL de suivi: https://github.com/${GITHUB_USER}/${GITHUB_REPO}/actions"
    
else
    echo "[X] VALIDATION ECHOUEE - $ERRORS erreur(s) trouvee(s)"
    echo ""
    echo "ACTIONS REQUISES:"
    echo "- Corrigez les erreurs listees ci-dessus"
    echo "- Relancez ce script: ./validate_github_setup.sh"
    echo "- Ne poussez PAS vers GitHub avant que toutes les verifications passent"
    echo ""
    echo "AIDE:"
    echo "- Consultez la documentation dans deployment_guide.md"
    echo "- Verifiez votre fichier .env"
    echo "- Testez la connexion Azure manuellement"
fi

echo ""
echo "STATISTIQUES:"
echo "- Verifications totales: $(grep -c "check_item" $0)"
echo "- Erreurs trouvees: $ERRORS"
echo "- Taux de reussite: $(( ($(grep -c "check_item" $0) - $ERRORS) * 100 / $(grep -c "check_item" $0) ))%"
echo ""

echo "CONFIGURATION DETECTEE:"
echo "- Projet: ${PROJECT_SLUG}"
echo "- Environnement: ${ENV}"
echo "- Docker Hub: ${DOCKERHUB_USER}/${PROJECT_SLUG}"
echo "- Azure RG: ${AZ_RG}"
echo "- Container: ${AZ_APP}"
echo "- Ports: ${API_PORT}, ${DASH_PORT}"

exit $ERRORS