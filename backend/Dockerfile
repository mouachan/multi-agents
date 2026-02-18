# =============================================================================
# Claims Processing Backend - Dockerfile (Red Hat UBI9)
# =============================================================================

FROM registry.access.redhat.com/ubi9/python-312:latest

# Labels
LABEL maintainer="Claims Demo Team" \
      description="Claims Processing Backend API" \
      version="1.0.0"

# Switch to root for package installation
USER 0

# Install PostgreSQL client libraries
RUN dnf install -y --nodocs postgresql-devel && \
    dnf clean all && \
    rm -rf /var/cache/dnf

WORKDIR /opt/app-root/src

# Copy and install Python dependencies (as root for permissions)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Fix permissions and switch to default user
RUN chown -R 1001:0 /opt/app-root && \
    chmod -R g=u /opt/app-root

USER 1001

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/app-root/src \
    PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]