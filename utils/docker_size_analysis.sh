#!/bin/bash
# Script d'analyse de la taille d'image Docker

echo "=== ANALYSE DE LA TAILLE IMAGE DOCKER ==="

IMAGE_NAME="p4x639/p7-tweet-api:latest"

# Vérification que l'image existe localement
echo "Vérification de la présence locale de l'image..."
if ! docker images | grep -q "p4x639/p7-tweet-api"; then
    echo "[!] Image non trouvée localement, téléchargement..."
    docker pull $IMAGE_NAME
fi

echo ""
echo "=== INFORMATIONS GÉNÉRALES ==="

# Taille totale de l'image
echo "Taille de l'image :"
docker images $IMAGE_NAME --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"

echo ""
echo "=== ANALYSE DES COUCHES (LAYERS) ==="

# Historique des couches avec leurs tailles
echo "Historique des couches Docker :"
docker history $IMAGE_NAME --format "table {{.CreatedBy}}\t{{.Size}}" --no-trunc

echo ""
echo "=== ANALYSE DÉTAILLÉE DES COUCHES ==="

# Historique avec plus de détails
echo "Couches avec commandes complètes :"
docker history $IMAGE_NAME --no-trunc

echo ""
echo "=== ANALYSE DU CONTENU DE L'IMAGE ==="

# Lancer un container temporaire pour analyser le contenu
echo "Analyse du contenu du système de fichiers..."
CONTAINER_ID=$(docker run -d $IMAGE_NAME sleep 60)

if [ $? -eq 0 ]; then
    echo "Container temporaire créé : $CONTAINER_ID"
    
    # Analyse des dossiers les plus volumineux
    echo ""
    echo "Top 20 des dossiers les plus volumineux :"
    docker exec $CONTAINER_ID du -sh /* 2>/dev/null | sort -hr | head -20
    
    echo ""
    echo "Analyse détaillée des dossiers Python :"
    docker exec $CONTAINER_ID find /usr/local/lib/python* -type d -name "*" -exec du -sh {} \; 2>/dev/null | sort -hr | head -10
    
    echo ""
    echo "Cache pip (si présent) :"
    docker exec $CONTAINER_ID du -sh /root/.cache 2>/dev/null || echo "Pas de cache pip trouvé"
    
    echo ""
    echo "Packages Python installés (les plus volumineux) :"
    docker exec $CONTAINER_ID find /usr/local/lib/python* -name "site-packages" -exec du -sh {}/* \; 2>/dev/null | sort -hr | head -15
    
    echo ""
    echo "Fichiers temporaires :"
    docker exec $CONTAINER_ID find /tmp -type f -exec du -sh {} \; 2>/dev/null | sort -hr | head -10
    
    echo ""
    echo "Logs et fichiers volumineux :"
    docker exec $CONTAINER_ID find / -type f -size +50M -exec du -sh {} \; 2>/dev/null | sort -hr
    
    echo ""
    echo "Analyse des modèles ML (si présents) :"
    docker exec $CONTAINER_ID find / -name "*.h5" -o -name "*.pkl" -o -name "*.bin" -o -name "*.pt" -o -name "*.pth" 2>/dev/null | while read file; do
        docker exec $CONTAINER_ID du -sh "$file" 2>/dev/null
    done | sort -hr
    
    # Nettoyage
    echo ""
    echo "Arrêt du container temporaire..."
    docker stop $CONTAINER_ID >/dev/null
    docker rm $CONTAINER_ID >/dev/null
    echo "Container temporaire supprimé"
    
else
    echo "[X] Impossible de créer un container temporaire pour l'analyse"
fi

echo ""
echo "=== COMPARAISON AVEC IMAGE DE BASE ==="

# Essayer d'identifier l'image de base
BASE_IMAGE=$(docker history $IMAGE_NAME --no-trunc | tail -1 | awk '{print $1}')
echo "ID de l'image de base probable : $BASE_IMAGE"

# Comparaison des tailles
echo ""
echo "Comparaison des tailles :"
echo "Image finale  : $(docker images $IMAGE_NAME --format '{{.Size}}')"
echo "Couches ajoutées : Calculez la différence avec l'image de base"

echo ""
echo "=== RECOMMANDATIONS D'OPTIMISATION ==="

echo ""
echo "ACTIONS RECOMMANDÉES POUR RÉDUIRE LA TAILLE :"
echo ""
echo "1. NETTOYAGE DES CACHES :"
echo "   - Supprimer le cache pip : RUN pip install ... && rm -rf /root/.cache"
echo "   - Nettoyer apt cache : RUN apt-get clean && rm -rf /var/lib/apt/lists/*"
echo ""
echo "2. MULTI-STAGE BUILD :"
echo "   - Utiliser une image de build séparée pour compiler"
echo "   - Copier seulement les artefacts nécessaires dans l'image finale"
echo ""
echo "3. OPTIMISATION DES DÉPENDANCES :"
echo "   - Installer seulement les packages nécessaires"
echo "   - Utiliser des wheels pré-compilés"
echo "   - Éviter les outils de développement dans l'image finale"
echo ""
echo "4. IMAGE DE BASE PLUS LÉGÈRE :"
echo "   - Passer de ubuntu à python:slim ou alpine"
echo "   - Utiliser des images distroless pour la production"
echo ""
echo "5. OPTIMISATION SPÉCIFIQUE ML :"
echo "   - Utiliser des modèles pré-entraînés plus petits"
echo "   - Compresser les modèles (.h5, .pkl)"
echo "   - Charger les modèles depuis un stockage externe"

echo ""
echo "=== TAILLE CIBLE RECOMMANDÉE ==="
echo "Pour Azure Container Instance :"
echo "- Taille optimale : < 1 GB"
echo "- Taille acceptable : < 2 GB" 
echo "- Taille actuelle : ~10 GB (TROP VOLUMINEUX)"
echo ""
echo "Objectif : Réduire de 80-90% la taille actuelle"