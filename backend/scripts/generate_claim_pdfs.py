#!/usr/bin/env python3
"""
Generate realistic claim PDF documents for OCR testing
"""

import os
from datetime import datetime, timedelta
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Sample data for generating realistic claims
AUTO_SCENARIOS = [
    {"incident": "Rear-end collision at intersection", "damage": "Front bumper damage, headlight broken", "location": "123 Main St, Springfield, IL"},
    {"incident": "Side-swipe on highway", "damage": "Driver side door scratched, mirror damaged", "location": "I-55 Mile Marker 42"},
    {"incident": "Parking lot collision", "damage": "Rear bumper dent, taillight cracked", "location": "Walmart Parking Lot, Oak Ave"},
    {"incident": "Hit-and-run while parked", "damage": "Passenger side panel scratched", "location": "456 Elm Street, Springfield, IL"},
    {"incident": "Fender bender at stoplight", "damage": "Front fender damage, hood misaligned", "location": "Intersection of 5th and Main"},
    {"incident": "Multi-vehicle pileup", "damage": "Significant front and rear damage", "location": "Highway 66 near Exit 12"},
    {"incident": "Collision with deer", "damage": "Hood damage, windshield cracked", "location": "Rural Route 45"},
    {"incident": "Backing into pole", "damage": "Rear bumper dent, sensor damaged", "location": "Shopping Center, Pine St"},
    {"incident": "T-bone collision", "damage": "Passenger door crushed, airbags deployed", "location": "Intersection of Oak and Maple"},
    {"incident": "Sliding on ice into guardrail", "damage": "Front quarter panel damage", "location": "Highway 72 North"},
]

HOME_SCENARIOS = [
    {"cause": "Burst pipe in kitchen", "damage": "Kitchen floor, cabinets, drywall damage", "type": "Water Damage"},
    {"cause": "Roof leak during storm", "damage": "Ceiling water damage, insulation wet", "type": "Storm Damage"},
    {"cause": "Fire in garage", "damage": "Garage structure, tools, vehicle damaged", "type": "Fire Damage"},
    {"cause": "Tree fell on house", "damage": "Roof damage, gutter destroyed", "type": "Storm Damage"},
    {"cause": "Basement flooding", "damage": "Basement carpet, drywall, HVAC damaged", "type": "Water Damage"},
    {"cause": "Broken window from vandalism", "damage": "Living room window, interior water damage", "type": "Vandalism"},
    {"cause": "Dishwasher leak", "damage": "Kitchen floor, lower cabinets", "type": "Water Damage"},
    {"cause": "Lightning strike", "damage": "Electrical system, appliances fried", "type": "Storm Damage"},
    {"cause": "Frozen pipe burst", "damage": "Bathroom walls, floor damage", "type": "Water Damage"},
    {"cause": "Wind damage to siding", "damage": "Exterior siding panels, insulation", "type": "Storm Damage"},
]

MEDICAL_SERVICES = [
    {"service": "Annual physical exam, blood work", "diagnosis": "Routine medical examination", "provider": "City Medical Center"},
    {"service": "Emergency room visit for chest pain", "diagnosis": "Acute chest pain, cardiac evaluation", "provider": "Springfield General Hospital"},
    {"service": "Knee surgery - ACL repair", "diagnosis": "Torn anterior cruciate ligament", "provider": "Orthopedic Specialists"},
    {"service": "Diagnostic imaging - MRI scan", "diagnosis": "Lower back pain evaluation", "provider": "Imaging Associates"},
    {"service": "Physical therapy sessions", "diagnosis": "Post-surgical rehabilitation", "provider": "Rehab Plus Center"},
    {"service": "Dental crown replacement", "diagnosis": "Tooth restoration", "provider": "Family Dental Care"},
    {"service": "Allergy testing and consultation", "diagnosis": "Seasonal allergies", "provider": "Allergy & Asthma Clinic"},
    {"service": "Colonoscopy screening", "diagnosis": "Preventive cancer screening", "provider": "Gastroenterology Center"},
    {"service": "Mental health counseling", "diagnosis": "Anxiety and depression treatment", "provider": "Behavioral Health Services"},
    {"service": "Urgent care for sprained ankle", "diagnosis": "Ankle sprain, X-ray", "provider": "QuickCare Urgent Care"},
]

NAMES = ["John Doe", "Jane Smith", "Michael Johnson", "Sarah Williams", "Robert Brown", "Emily Davis",
         "David Martinez", "Lisa Anderson", "James Wilson", "Mary Taylor", "Christopher Moore",
         "Jennifer Thomas", "Daniel Jackson", "Patricia White", "Matthew Harris"]

ADDRESSES = ["456 Oak Ave, Springfield, IL", "789 Pine St, Chicago, IL", "321 Maple Dr, Peoria, IL",
             "654 Cedar Ln, Naperville, IL", "987 Birch Rd, Aurora, IL", "147 Elm St, Joliet, IL"]

def generate_auto_claim_pdf(output_path, claim_number, name, address, date_incident):
    """Generate an auto insurance claim PDF"""
    scenario = random.choice(AUTO_SCENARIOS)
    amount = random.randint(1500, 8000)
    policy_num = f"AUTO-{random.randint(100000, 999999)}"
    plate = f"{random.choice(['ABC', 'XYZ', 'DEF', 'GHI'])}-{random.randint(1000, 9999)}"
    vehicle = random.choice(["Toyota Camry 2022", "Honda Accord 2021", "Ford F-150 2023",
                            "Chevrolet Malibu 2020", "Nissan Altima 2022"])

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "AUTO INSURANCE CLAIM FORM")

    # Content
    c.setFont("Helvetica", 11)
    y = height - 1.5*inch

    lines = [
        f"Claim Number: {claim_number}",
        f"Date of Incident: {date_incident.strftime('%Y-%m-%d')}",
        f"Claimant Name: {name}",
        f"Policy Number: {policy_num}",
        f"Address: {address}",
        "",
        f"Vehicle Make/Model: {vehicle}",
        f"License Plate: {plate}",
        "",
        f"Incident Location: {scenario['location']}",
        f"Incident Description: {scenario['incident']}",
        "",
        f"Damage Description: {scenario['damage']}",
        f"Estimated Repair Cost: ${amount:,.2f}",
        "",
        f"Police Report Number: SPD-{random.randint(2024, 2024)}-{random.randint(1000, 9999)}",
        "",
        "Signature: [Signed]",
        f"Date: {date_incident.strftime('%Y-%m-%d')}",
    ]

    for line in lines:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch

    c.save()
    return amount

def generate_home_claim_pdf(output_path, claim_number, name, address, date_loss):
    """Generate a home insurance claim PDF"""
    scenario = random.choice(HOME_SCENARIOS)
    amount = random.randint(3000, 15000)
    policy_num = f"HOME-{random.randint(100000, 999999)}"

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "HOME INSURANCE CLAIM FORM")

    # Content
    c.setFont("Helvetica", 11)
    y = height - 1.5*inch

    lines = [
        f"Claim Number: {claim_number}",
        f"Date of Loss: {date_loss.strftime('%Y-%m-%d')}",
        f"Claimant Name: {name}",
        f"Policy Number: {policy_num}",
        f"Property Address: {address}",
        "",
        f"Type of Loss: {scenario['type']}",
        f"Cause: {scenario['cause']}",
        "",
        f"Damage Description: {scenario['damage']}",
        f"Estimated Repair Cost: ${amount:,.2f}",
        "",
        f"Emergency Services: {'Yes - ' + random.choice(['Plumber', 'Electrician', 'Roofer', 'Fire Dept']) + ' called on ' + date_loss.strftime('%Y-%m-%d')}",
        "Photos Attached: Yes",
        "",
        "Signature: [Signed]",
        f"Date: {date_loss.strftime('%Y-%m-%d')}",
    ]

    for line in lines:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch

    c.save()
    return amount

def generate_medical_claim_pdf(output_path, claim_number, name, address, date_service):
    """Generate a medical insurance claim PDF"""
    service_info = random.choice(MEDICAL_SERVICES)
    amount = random.randint(200, 5000)
    policy_num = f"MED-{random.randint(100000, 999999)}"
    npi = f"{random.randint(1000000000, 9999999999)}"

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "MEDICAL INSURANCE CLAIM FORM")

    # Content
    c.setFont("Helvetica", 11)
    y = height - 1.5*inch

    lines = [
        f"Claim Number: {claim_number}",
        f"Date of Service: {date_service.strftime('%Y-%m-%d')}",
        f"Patient Name: {name}",
        f"Policy Number: {policy_num}",
        f"Patient Address: {address}",
        "",
        f"Provider Name: {service_info['provider']}",
        f"Provider NPI: {npi}",
        "",
        f"Diagnosis Code: {random.choice(['Z00.00', 'M25.561', 'R07.9', 'J30.9', 'M54.5'])}",
        f"Diagnosis: {service_info['diagnosis']}",
        "",
        f"Procedure: {service_info['service']}",
        f"Total Charges: ${amount:,.2f}",
        "",
        "Patient Signature: [Signed]",
        f"Date: {date_service.strftime('%Y-%m-%d')}",
    ]

    for line in lines:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch

    c.save()
    return amount

def main():
    """Generate 50+ claim PDFs"""
    output_dir = "/tmp/claim_documents"
    os.makedirs(output_dir, exist_ok=True)

    claims_data = []
    base_date = datetime.now() - timedelta(days=90)

    print("Generating Auto Insurance Claims...")
    for i in range(1, 21):  # 20 auto claims
        claim_number = f"CLM-2024-AUTO-{i:03d}"
        name = random.choice(NAMES)
        address = random.choice(ADDRESSES)
        date_incident = base_date + timedelta(days=random.randint(0, 90))

        pdf_path = os.path.join(output_dir, f"claim_auto_{i:03d}.pdf")
        amount = generate_auto_claim_pdf(pdf_path, claim_number, name, address, date_incident)

        claims_data.append({
            "claim_number": claim_number,
            "claim_type": "AUTO",
            "user_id": f"user_{random.randint(1, 5):03d}",
            "document_path": pdf_path,
            "submitted_at": date_incident.isoformat(),
            "expected_amount": amount
        })
        print(f"  Generated: {claim_number}")

    print("\nGenerating Home Insurance Claims...")
    for i in range(1, 16):  # 15 home claims
        claim_number = f"CLM-2024-HOME-{i:03d}"
        name = random.choice(NAMES)
        address = random.choice(ADDRESSES)
        date_loss = base_date + timedelta(days=random.randint(0, 90))

        pdf_path = os.path.join(output_dir, f"claim_home_{i:03d}.pdf")
        amount = generate_home_claim_pdf(pdf_path, claim_number, name, address, date_loss)

        claims_data.append({
            "claim_number": claim_number,
            "claim_type": "HOME",
            "user_id": f"user_{random.randint(1, 5):03d}",
            "document_path": pdf_path,
            "submitted_at": date_loss.isoformat(),
            "expected_amount": amount
        })
        print(f"  Generated: {claim_number}")

    print("\nGenerating Medical Insurance Claims...")
    for i in range(1, 16):  # 15 medical claims
        claim_number = f"CLM-2024-MED-{i:03d}"
        name = random.choice(NAMES)
        address = random.choice(ADDRESSES)
        date_service = base_date + timedelta(days=random.randint(0, 90))

        pdf_path = os.path.join(output_dir, f"claim_medical_{i:03d}.pdf")
        amount = generate_medical_claim_pdf(pdf_path, claim_number, name, address, date_service)

        claims_data.append({
            "claim_number": claim_number,
            "claim_type": "MEDICAL",
            "user_id": f"user_{random.randint(1, 5):03d}",
            "document_path": pdf_path,
            "submitted_at": date_service.isoformat(),
            "expected_amount": amount
        })
        print(f"  Generated: {claim_number}")

    # Generate SQL insert script
    sql_file = os.path.join(output_dir, "seed_claims.sql")
    with open(sql_file, 'w') as f:
        f.write("-- Seed claims data\n")
        f.write("-- Generated on: " + datetime.now().isoformat() + "\n\n")

        for claim in claims_data:
            f.write(f"""
INSERT INTO claims (claim_number, claim_type, user_id, document_path, status, submitted_at, metadata)
VALUES (
    '{claim['claim_number']}',
    '{claim['claim_type']}',
    '{claim['user_id']}',
    '{claim['document_path']}',
    'pending',
    '{claim['submitted_at']}',
    '{{"expected_amount": {claim["expected_amount"]}}}'::jsonb
);
""")

    print(f"\n✓ Generated {len(claims_data)} claim PDFs in {output_dir}")
    print(f"✓ SQL seed script: {sql_file}")
    print(f"\nBreakdown:")
    print(f"  - Auto: 20 claims")
    print(f"  - Home: 15 claims")
    print(f"  - Medical: 15 claims")
    print(f"  - Total: 50 claims")

if __name__ == "__main__":
    main()
