#!/usr/bin/env python3
"""
Seed RAG vector database with user contracts and historical claims
"""

import os
import sys
import asyncio
import httpx
import psycopg2
from psycopg2.extras import Json
from datetime import datetime, timedelta
import random

# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "claims_pass")

# Embedding service
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://embeddinggemma-300m-edg-demo.apps.cluster-rk6mx.rk6mx.sandbox492.opentlc.com")

# User data
USERS_DATA = [
    {
        "user_id": "USER001",
        "email": "john.doe@example.com",
        "full_name": "John Doe",
        "date_of_birth": "1985-03-15",
        "phone_number": "+1-555-0101",
        "address": "123 Main St, Springfield, IL 62701"
    },
    {
        "user_id": "USER002",
        "email": "jane.smith@example.com",
        "full_name": "Jane Smith",
        "date_of_birth": "1990-07-22",
        "phone_number": "+1-555-0102",
        "address": "456 Oak Ave, Chicago, IL 60601"
    },
    {
        "user_id": "USER003",
        "email": "michael.johnson@example.com",
        "full_name": "Michael Johnson",
        "date_of_birth": "1978-11-30",
        "phone_number": "+1-555-0103",
        "address": "789 Pine St, Peoria, IL 61602"
    },
    {
        "user_id": "USER004",
        "email": "sarah.williams@example.com",
        "full_name": "Sarah Williams",
        "date_of_birth": "1992-05-18",
        "phone_number": "+1-555-0104",
        "address": "321 Maple Dr, Naperville, IL 60540"
    },
    {
        "user_id": "USER005",
        "email": "robert.brown@example.com",
        "full_name": "Robert Brown",
        "date_of_birth": "1982-09-25",
        "phone_number": "+1-555-0105",
        "address": "654 Cedar Ln, Aurora, IL 60505"
    }
]

# Contract templates
CONTRACTS_DATA = [
    # AUTO contracts
    {
        "contract_type": "AUTO",
        "template": """AUTO INSURANCE CONTRACT
Contract Number: {contract_number}
Policyholder: {full_name}
Coverage Type: Comprehensive Auto Insurance
Coverage Amount: ${coverage_amount:,.2f}
Deductible: ${deductible}
Effective Date: {start_date}
Expiration Date: {end_date}

Key Terms:
- Collision coverage up to ${coverage_amount:,.2f}
- Liability coverage: $500,000 per incident
- Medical payments: $50,000 per person
- Uninsured motorist coverage included
- Roadside assistance included
- Deductible: ${deductible} per claim

Covered Vehicles:
- Primary vehicle coverage
- Rental car coverage (up to $50/day)

This contract provides comprehensive protection for automotive accidents, theft, and damage.""",
        "coverage_amounts": [100000, 150000, 250000, 500000],
        "deductibles": [500, 1000, 2500]
    },
    # HOME contracts
    {
        "contract_type": "HOME",
        "template": """HOME INSURANCE CONTRACT
Contract Number: {contract_number}
Policyholder: {full_name}
Coverage Type: Homeowners Insurance Policy
Coverage Amount: ${coverage_amount:,.2f}
Deductible: ${deductible}
Effective Date: {start_date}
Expiration Date: {end_date}

Key Terms:
- Dwelling coverage: ${coverage_amount:,.2f}
- Personal property coverage: 70% of dwelling amount
- Liability coverage: $300,000
- Medical payments to others: $5,000
- Loss of use coverage included
- Deductible: ${deductible} per claim

Covered Perils:
- Fire and smoke damage
- Water damage (excluding floods)
- Theft and vandalism
- Storm and wind damage
- Falling objects

This contract protects your home and personal property against covered losses.""",
        "coverage_amounts": [200000, 300000, 500000, 750000],
        "deductibles": [1000, 2500, 5000]
    },
    # MEDICAL contracts
    {
        "contract_type": "MEDICAL",
        "template": """MEDICAL INSURANCE CONTRACT
Contract Number: {contract_number}
Policyholder: {full_name}
Coverage Type: Comprehensive Health Insurance
Coverage Amount: ${coverage_amount:,.2f} annual maximum
Deductible: ${deductible} annual
Effective Date: {start_date}
Expiration Date: {end_date}

Key Terms:
- Annual out-of-pocket maximum: ${coverage_amount:,.2f}
- Annual deductible: ${deductible}
- Preventive care: 100% covered (no deductible)
- Primary care visits: $25 copay
- Specialist visits: $50 copay
- Emergency room: 20% coinsurance after deductible
- Prescription drugs: Covered with tiered copays

Covered Services:
- Doctor visits and specialist consultations
- Hospital stays and surgeries
- Diagnostic tests and lab work
- Prescription medications
- Mental health services
- Physical therapy and rehabilitation

This contract provides comprehensive medical coverage with a focus on preventive care.""",
        "coverage_amounts": [5000, 10000, 15000, 25000],
        "deductibles": [500, 1000, 1500, 3000]
    }
]


async def create_embedding(text: str) -> list:
    """Create embedding using TEI service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                EMBEDDING_URL,
                json={"inputs": text}
            )

            if response.status_code == 200:
                result = response.json()
                # TEI returns embeddings as array
                if isinstance(result, list) and len(result) > 0:
                    return result[0]
                else:
                    print(f"Unexpected embedding response format: {result}")
                    return None
            else:
                print(f"Embedding API error: {response.status_code}")
                return None
    except Exception as e:
        print(f"Error creating embedding: {e}")
        return None


def generate_contracts_for_user(user_data, num_contracts=2):
    """Generate insurance contracts for a user"""
    contracts = []
    base_date = datetime.now() - timedelta(days=random.randint(365, 1095))

    # Ensure variety of contract types
    contract_types = random.sample(CONTRACTS_DATA, min(num_contracts, len(CONTRACTS_DATA)))

    for i, contract_template in enumerate(contract_types):
        contract_number = f"{contract_template['contract_type']}-{random.randint(100000, 999999)}"
        coverage_amount = random.choice(contract_template['coverage_amounts'])
        deductible = random.choice(contract_template['deductibles'])
        start_date = base_date + timedelta(days=i*180)
        end_date = start_date + timedelta(days=365)

        full_text = contract_template['template'].format(
            contract_number=contract_number,
            full_name=user_data['full_name'],
            coverage_amount=coverage_amount,
            deductible=deductible,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        # Extract key terms for structured storage
        key_terms = {
            "coverage_amount": coverage_amount,
            "deductible": deductible,
            "contract_type": contract_template['contract_type'],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

        contracts.append({
            "user_id": user_data['user_id'],
            "contract_number": contract_number,
            "contract_type": contract_template['contract_type'],
            "coverage_amount": coverage_amount,
            "full_text": full_text,
            "key_terms": key_terms,
            "is_active": end_date > datetime.now(),
            "start_date": start_date,
            "end_date": end_date
        })

    return contracts


async def seed_rag_data():
    """Main seeding function"""
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
        print(f"Embedding service: {EMBEDDING_URL}")
        print()

        # Clear existing data
        print("Clearing existing RAG data...")
        cursor.execute("DELETE FROM user_contracts")
        cursor.execute("DELETE FROM users WHERE user_id LIKE 'user_%'")
        conn.commit()
        print("Cleared existing data")
        print()

        # Insert users
        print("Inserting users...")
        user_insert = """
            INSERT INTO users (user_id, email, full_name, date_of_birth, phone_number, address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        for user in USERS_DATA:
            # Convert address to JSONB format
            address_json = Json({"street": user['address']})

            cursor.execute(user_insert, (
                user['user_id'],
                user['email'],
                user['full_name'],
                user['date_of_birth'],
                user['phone_number'],
                address_json
            ))
            print(f"  Inserted user: {user['user_id']} ({user['full_name']})")

        conn.commit()
        print()

        # Generate and insert contracts with embeddings
        print("Generating user contracts with embeddings...")
        contract_insert = """
            INSERT INTO user_contracts
            (user_id, contract_number, contract_type, coverage_amount, full_text,
             key_terms, is_active, start_date, end_date, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        total_contracts = 0
        for user in USERS_DATA:
            print(f"\nProcessing user: {user['user_id']}")
            contracts = generate_contracts_for_user(user, num_contracts=random.randint(1, 3))

            for contract in contracts:
                print(f"  Generating embedding for contract: {contract['contract_number']}")

                # Create embedding from full contract text
                embedding = await create_embedding(contract['full_text'])

                if embedding:
                    # Convert embedding to PostgreSQL vector format
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'

                    cursor.execute(contract_insert, (
                        contract['user_id'],
                        contract['contract_number'],
                        contract['contract_type'],
                        contract['coverage_amount'],
                        contract['full_text'],
                        Json(contract['key_terms']),
                        contract['is_active'],
                        contract['start_date'],
                        contract['end_date'],
                        embedding_str
                    ))

                    total_contracts += 1
                    print(f"    ✓ Inserted contract with embedding (dim: {len(embedding)})")
                else:
                    print(f"    ✗ Failed to generate embedding, skipping")

        conn.commit()

        print()
        print(f"✓ Successfully seeded RAG database!")
        print(f"  - Users: {len(USERS_DATA)}")
        print(f"  - Contracts with embeddings: {total_contracts}")

        # Verify
        cursor.execute("SELECT user_id, COUNT(*) FROM user_contracts GROUP BY user_id")
        results = cursor.fetchall()
        print("\nContract distribution:")
        for user_id, count in results:
            cursor.execute("""
                SELECT contract_type, is_active
                FROM user_contracts
                WHERE user_id = %s
            """, (user_id,))
            contracts = cursor.fetchall()
            types = [f"{ct} ({'active' if active else 'expired'})" for ct, active in contracts]
            print(f"  {user_id}: {count} contracts ({', '.join(types)})")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_rag_data())
