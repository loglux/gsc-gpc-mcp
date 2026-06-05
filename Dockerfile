FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY shared/ ./shared/
COPY gsc/ ./gsc/
COPY gpc/ ./gpc/

# credentials/ is mounted at runtime — never baked into the image
VOLUME ["/app/credentials"]

# SERVER=gsc or SERVER=gpc, PORT is set per-service in docker-compose
ENV PORT=8000
CMD ["sh", "-c", "python -m ${SERVER}.server"]
