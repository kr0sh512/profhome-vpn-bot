FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py ./
COPY vpn_bot ./vpn_bot

RUN mkdir -p /app/data

CMD ["python", "bot.py", "--config", "/app/config.toml"]
