# MCP OCR Server Dockerfile - Vision LLM OCR (Qwen2.5-VL-7B via LlamaStack)
FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0

# Install system dependencies for PDF processing
# - poppler-utils: PDF to image conversion (pdf2image dependency)
RUN dnf install -y \
    poppler-utils \
    && dnf clean all

# Note: OCR is done by Qwen2.5-VL-7B via remote LlamaStack inference API.
# This container only handles PDF→image conversion and API calls.
# Memory footprint: ~100MB (vs ~2GB with EasyOCR/PyTorch)

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Fix permissions for OpenShift
RUN chgrp -R 0 /app && \
    chmod -R g=u /app

USER 1001

EXPOSE 8080

CMD ["python", "server.py"]
