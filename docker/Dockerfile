FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/ data/
COPY policies/ policies/
COPY scripts/ scripts/

ENV PYTHONPATH=/app/src
ENV FACTOR_ENV=production
ENV FACTOR_KNOWLEDGE_PATH=/app/data/chroma

EXPOSE 8000

CMD ["uvicorn", "factor.app:app", "--host", "0.0.0.0", "--port", "8000"]
