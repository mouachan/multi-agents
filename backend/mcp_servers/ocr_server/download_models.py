"""
Pre-download EasyOCR models during Docker build.
This avoids downloading models on every container startup.
"""
import os
import easyocr

# Set model storage directory
os.environ['EASYOCR_MODULE_PATH'] = '/app/models'

# Languages to download (en, fr)
LANGUAGES = os.getenv("OCR_LANGUAGES", "en,fr").split(",")

print(f"Downloading EasyOCR models for languages: {LANGUAGES}")
print(f"Models will be stored in: /app/models")

# Initialize reader with GPU=False (build time, no GPU)
# This will download the models
reader = easyocr.Reader(LANGUAGES, gpu=False)

print(f"✅ EasyOCR models downloaded successfully")
print(f"Models location: {os.environ['EASYOCR_MODULE_PATH']}")
