#!/bin/bash
# Script de build et push - SIMPLE

echo "=== BUILD ET PUSH AVEC DOCKER-COMPOSE ==="

# Build avec docker-compose (utilise TOUT le docker-compose.yml)
echo "Build de l'image avec docker-compose..."
docker-compose build

# Push vers Docker Hub
echo "Push vers Docker Hub..."
docker push p4x639/p7-tweet-api:latest

echo "✅ Terminé !"
