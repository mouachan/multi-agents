#!/usr/bin/env python3
"""
Seed PostgreSQL database with claim records
"""

import os
import sys
from datetime import datetime, timedelta
import random
import psycopg2
from psycopg2.extras import Json

# Database configuration - can be overridden by environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "claims_pass")

# Claim data (matching the generated PDFs)
def get_claim_data():
    """Generate claim data matching the PDF files"""
    base_date = datetime.now() - timedelta(days=90)
    claims = []

    # Auto claims (20)
    for i in range(1, 21):
        claim_number = f"CLM-2024-AUTO-{i:03d}"
        date_incident = base_date + timedelta(days=random.randint(0, 90))
        claims.append({
            "claim_number": claim_number,
            "claim_type": "AUTO",
            "user_id": f"user_{random.randint(1, 5):03d}",
            "document_path": f"/claim_documents/claim_auto_{i:03d}.pdf",
            "submitted_at": date_incident,
            "status": "pending",
            "metadata": {"source": "pdf_upload", "category": "auto_insurance"}
        })

    # Home claims (15)
    for i in range(1, 16):
        claim_number = f"CLM-2024-HOME-{i:03d}"
        date_loss = base_date + timedelta(days=random.randint(0, 90))
        claims.append({
            "claim_number": claim_number,
            "claim_type": "HOME",
            "user_id": f"user_{random.randint(1, 5):03d}",
            "document_path": f"/claim_documents/claim_home_{i:03d}.pdf",
            "submitted_at": date_loss,
            "status": "pending",
            "metadata": {"source": "pdf_upload", "category": "home_insurance"}
        })

    # Medical claims (15)
    for i in range(1, 16):
        claim_number = f"CLM-2024-MED-{i:03d}"
        date_service = base_date + timedelta(days=random.randint(0, 90))
        claims.append({
            "claim_number": claim_number,
            "claim_type": "MEDICAL",
            "user_id": f"user_{random.randint(1, 5):03d}",
            "document_path": f"/claim_documents/claim_medical_{i:03d}.pdf",
            "submitted_at": date_service,
            "status": "pending",
            "metadata": {"source": "pdf_upload", "category": "medical_insurance"}
        })

    return claims

def seed_database():
    """Seed the database with claim records"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        print(f"Connected to database: {POSTGRES_DB}")
        print(f"Host: {POSTGRES_HOST}:{POSTGRES_PORT}")
        print()

        # Clear existing claims (optional - comment out to keep existing data)
        print("Clearing existing claims...")
        cursor.execute("DELETE FROM claims WHERE claim_number LIKE 'CLM-2024-%'")
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} existing claims")
        print()

        # Get claim data
        claims = get_claim_data()

        # Insert claims
        print(f"Inserting {len(claims)} new claims...")
        insert_query = """
            INSERT INTO claims (
                claim_number, claim_type, user_id, document_path,
                status, submitted_at, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
        """

        inserted = 0
        for claim in claims:
            try:
                cursor.execute(insert_query, (
                    claim["claim_number"],
                    claim["claim_type"],
                    claim["user_id"],
                    claim["document_path"],
                    claim["status"],
                    claim["submitted_at"],
                    Json(claim["metadata"])
                ))
                inserted += 1
                if inserted % 10 == 0:
                    print(f"  Inserted {inserted}/{len(claims)} claims...")
            except Exception as e:
                print(f"  Error inserting {claim['claim_number']}: {e}")

        # Commit changes
        conn.commit()

        print()
        print(f"✓ Successfully seeded database with {inserted} claims!")
        print()
        print("Breakdown:")
        print(f"  - Auto: 20 claims")
        print(f"  - Home: 15 claims")
        print(f"  - Medical: 15 claims")
        print()

        # Verify
        cursor.execute("SELECT claim_type, COUNT(*) FROM claims GROUP BY claim_type")
        results = cursor.fetchall()
        print("Verification - Claims by type:")
        for claim_type, count in results:
            print(f"  {claim_type}: {count}")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_database()
