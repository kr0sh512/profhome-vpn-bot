FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py ./
COPY vpn_bot ./vpn_bot

RUN useradd --create-home --uid 10001 botuser \
    && mkdir -p /app/data \
    && chown -R botuser:botuser /app

USER botuser

CMD ["python", "bot.py", "--config", "/app/config.toml"]
