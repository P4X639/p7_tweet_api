Synthèse du Déploiement Azure Container Instance
🎯 Objectif Atteint
Déploiement réussi d'une API FastAPI avec interface Dash sur Azure Container Instance, accessible via deux ports (8000 et 8050).
📋 Étapes Clés du Succès
1. Configuration de l'Authentification Azure

Création d'un service principal via az ad sp create-for-rbac
Configuration des variables d'environnement dans .env :

AZ_CLIENT_ID, AZ_CLIENT_SECRET, AZ_TENANT_ID, AZ_SUBSCRIPTION_ID


Test de connexion avec un script Python utilisant ClientSecretCredential

2. Préparation de l'Image Docker

Correction du Dockerfile : ajout de EXPOSE 8050 en plus du port 8000
Utilisation de docker-compose pour le build au lieu de docker build seul
Raison cruciale : docker-compose charge automatiquement le fichier .env, contrairement à docker build standalone

3. Résolution des Problèmes de Providers Azure

Enregistrement du provider Microsoft.ContainerInstance
Attente de l'activation avant déploiement (statut "Registered")

4. Gestion des Conflits de Déploiement

Arrêt propre des containers existants avant suppression
Vérification de suppression complète avant redéploiement
Gestion des erreurs de registre Docker Hub avec retry et délais d'attente

5. Configuration des Ports et Variables

Exposition des deux ports : 8000 (FastAPI) et 8050 (Dash)
Variables d'environnement de production dans Azure Container Instance
Résolution du problème de chargement des variables via load_dotenv()

6. Optimisation de la Documentation API

Masquage des endpoints de debug avec include_in_schema=False
Conservation de la fonctionnalité pour le développement

⚡ Points Critiques Identifiés
Différence Docker vs Docker-Compose

docker build : utilise uniquement le Dockerfile
docker-compose build : utilise Dockerfile + docker-compose.yml + .env
Impact : Les variables d'environnement ne sont chargées qu'avec docker-compose

Timing des Déploiements

Problème : Erreurs de registre Docker Hub lors de déploiements rapides
Solution : Délais d'attente et mécanismes de retry

Gestion des Services Multi-Ports

Défi : Démarrage de FastAPI (8000) et Dash (8050) dans le même container
Résolution : Configuration correcte des ports exposés et variables d'environnement

🛠️ Outils et Technologies Utilisés

Azure CLI pour l'authentification et le déploiement
Docker & Docker-Compose pour la containerisation
Azure Container Instance comme plateforme de déploiement
FastAPI + Pydantic pour l'API REST
Python dotenv pour la gestion des variables d'environnement

📊 Résultat Final

✅ API accessible sur http://IP:8000 (documentation Swagger)
✅ Interface Dash sur http://IP:8050
✅ Déploiement automatisé via script bash
✅ Authentification Azure sécurisée
✅ Gestion robuste des erreurs et retry

🔑 Apprentissages Clés

Docker-compose est essentiel pour les projets avec variables d'environnement
Les délais d'attente sont cruciaux pour la stabilité des déploiements
La gestion des providers Azure doit être vérifiée avant déploiement
Les services multi-ports nécessitent une configuration précise des expositions
RéessayerClaude peut faire des erreurs. Assurez-vous de vérifier ses réponses.Recherche Sonnet 4