FROM python:3.11-slim

# System vorbereiten
RUN apt-get update && apt-get install -y gcc libffi-dev python3-dev

# Arbeitsverzeichnis setzen
WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App kopieren
COPY . .

# Port freigeben & Startbefehl setzen
EXPOSE 881
CMD ["python", "wecker.py"]
