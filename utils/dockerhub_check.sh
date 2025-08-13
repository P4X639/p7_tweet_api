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

TAG_PROBE="check-$(date +%Y%m%d%H%M%S)"

echo "Repository cible : ${IMAGE}"
echo "Tag de test      : ${TAG_PROBE}"
echo

# --- Login Docker Hub ---------------------------------------------------------
if [ -n "${DOCKERHUB_TOKEN}" ]; then
  printf '%s' "${DOCKERHUB_TOKEN}" | docker login -u "${DOCKERHUB_USER}" --password-stdin
else
  echo "Info: DOCKERHUB_TOKEN non défini, passage en login interactif."
  docker login -u "${DOCKERHUB_USER}"
fi

# --- Crée et pousse une image de test ultra-légère ----------------------------
# Option 1 : re-tagger hello-world (le plus simple et le plus petit)
docker pull hello-world:latest >/dev/null
docker tag hello-world:latest "${IMAGE}:${TAG_PROBE}"
docker push "${IMAGE}:${TAG_PROBE}"

# --- Vérification côté Hub ----------------------------------------------------
if docker manifest inspect "${IMAGE}:${TAG_PROBE}" >/dev/null 2>&1; then
  echo "✓ Docker Hub prêt : le tag ${IMAGE}:${TAG_PROBE} est accessible."
else
  echo "✗ Échec de vérification du manifest. Vérifie droits/visibilité du repo." >&2
  exit 1
fi

