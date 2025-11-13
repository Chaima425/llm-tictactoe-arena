# Étape 1 : utiliser une image Python officielle
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements et installer les dépendances
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code dans le conteneur
COPY . .

# Exposer le port sur lequel l'application tourne
EXPOSE 8000 8080

# Commande pour lancer l'app
# puisque le NiceGUI est lancé depuis main.py
CMD ["python", "main.py"]