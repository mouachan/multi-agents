FROM registry.access.redhat.com/ubi9/python-311:latest
USER 0
WORKDIR /app
COPY tracking_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY tracking_server/server.py .
RUN chmod -R 755 /app
USER 1001
EXPOSE 8080
CMD ["python", "server.py"]
