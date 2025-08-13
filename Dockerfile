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
    procps htop net-tools vim nano less lsof tcpdump bash tree \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copier le fichier des dépendances Python
COPY requirements.txt .

# Installation des packages Python
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copier les fichiers de l'application
COPY .env .
COPY main.py .
COPY assets/ ./assets/
COPY services/ ./services/
COPY utils/ ./utils/

# Répertoires de travail
RUN mkdir -p data models reports logs

# Exposer le port de l’API
EXPOSE 8000 8050

# Commande par défaut
CMD ["python", "main.py"]
