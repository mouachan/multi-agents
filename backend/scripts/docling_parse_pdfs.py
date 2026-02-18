#!/usr/bin/env python3
"""
Parse PDFs using Docling and update claim_documents with extracted text.

Docling is IBM's advanced document parsing library that extracts structured
content from PDFs with better accuracy than traditional OCR.
"""

import logging
import os
import sys
from pathlib import Path

from docling.document_converter import DocumentConverter
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgresql.claims-demo.svc.cluster.local")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PDF_DIR = os.getenv("PDF_DIR", "/pdfs")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


def parse_pdf_with_docling(pdf_path: str) -> str:
    """
    Parse PDF using Docling.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content
    """
    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_path)

        # Extract text from document
        # Docling returns structured document with text, tables, images
        text_content = result.document.export_to_text()

        return text_content.strip()

    except Exception as e:
        logger.error(f"Docling parsing failed for {pdf_path}: {e}")
        raise


def main():
    """Main processing function."""

    logger.info("Starting Docling PDF parsing...")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info(f"PDF directory: {PDF_DIR}")

    # Check PDF directory exists
    pdf_path = Path(PDF_DIR)
    if not pdf_path.exists():
        logger.error(f"PDF directory not found: {PDF_DIR}")
        sys.exit(1)

    # Connect to database
    logger.info("Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    try:
        # Get claim documents that need parsing
        with SessionLocal() as session:
            query = text("""
                SELECT
                    CAST(cd.id AS text) as doc_id,
                    c.claim_number,
                    cd.file_path
                FROM claim_documents cd
                JOIN claims c ON cd.claim_id = c.id
                WHERE cd.raw_ocr_text IS NOT NULL
                ORDER BY c.claim_number
            """)

            result = session.execute(query).fetchall()
            documents = [(row.doc_id, row.claim_number, row.file_path) for row in result]

        if not documents:
            logger.warning("No documents found to parse")
            return

        logger.info(f"Found {len(documents)} documents to parse with Docling")

        # Parse PDFs
        parsed = 0
        failed = 0

        for doc_id, claim_number, file_path in documents:
            # Get PDF filename
            filename = Path(file_path).name
            pdf_file_path = pdf_path / filename

            if not pdf_file_path.exists():
                logger.error(f"PDF not found: {pdf_file_path}")
                failed += 1
                continue

            logger.info(f"Parsing {claim_number} ({filename})...")

            try:
                # Parse with Docling
                extracted_text = parse_pdf_with_docling(str(pdf_file_path))

                # Update database
                with SessionLocal() as session:
                    update_query = text("""
                        UPDATE claim_documents
                        SET raw_ocr_text = :ocr_text,
                            ocr_confidence = 0.95,
                            ocr_processed_at = NOW()
                        WHERE CAST(id AS text) = :doc_id
                    """)

                    session.execute(
                        update_query,
                        {
                            "ocr_text": extracted_text,
                            "doc_id": doc_id
                        }
                    )
                    session.commit()

                parsed += 1
                logger.info(f"  ✅ Parsed {claim_number} ({parsed}/{len(documents)})")

                if parsed % 10 == 0:
                    logger.info(f"Progress: {parsed}/{len(documents)} documents parsed")

            except Exception as e:
                logger.error(f"  ❌ Failed to parse {claim_number}: {e}")
                failed += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"Docling Parsing Complete")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Parsed: {parsed}/{len(documents)}")
        logger.info(f"❌ Failed: {failed}/{len(documents)}")
        logger.info(f"{'='*60}")

        if failed > 0:
            logger.warning(f"Some documents failed to parse. Check logs above.")
            sys.exit(1)
        else:
            logger.info("🎉 All PDFs parsed successfully with Docling!")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
