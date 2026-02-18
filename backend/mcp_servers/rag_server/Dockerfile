# MCP RAG Server Dockerfile - Centralized via LlamaStack
# No direct DB access - everything via LlamaStack APIs
FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy consolidated server code (all in server.py)
COPY server.py .

RUN chmod -R 755 /app

USER 1001

EXPOSE 8080

# Start MCP server with FastMCP SDK
CMD ["python", "server.py"]
