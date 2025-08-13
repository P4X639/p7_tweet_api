#!/usr/bin/env bash 
set -Eeuo pipefail

# --- Paramètres (surclassables par .env) ----------
PROJECT_SLUG="${PROJECT_SLUG:-p7-tweet-api}"
DOCKERHUB_USER="${DOCKERHUB_USER:-p4x639}"
DOCKERHUB_TOKEN="${DOCKERHUB_TOKEN:-}"  # si vide, login interactif
IMAGE="${IMAGE:-docker.io/${DOCKERHUB_USER}/${PROJECT_SLUG}}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# -----------------------------------------------------------------------------
# Publish images to Docker Hub using docker-compose/docker compose
# Builds with compose, pushes ${IMAGE}:${TAG} + ${IMAGE}:latest
# -----------------------------------------------------------------------------

# Detect compose command (v2 'docker compose' preferred, fallback to 'docker-compose')
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif docker-compose version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "Erreur: Docker Compose n'est pas installé (ni 'docker compose' ni 'docker-compose')." >&2
  exit 1
fi

# ------------------------ User-provided defaults (overridable) ----------------
PROJECT_SLUG="${PROJECT_SLUG:-p7-tweet-api}"
ENV="${ENV:-prod}"
LOCATION="${LOCATION:-francecentral}"

DOCKERHUB_USER="${DOCKERHUB_USER:-p4x639}"
DOCKERHUB_TOKEN="${DOCKERHUB_TOKEN:-}"     # Laisse vide pour login interactif
IMAGE="${IMAGE:-docker.io/${DOCKERHUB_USER}/${PROJECT_SLUG}}"

AZ_RG="${AZ_RG:-rg-${PROJECT_SLUG}-${ENV}}"
AZ_LOGWS="${AZ_LOGWS:-log-${PROJECT_SLUG}-${ENV}}"
AZ_CAE="${AZ_CAE:-cae-${PROJECT_SLUG}-${ENV}}"
AZ_APP="${AZ_APP:-app-${PROJECT_SLUG}-${ENV}}"

# Versioning (TAG = VERSION-GIT_SHA)
GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo nogit)"
VERSION="${VERSION:-0.1.0}"
TAG="${TAG:-${VERSION}-${GIT_SHA}}"

export IMAGE TAG

# ------------------------------ Pre-flight checks -----------------------------
if [ ! -f "docker-compose.yml" ] && [ ! -f "compose.yml" ]; then
  echo "Erreur: aucun docker-compose.yml/compose.yml trouvé dans le répertoire courant." >&2
  exit 1
fi

echo ">>> Projet      : ${PROJECT_SLUG}"
echo ">>> Registry    : ${IMAGE}"
echo ">>> Tag build   : ${TAG}"
echo ">>> Tag latest  : latest"
echo ">>> Compose     : $COMPOSE"
echo

# ------------------------------- Docker login ---------------------------------
if [ -n "${DOCKERHUB_TOKEN}" ]; then
  printf '%s' "${DOCKERHUB_TOKEN}" | docker login -u "${DOCKERHUB_USER}" --password-stdin
else
  echo "Info: DOCKERHUB_TOKEN non défini, passage en login interactif Docker Hub."
  docker login -u "${DOCKERHUB_USER}"
fi

# ------------------------------- Build images ---------------------------------
# On suppose que le compose définit 'image: ${IMAGE}:${TAG}' pour le/les services à pousser.
# Exemple:
# services:
#   api:
#     build:
#       context: .
#       dockerfile: Dockerfile
#     image: ${IMAGE}:${TAG}
#
echo ">>> Build compose (sans cache)…"
$COMPOSE build --no-cache

# ------------------------------- Push images ----------------------------------
# 1) Tentative de push via compose (pousse ce qui est référencé par 'image:')
set +e
$COMPOSE push
COMPOSE_PUSH_RC=$?
set -e

if [ $COMPOSE_PUSH_RC -ne 0 ]; then
  echo "Avertissement: '$COMPOSE push' a échoué (probablement pas de champ 'image:' explicite)."
  echo "On retague l'image buildée vers '${IMAGE}:${TAG}' puis on pousse manuellement."

  # Récupère l'ID de la première image buildée par compose et la retague
  FIRST_IMG_ID="$($COMPOSE images -q | head -n 1)"
  if [ -z "${FIRST_IMG_ID}" ]; then
    echo "Erreur: impossible de récupérer l'image buildée. Vérifie le compose." >&2
    exit 1
  fi

  docker tag "${FIRST_IMG_ID}" "${IMAGE}:${TAG}"
  docker push "${IMAGE}:${TAG}"
fi

# 2) Tag + push 'latest'
echo ">>> Tag 'latest' et push…"
docker tag "${IMAGE}:${TAG}" "${IMAGE}:latest"
docker push "${IMAGE}:latest"

# ------------------------------- Summary --------------------------------------
DIGEST_TAG="$(docker inspect --format='{{index .RepoDigests 0}}' "${IMAGE}:${TAG}" || true)"
DIGEST_LATEST="$(docker inspect --format='{{index .RepoDigests 0}}' "${IMAGE}:latest" || true)"

echo
echo "✓ Push terminé."
echo "  - ${IMAGE}:${TAG}    => ${DIGEST_TAG:-(digest indisponible)}"
echo "  - ${IMAGE}:latest    => ${DIGEST_LATEST:-(digest indisponible)}"
echo
echo "Prochaines étapes:"
echo "  - Smoke test: docker run --rm -p 8080:8080 ${IMAGE}:${TAG}"
echo "  - Déploiement Azure: utiliser ACI/App Service/Container Apps (script séparé)."
