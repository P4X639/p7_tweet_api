# Commande de lancement de la creation de l'image avec les info git
# Executée depuis WLS
# python3 utils/git_last_push_info.py > version_info.json && docker-compose build --no-cache && docker-compose up -d

# Base image compatible TensorFlow 2.15.0 + Python 3.10
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Variables d’environnement recommandées
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl git \
    procps htop net-tools vim nano less lsof tcpdump bash tree wget ngrep jq\
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copier le fichier des dépendances Python
COPY requirements.txt .

# Installation des packages Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copier les fichiers de l'application
COPY .env .
COPY main.py .
COPY assets/ ./assets/
COPY services/ ./services/
COPY utils/ ./utils/
COPY tests/ ./tests/
COPY version_info.json .
#COPY start.sh /app/start.sh
#COPY api-restart.sh /app/api-restart.sh
#COPY api-status.sh  /app/api-status.sh
#COPY api-stop.sh /app/api-stop.sh
#RUN chmod +x /app/*.sh

RUN mkdir -p data models reports log

# Exposer le port de l’API
EXPOSE 8000 8050

# Commande par défaut
CMD ["python", "main.py"]
#CMD ["/app/start.sh"]

