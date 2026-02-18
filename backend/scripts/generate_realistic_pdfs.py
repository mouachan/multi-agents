#!/usr/bin/env python3
"""
Generate realistic PDFs from seed data OCR texts.

Reads claim_documents from PostgreSQL and generates PDFs with the OCR text
rendered as realistic insurance claim documents.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
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
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/pdfs")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


def create_pdf_from_text(output_path: str, claim_number: str, claim_type: str, ocr_text: str):
    """
    Create a PDF document from OCR text.

    Args:
        output_path: Path to save PDF
        claim_number: Claim number (e.g., CLM-2024-0001)
        claim_type: Type of claim (Auto, Medical, Home, Life)
        ocr_text: Text content to render
    """

    # Create PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=12,
        alignment=1  # Center
    )

    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica'
    )

    # Add title
    title = Paragraph(f"INSURANCE CLAIM DOCUMENT", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))

    # Add claim info table
    claim_info_data = [
        ['Claim Number:', claim_number],
        ['Claim Type:', claim_type],
        ['Document Date:', datetime.now().strftime('%Y-%m-%d')],
    ]

    claim_info_table = Table(claim_info_data, colWidths=[2*inch, 4*inch])
    claim_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(claim_info_table)
    elements.append(Spacer(1, 0.3*inch))

    # Add separator line
    elements.append(Spacer(1, 0.1*inch))

    # Add claim content header
    content_header = Paragraph("CLAIM DETAILS", header_style)
    elements.append(content_header)
    elements.append(Spacer(1, 0.1*inch))

    # Split OCR text into paragraphs (preserve formatting)
    lines = ocr_text.split('\n')
    for line in lines:
        if line.strip():
            # Handle different formatting
            if line.strip().isupper() and len(line.strip()) < 50:
                # Likely a header
                para = Paragraph(line.strip(), header_style)
            else:
                # Regular body text - escape XML special chars
                escaped_line = (line
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                )
                para = Paragraph(escaped_line, body_style)
            elements.append(para)
        else:
            elements.append(Spacer(1, 0.1*inch))

    # Add footer
    elements.append(Spacer(1, 0.3*inch))
    footer_text = f"<i>Document generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)

    # Build PDF
    doc.build(elements)
    logger.info(f"Generated PDF: {output_path}")


def main():
    """Main processing function."""

    logger.info("Starting PDF generation...")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Create output directory
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    # Connect to database
    logger.info("Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    try:
        # Get claim documents with OCR text
        with SessionLocal() as session:
            query = text("""
                SELECT
                    c.claim_number,
                    c.claim_type,
                    cd.raw_ocr_text,
                    cd.file_path
                FROM claim_documents cd
                JOIN claims c ON cd.claim_id = c.id
                WHERE cd.raw_ocr_text IS NOT NULL
                ORDER BY c.claim_number
            """)

            result = session.execute(query).fetchall()
            documents = [(row.claim_number, row.claim_type, row.raw_ocr_text, row.file_path)
                        for row in result]

        if not documents:
            logger.warning("No documents found with OCR text")
            return

        logger.info(f"Found {len(documents)} documents to generate")

        # Generate PDFs
        generated = 0
        for claim_number, claim_type, ocr_text, file_path in documents:
            # Extract filename from file_path
            filename = Path(file_path).name
            pdf_path = output_path / filename

            try:
                create_pdf_from_text(
                    str(pdf_path),
                    claim_number,
                    claim_type,
                    ocr_text
                )
                generated += 1

                if generated % 10 == 0:
                    logger.info(f"Progress: {generated}/{len(documents)} PDFs generated")

            except Exception as e:
                logger.error(f"Failed to generate PDF for {claim_number}: {e}")

        logger.info(f"\n{'='*60}")
        logger.info(f"PDF Generation Complete")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Generated: {generated}/{len(documents)} PDFs")
        logger.info(f"📁 Output directory: {OUTPUT_DIR}")
        logger.info(f"{'='*60}")

        if generated < len(documents):
            logger.warning(f"Some PDFs failed to generate. Check logs above.")
            sys.exit(1)
        else:
            logger.info("🎉 All PDFs generated successfully!")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
