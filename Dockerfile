# Render/Railway default build: repo-root Dockerfile mirroring backend/Dockerfile.
# Local compose keeps using backend/Dockerfile; both install the same pinned stack.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app
WORKDIR /srv
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/migrations ./migrations
RUN chown -R app:app /srv
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["sh", "-c", "test -n \"$DATABASE_URL\" || (echo 'FATAL: DATABASE_URL is not set; configure it in the host secret manager' >&2; exit 1); python -c \"from app.migrate import migrate; import os; print(migrate(os.environ['DATABASE_URL']))\" && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
