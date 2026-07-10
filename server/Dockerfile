FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libgeos for shapely (WKB decoding of PostGIS geographies in the CDC normalizer)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgeos-c1v5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

EXPOSE 8000

# Default command runs the API; workers override with e.g.
#   command: python -m workers.projector
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
