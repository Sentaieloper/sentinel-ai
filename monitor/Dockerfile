FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_VERSION=20

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY drift_reader/package.json drift_reader/package-lock.json drift_reader/
RUN cd drift_reader && npm ci --omit=dev

COPY chain_reader/package.json chain_reader/package-lock.json chain_reader/
RUN cd chain_reader && npm ci --omit=dev

COPY . .

CMD ["python", "start.py"]
