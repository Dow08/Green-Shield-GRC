# ------------------------------------------------------------------
# Auditor_App — l'outil GRC (Python / Streamlit)
# ------------------------------------------------------------------
FROM python:3.12-slim

# Bonnes pratiques Python en conteneur.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances d'abord (cache de couche Docker).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code applicatif + référentiel + thème.
COPY . .

# Exécution en utilisateur non-root (durcissement).
RUN useradd --create-home --uid 10001 auditor && chown -R auditor:auditor /app
USER auditor

EXPOSE 8501

# Healthcheck : l'endpoint interne de Streamlit.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"

CMD ["streamlit", "run", "app.py"]
