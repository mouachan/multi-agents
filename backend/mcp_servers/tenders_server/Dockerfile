# MCP Tenders Server Dockerfile - CRUD operations on tenders (Appels d'Offres)
FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0

WORKDIR /app

# Copy requirements
COPY tenders_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities and server code
COPY shared/ ./shared/
COPY tenders_server/server.py .

RUN chmod -R 755 /app

USER 1001

EXPOSE 8080

# Start MCP server with FastMCP SDK
CMD ["python", "server.py"]
