# Utilisation d'une image Python légère
FROM python:3.9-slim

# Définition du répertoire de travail
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Installation des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposition du port utilisé par Streamlit
EXPOSE 8501

# Commande pour lancer l'application Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
