# MCP OCR Server Dockerfile - EasyOCR with GPU Support
FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0

# Install system dependencies for EasyOCR, PDF processing, and CUDA
# - poppler-utils: PDF to image conversion (pdf2image dependency)
# - mesa-libGL: OpenGL library for OpenCV (EasyOCR dependency)
# - libgomp: OpenMP library for parallel processing
RUN dnf install -y \
    poppler-utils \
    mesa-libGL \
    libgomp \
    && dnf clean all

# Note: EasyOCR is embedded - all OCR processing happens in this container
# With GPU: 2-4s per page | Without GPU: 40-50s per page

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
# CRITICAL: Uninstall any pre-existing NumPy to prevent version conflicts
# The base UBI9 Python image may have NumPy 2.x which is incompatible with PyTorch/OpenCV
RUN pip uninstall -y numpy || true

# Install PyTorch with CUDA support (CUDA 11.8 for broad compatibility)
# This allows GPU acceleration when nvidia.com/gpu is available
RUN pip install --no-cache-dir \
    torch==2.2.0 \
    torchvision==0.17.0 \
    --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies (excluding torch/torchvision already installed)
# hadolint ignore=SC2261
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    starlette \
    Pillow==9.5.0 \
    pdf2image==1.17.0 \
    httpx>=0.27.0 \
    pydantic>=2.7.2 \
    python-multipart>=0.0.9 \
    easyocr==1.7.0 \
    opencv-python-headless==4.8.1.78 \
    "numpy>=1.21.0,<2.0.0" \
    "mcp[cli]>=1.8.0" \
  && mkdir -p /app/models

# Pre-download EasyOCR models during build to avoid downloading at runtime
COPY download_models.py .
ENV EASYOCR_MODULE_PATH=/app/models
RUN python download_models.py

# Copy consolidated server code (all in server.py)
COPY server.py .

# Fix permissions for OpenShift
RUN chgrp -R 0 /app && \
    chmod -R g=u /app

USER 1001

EXPOSE 8080

# Start MCP server with python (includes EasyOCR pre-initialization + uvicorn)
CMD ["python", "server.py"]
