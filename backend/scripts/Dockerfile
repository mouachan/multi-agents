FROM python:3.11-slim
WORKDIR /scripts
COPY init_data.py .
COPY init_data/ ./init_data/
RUN pip install --no-cache-dir httpx psycopg2-binary reportlab mcp
CMD ["python", "init_data.py"]
