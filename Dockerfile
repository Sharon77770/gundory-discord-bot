FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

RUN useradd --create-home --uid 10001 briar \
    && mkdir -p /data \
    && chown -R briar:briar /app /data
USER briar

CMD ["sh", "-c", "alembic upgrade head && exec python -m app.main"]

