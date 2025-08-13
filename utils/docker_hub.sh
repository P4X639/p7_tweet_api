# Identité / nommage
PROJECT_SLUG=p7-tweet-api
ENV=prod
LOCATION=francecentral

# Docker Hub
DOCKERHUB_USER=p4x639
IMAGE=docker.io/$DOCKERHUB_USER/$PROJECT_SLUG

# Azure
AZ_RG=rg-$PROJECT_SLUG-$ENV
AZ_LOGWS=log-$PROJECT_SLUG-$ENV
AZ_CAE=cae-$PROJECT_SLUG-$ENV
AZ_APP=app-$PROJECT_SLUG-$ENV

# Environnements
source ../.env

# Construire et pousser l’image sur Docker Hub
GIT_SHA=$(git rev-parse --short HEAD)
VERSION=0.1.0
TAG=${VERSION}-${GIT_SHA}

docker login -u $DOCKERHUB_USER
docker build -t $IMAGE:$TAG -t $IMAGE:latest .
docker push $IMAGE:$TAG
docker push $IMAGE:latest
