FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /scripts
COPY init_data.py .
COPY init_data/ ./init_data/
RUN pip install --no-cache-dir httpx httpx-sse psycopg2-binary "mcp[cli]>=1.8.0"
CMD ["python", "init_data.py"]
