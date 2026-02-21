#!/usr/bin/env python3
"""
Generate realistic claim PDF documents for the multi-agents platform.
Outputs to documents/claims/ with filenames matching the seed data.
"""

import os
import sys
from datetime import datetime, timedelta
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Use fixed seed for reproducible output
random.seed(42)

# ============================================================================
# Auto claim scenarios
# ============================================================================
AUTO_SCENARIOS = [
    {"incident": "Rear-end collision at intersection of Route 66 and Main St. Traffic was heavy during rush hour. The other driver ran a red light.",
     "damage": "Front bumper severely damaged, both headlights broken, radiator punctured, hood bent. Airbags did not deploy.",
     "location": "Intersection of Route 66 and Main St, Springfield, IL",
     "vehicle": "Toyota Camry 2022", "plate": "ABC-4521"},
    {"incident": "Side-swipe collision on highway I-55 during lane change. Other vehicle merged without checking blind spot.",
     "damage": "Driver side door deeply scratched, side mirror torn off, rear quarter panel dented. Paint damage along entire driver side.",
     "location": "I-55 Southbound, Mile Marker 42, near Springfield",
     "vehicle": "Honda Accord 2021", "plate": "XYZ-7834"},
    {"incident": "Rear-end collision in Walmart parking lot while backing out of space. Low speed impact.",
     "damage": "Rear bumper dented and cracked, taillight assembly broken, trunk lid misaligned. Minor cosmetic damage.",
     "location": "Walmart Supercenter Parking Lot, 1500 Oak Ave, Springfield, IL",
     "vehicle": "Ford F-150 2023", "plate": "DEF-2198"},
    {"incident": "Hit-and-run incident while vehicle was parked on Elm Street overnight. Discovered damage in the morning.",
     "damage": "Passenger side front fender crushed, door panel scratched, wheel rim bent. Paint transfer from white vehicle.",
     "location": "456 Elm Street, Springfield, IL (street parking)",
     "vehicle": "Chevrolet Malibu 2020", "plate": "GHI-5567"},
    {"incident": "Fender bender at stoplight on 5th and Main. Vehicle ahead stopped suddenly for pedestrian.",
     "damage": "Front fender pushed in, hood slightly buckled, bumper cover cracked. Headlight housing cracked.",
     "location": "Intersection of 5th Street and Main Avenue, Springfield, IL",
     "vehicle": "Nissan Altima 2022", "plate": "JKL-3342"},
    {"incident": "Multi-vehicle pileup on Highway 66 due to sudden fog. Chain reaction involving 4 vehicles.",
     "damage": "Significant front and rear damage, both bumpers destroyed, trunk crushed, rear window shattered. Totaled.",
     "location": "Highway 66 near Exit 12, Sangamon County, IL",
     "vehicle": "Subaru Outback 2021", "plate": "MNO-8891"},
    {"incident": "Collision with deer crossing rural road at dusk. Animal appeared suddenly from wooded area.",
     "damage": "Hood severely dented, windshield cracked in multiple places, front grille destroyed. Deer hair embedded in damage.",
     "location": "Rural Route 45, 3 miles south of Chatham, IL",
     "vehicle": "Dodge Ram 1500 2022", "plate": "PQR-1123"},
    {"incident": "Backed into concrete pole in shopping center parking garage. Limited visibility due to pillar obstruction.",
     "damage": "Rear bumper deeply dented, backup camera destroyed, rear parking sensors non-functional. Exhaust pipe bent.",
     "location": "Springfield Mall Parking Garage, Level B2, Pine Street",
     "vehicle": "BMW X3 2023", "plate": "STU-6745"},
    {"incident": "T-bone collision at uncontrolled intersection. Other driver failed to yield right of way.",
     "damage": "Passenger door completely crushed, B-pillar deformed, side airbags deployed. Window shattered. Occupant injury.",
     "location": "Intersection of Oak Drive and Maple Court, Springfield, IL",
     "vehicle": "Hyundai Tucson 2022", "plate": "VWX-9908"},
    {"incident": "Lost control on icy road and slid into guardrail. Black ice conditions, temperature was 28F.",
     "damage": "Front right quarter panel crushed against guardrail, wheel assembly damaged, axle potentially bent.",
     "location": "Highway 72 North, near Lake Springfield",
     "vehicle": "Jeep Cherokee 2021", "plate": "YZA-2234"},
    {"incident": "Rear-ended while stopped at railroad crossing. Following vehicle distracted by phone.",
     "damage": "Rear bumper destroyed, trunk lid bent, rear lights broken. Whiplash reported by driver.",
     "location": "Railroad crossing on County Road 14, Sherman, IL",
     "vehicle": "Kia Sorento 2023", "plate": "BCD-5567"},
    {"incident": "Swerved to avoid pothole and hit curb. Deep pothole on poorly maintained road.",
     "damage": "Front right tire blown, wheel rim cracked, suspension damage, lower control arm bent.",
     "location": "3200 Block of Washington Street, Springfield, IL",
     "vehicle": "Mazda CX-5 2022", "plate": "EFG-8890"},
    {"incident": "Hail storm damage while parked at workplace. Golf ball sized hail for 15 minutes.",
     "damage": "Multiple dents across hood, roof, and trunk. Windshield chipped in 3 places. Both side mirrors cracked.",
     "location": "State Capitol Complex Parking Lot, Springfield, IL",
     "vehicle": "Tesla Model 3 2023", "plate": "HIJ-1122"},
    {"incident": "Collision in drive-through lane. Vehicle behind rolled forward while driver was at window.",
     "damage": "Rear bumper scratched and pushed in, rear sensor bar damaged. Minor trunk lid paint damage.",
     "location": "McDonald's Drive-Through, 890 Wabash Ave, Springfield, IL",
     "vehicle": "Volkswagen Jetta 2021", "plate": "KLM-4455"},
    {"incident": "Garage door closed on vehicle while pulling out. Door sensor malfunction.",
     "damage": "Roof panel dented and scratched, rear spoiler broken, rear window gasket displaced.",
     "location": "Residential garage, 567 Birch Lane, Springfield, IL",
     "vehicle": "Toyota RAV4 2022", "plate": "NOP-7788"},
    {"incident": "Flooding damage from flash flood. Vehicle stalled in rising water on underpass.",
     "damage": "Engine hydrolocked, interior flooded to dashboard level, electrical system compromised. Likely total loss.",
     "location": "Veterans Parkway underpass at I-72, Springfield, IL",
     "vehicle": "Honda CR-V 2021", "plate": "QRS-0011"},
    {"incident": "Construction zone accident. Loose gravel kicked up by truck, followed by sudden stop.",
     "damage": "Windshield shattered by large stone, front bumper impacted barrier, paint chips across entire front.",
     "location": "I-55 construction zone, Mile 38-42, Williamsville, IL",
     "vehicle": "Ford Escape 2023", "plate": "TUV-3344"},
    {"incident": "Vandalism in apartment complex parking. Vehicle keyed and tires slashed overnight.",
     "damage": "Deep key scratches on all four panels, two tires slashed, driver side mirror kicked off.",
     "location": "Sunset Apartments, 2100 South Grand Ave, Springfield, IL",
     "vehicle": "Chevrolet Equinox 2022", "plate": "WXY-6677"},
    {"incident": "Backing out of driveway into neighbor's parked car. Limited visibility due to hedge.",
     "damage": "Rear bumper cracked, tail light broken, minor trunk dent. Other vehicle also damaged.",
     "location": "Residential driveway, 234 Cedar Court, Rochester, IL",
     "vehicle": "Buick Encore 2021", "plate": "ZAB-9900"},
    {"incident": "Collision with shopping cart in grocery store parking lot during high winds.",
     "damage": "Multiple door dings, passenger side panel dented, paint scratched in several spots.",
     "location": "Meijer Parking Lot, 3000 Lindbergh Blvd, Springfield, IL",
     "vehicle": "Nissan Rogue 2023", "plate": "CDE-2233"},
]

# ============================================================================
# Home claim scenarios
# ============================================================================
HOME_SCENARIOS = [
    {"cause": "Burst pipe in kitchen under the sink. Pipe corroded due to age (original 1985 plumbing). Water flowed for approximately 4 hours before discovery.",
     "damage": "Kitchen hardwood floor warped (200 sq ft), lower cabinets swollen and delaminated, drywall water damage extending into dining room.",
     "type": "Water Damage", "cost": 12500},
    {"cause": "Severe thunderstorm with 70mph winds caused roof shingle damage and subsequent leak. Multiple shingles torn off on south-facing slope.",
     "damage": "Ceiling water stains in master bedroom and hallway (150 sq ft). Insulation saturated in attic. Drywall bubbling and potential mold concern.",
     "type": "Storm Damage", "cost": 8700},
    {"cause": "Electrical fire originated in garage outlet (overloaded circuit). Fire contained to garage but smoke damage throughout first floor.",
     "damage": "Garage structure charred (west wall), stored tools and equipment destroyed, vehicle in garage sustained heat damage. Smoke damage to kitchen and living room.",
     "type": "Fire Damage", "cost": 35000},
    {"cause": "Large oak tree fell on house during ice storm. Tree was approximately 60 feet tall and landed across the roof ridge.",
     "damage": "Roof structure collapsed in two rooms (master bedroom and office), gutter system destroyed on east side, exterior siding damaged. Temporary tarp installed.",
     "type": "Storm Damage", "cost": 22000},
    {"cause": "Basement flooding from sump pump failure during heavy rainfall. Pump motor burned out, backup battery also dead.",
     "damage": "Finished basement carpet ruined (800 sq ft), drywall damaged 4 feet up all walls, HVAC ductwork contaminated, stored belongings destroyed.",
     "type": "Water Damage", "cost": 18500},
    {"cause": "Vandalism - rocks thrown through living room bay window. Incident occurred during nighttime. Police report filed.",
     "damage": "Bay window completely shattered (triple pane, custom size), interior water damage from rain entry before temporary covering, curtains and carpet stained.",
     "type": "Vandalism", "cost": 6200},
    {"cause": "Dishwasher supply line failed (braided stainless steel connector burst). Water leaked for estimated 8 hours overnight.",
     "damage": "Kitchen tile floor undermined, subfloor rotted, lower kitchen cabinets destroyed (6 units), adjacent laundry room floor buckled.",
     "type": "Water Damage", "cost": 14300},
    {"cause": "Lightning strike hit chimney during severe thunderstorm. Electrical surge destroyed electronics and caused small fire in attic.",
     "damage": "Chimney masonry cracked and partially collapsed, attic fire damage (contained), entire home electrical system fried including HVAC control board, TV, computers.",
     "type": "Storm Damage", "cost": 28000},
    {"cause": "Frozen pipe burst in upstairs bathroom during cold snap (-15F). Pipe in exterior wall with insufficient insulation.",
     "damage": "Bathroom flooring destroyed, water cascaded to first floor causing ceiling collapse in living room, hardwood floor warping in two rooms.",
     "type": "Water Damage", "cost": 16800},
    {"cause": "High winds (60+ mph) tore vinyl siding panels off east and north sides of house. Exposed sheathing then absorbed rain.",
     "damage": "32 siding panels missing/damaged, house wrap torn, OSB sheathing swelling from moisture, insulation compromised in affected wall cavities.",
     "type": "Storm Damage", "cost": 9500},
    {"cause": "Water heater tank failure (10-year-old unit). Bottom rusted through, 50 gallons released into utility room.",
     "damage": "Utility room flooring destroyed, adjacent family room carpet saturated, lower drywall damage in both rooms, furnace base corroded.",
     "type": "Water Damage", "cost": 7800},
    {"cause": "Tornado damage - EF1 tornado passed within 200 yards. Not a direct hit but wind damage significant.",
     "damage": "Roof ridge cap torn off, multiple skylights broken, fence destroyed, shed demolished, significant yard debris.",
     "type": "Storm Damage", "cost": 19500},
    {"cause": "Cooking fire on stovetop. Grease fire spread to range hood and upper cabinets before extinguisher deployment.",
     "damage": "Range hood destroyed, upper cabinets (4 units) charred, ceiling above stove fire-damaged, smoke and soot throughout kitchen and dining area.",
     "type": "Fire Damage", "cost": 15200},
    {"cause": "Raccoon infestation in attic. Animals entered through damaged soffit and nested for weeks before discovery.",
     "damage": "Attic insulation contaminated (must be replaced), HVAC flex ducts chewed through, soffit boards destroyed, animal waste remediation needed.",
     "type": "Animal Damage", "cost": 8900},
    {"cause": "Ice dam formation on roof caused water to back up under shingles and leak into walls of second floor.",
     "damage": "Interior wall damage in two bedrooms, ceiling paint bubbling and peeling, mold discovered behind drywall in one wall, window trim rotted.",
     "type": "Water Damage", "cost": 11200},
]

# ============================================================================
# Medical claim scenarios
# ============================================================================
MEDICAL_SCENARIOS = [
    {"service": "Annual physical examination including comprehensive blood work panel (CBC, CMP, lipid panel, thyroid, A1C). EKG performed due to family history.",
     "diagnosis": "Routine preventive care examination - Z00.00", "provider": "Springfield Family Medicine Center",
     "doctor": "Dr. Sarah Chen, MD", "npi": "1234567890", "cost": 850},
    {"service": "Emergency room visit for acute chest pain. CT angiogram, troponin levels x3, cardiac monitoring 6 hours. Discharged with follow-up.",
     "diagnosis": "Acute chest pain, non-cardiac origin - R07.9", "provider": "Springfield General Hospital Emergency Dept",
     "doctor": "Dr. James Rodriguez, MD", "npi": "2345678901", "cost": 8500},
    {"service": "Arthroscopic ACL reconstruction surgery with hamstring autograft. Pre-op MRI, anesthesia, 2-night hospital stay, post-op brace.",
     "diagnosis": "Complete tear of anterior cruciate ligament, right knee - S83.511A", "provider": "Illinois Orthopedic Specialists",
     "doctor": "Dr. Michael Park, MD, FAAOS", "npi": "3456789012", "cost": 32000},
    {"service": "Diagnostic MRI of lumbar spine with and without contrast. Radiologist interpretation and report.",
     "diagnosis": "Low back pain with radiculopathy, lumbar region - M54.5", "provider": "Advanced Imaging Associates",
     "doctor": "Dr. Lisa Wang, MD (Radiology)", "npi": "4567890123", "cost": 3200},
    {"service": "Physical therapy - 12 sessions post ACL reconstruction. Includes ROM exercises, strengthening, gait training, modalities.",
     "diagnosis": "Post-surgical rehabilitation, right knee ACL repair - Z96.651", "provider": "Rehab Plus Physical Therapy",
     "doctor": "Dr. Amanda Foster, DPT", "npi": "5678901234", "cost": 2400},
    {"service": "Dental crown replacement - porcelain-fused-to-metal crown on molar #30. Includes impression, temporary crown, and final placement.",
     "diagnosis": "Dental caries, tooth #30 with prior root canal - K02.9", "provider": "Springfield Family Dental Care",
     "doctor": "Dr. Robert Kim, DDS", "npi": "6789012345", "cost": 1800},
    {"service": "Comprehensive allergy testing panel (environmental and food) - 60 allergen skin prick test plus specific IgE blood panel.",
     "diagnosis": "Allergic rhinitis, seasonal and perennial - J30.9", "provider": "Central Illinois Allergy & Asthma Clinic",
     "doctor": "Dr. Patricia Nguyen, MD", "npi": "7890123456", "cost": 1200},
    {"service": "Screening colonoscopy with polyp removal (2 sessile polyps removed via snare polypectomy). Moderate sedation.",
     "diagnosis": "Encounter for screening for malignant neoplasm of colon - Z12.11", "provider": "Springfield Gastroenterology Center",
     "doctor": "Dr. David Cohen, MD, FACG", "npi": "8901234567", "cost": 4500},
    {"service": "Mental health counseling - 8 individual therapy sessions (CBT-based). Initial evaluation plus 7 follow-up sessions.",
     "diagnosis": "Generalized anxiety disorder with moderate depression - F41.1, F32.1", "provider": "Behavioral Health Services of Springfield",
     "doctor": "Dr. Jennifer Adams, PsyD", "npi": "9012345678", "cost": 1600},
    {"service": "Urgent care visit for ankle injury. X-ray (3 views), examination, air cast application, crutch fitting.",
     "diagnosis": "Sprain of calcaneofibular ligament, right ankle - S93.411A", "provider": "QuickCare Urgent Care Center",
     "doctor": "Dr. Thomas Brown, MD", "npi": "0123456789", "cost": 950},
    {"service": "Dermatology consultation for suspicious mole. Shave biopsy performed and sent to pathology. Follow-up visit for results.",
     "diagnosis": "Dysplastic nevus, trunk - D22.5", "provider": "Springfield Dermatology Associates",
     "doctor": "Dr. Karen Mitchell, MD, FAAD", "npi": "1122334455", "cost": 650},
    {"service": "Prenatal care - routine 20-week anatomy ultrasound scan. Detailed fetal survey with measurements and images.",
     "diagnosis": "Supervision of normal pregnancy, second trimester - Z34.02", "provider": "Women's Health Center of Springfield",
     "doctor": "Dr. Emily Richardson, MD, OB-GYN", "npi": "2233445566", "cost": 1100},
    {"service": "Ophthalmology exam - comprehensive dilated eye exam, OCT scan, visual field test. New prescription for corrective lenses.",
     "diagnosis": "Open-angle glaucoma suspect, bilateral - H40.011", "provider": "Prairie Eye Center",
     "doctor": "Dr. William Torres, MD, FACS", "npi": "3344556677", "cost": 450},
    {"service": "Cardiology consultation - stress echocardiogram, 24-hour Holter monitor, follow-up visit with treatment plan discussion.",
     "diagnosis": "Palpitations and exercise intolerance - R00.2", "provider": "Heart & Vascular Institute of Illinois",
     "doctor": "Dr. Maria Santos, MD, FACC", "npi": "4455667788", "cost": 3800},
    {"service": "ENT consultation for chronic sinusitis. CT sinus scan, nasal endoscopy, culture obtained. Medical management initiated.",
     "diagnosis": "Chronic sinusitis, unspecified - J32.9", "provider": "Springfield ENT Specialists",
     "doctor": "Dr. Andrew Lee, MD", "npi": "5566778899", "cost": 1400},
]

NAMES = [
    "Michael Brown", "Sarah Johnson", "David Garcia", "Jennifer Martinez",
    "Robert Wilson", "Linda Anderson", "James Taylor", "Patricia Thomas",
    "John Moore", "Mary Jackson", "William White", "Barbara Harris",
    "Richard Martin", "Susan Thompson", "Charles Lee",
]

ADDRESSES = [
    "123 Main St, Chicago, IL 60601",
    "456 Oak Ave, Springfield, IL 62701",
    "789 Pine St, Naperville, IL 60540",
    "321 Maple Dr, Peoria, IL 61602",
    "654 Cedar Ln, Aurora, IL 60505",
    "987 Birch Rd, Joliet, IL 60432",
]


def generate_auto_claim_pdf(output_path, claim_number, name, address, date_incident, scenario_idx):
    """Generate a realistic auto insurance claim PDF."""
    scenario = AUTO_SCENARIOS[scenario_idx % len(AUTO_SCENARIOS)]
    amount = random.randint(2000, 35000)
    policy_num = f"AUTO-{random.randint(100000, 999999)}"

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1*inch, height - 0.8*inch, "AUTO INSURANCE CLAIM FORM")
    c.setFont("Helvetica", 9)
    c.drawString(1*inch, height - 1.05*inch, "Springfield Mutual Insurance Company - Claims Department")
    c.line(1*inch, height - 1.15*inch, width - 1*inch, height - 1.15*inch)

    c.setFont("Helvetica", 10)
    y = height - 1.5*inch

    def write_field(label, value, bold_label=True):
        nonlocal y
        if bold_label:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(1*inch, y, f"{label}:")
            c.setFont("Helvetica", 10)
            c.drawString(3*inch, y, str(value))
        else:
            c.drawString(1*inch, y, str(value))
        y -= 0.22*inch

    def write_section(title):
        nonlocal y
        y -= 0.15*inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, y, title)
        c.line(1*inch, y - 0.05*inch, width - 1*inch, y - 0.05*inch)
        y -= 0.3*inch
        c.setFont("Helvetica", 10)

    def write_wrapped(text, max_width=6.5):
        nonlocal y
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", 10) < max_width * inch:
                line = test
            else:
                c.drawString(1*inch, y, line)
                y -= 0.18*inch
                line = word
        if line:
            c.drawString(1*inch, y, line)
            y -= 0.18*inch

    write_section("CLAIM INFORMATION")
    write_field("Claim Number", claim_number)
    write_field("Date Filed", datetime.now().strftime("%Y-%m-%d"))
    write_field("Date of Incident", date_incident.strftime("%Y-%m-%d %H:%M"))
    write_field("Policy Number", policy_num)

    write_section("CLAIMANT INFORMATION")
    write_field("Full Name", name)
    write_field("Address", address)
    write_field("Phone", f"(555) {random.randint(100,999)}-{random.randint(1000,9999)}")
    write_field("Email", f"{name.lower().replace(' ', '.')}@email.com")

    write_section("VEHICLE INFORMATION")
    write_field("Vehicle", scenario["vehicle"])
    write_field("License Plate", scenario["plate"])
    write_field("VIN", f"{''.join(random.choices('0123456789ABCDEFGHJKLMNPRSTUVWXYZ', k=17))}")
    write_field("Mileage", f"{random.randint(5000, 85000):,} miles")

    write_section("INCIDENT DETAILS")
    write_field("Location", "")
    write_wrapped(scenario["location"])
    y -= 0.1*inch
    write_field("Description", "")
    write_wrapped(scenario["incident"])

    write_section("DAMAGE ASSESSMENT")
    write_wrapped(scenario["damage"])
    y -= 0.1*inch
    write_field("Estimated Repair Cost", f"${amount:,.2f}")
    write_field("Police Report", f"SPD-2024-{random.randint(10000, 99999)}")
    write_field("Tow Required", random.choice(["Yes - ABC Towing", "No"]))

    y -= 0.3*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y, "Claimant Signature: ________________________")
    c.drawString(4.5*inch, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    c.save()
    return amount


def generate_home_claim_pdf(output_path, claim_number, name, address, date_loss, scenario_idx):
    """Generate a realistic home insurance claim PDF."""
    scenario = HOME_SCENARIOS[scenario_idx % len(HOME_SCENARIOS)]
    amount = scenario.get("cost", random.randint(5000, 30000))
    policy_num = f"HOME-{random.randint(100000, 999999)}"

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(1*inch, height - 0.8*inch, "HOME INSURANCE CLAIM FORM")
    c.setFont("Helvetica", 9)
    c.drawString(1*inch, height - 1.05*inch, "Springfield Mutual Insurance Company - Property Claims Division")
    c.line(1*inch, height - 1.15*inch, width - 1*inch, height - 1.15*inch)

    c.setFont("Helvetica", 10)
    y = height - 1.5*inch

    def write_field(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*inch, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(3.2*inch, y, str(value))
        y -= 0.22*inch

    def write_section(title):
        nonlocal y
        y -= 0.15*inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, y, title)
        c.line(1*inch, y - 0.05*inch, width - 1*inch, y - 0.05*inch)
        y -= 0.3*inch
        c.setFont("Helvetica", 10)

    def write_wrapped(text, max_width=6.5):
        nonlocal y
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", 10) < max_width * inch:
                line = test
            else:
                c.drawString(1*inch, y, line)
                y -= 0.18*inch
                line = word
        if line:
            c.drawString(1*inch, y, line)
            y -= 0.18*inch

    write_section("CLAIM INFORMATION")
    write_field("Claim Number", claim_number)
    write_field("Date of Loss", date_loss.strftime("%Y-%m-%d"))
    write_field("Type of Loss", scenario["type"])
    write_field("Policy Number", policy_num)

    write_section("PROPERTY OWNER INFORMATION")
    write_field("Full Name", name)
    write_field("Property Address", address)
    write_field("Phone", f"(555) {random.randint(100,999)}-{random.randint(1000,9999)}")
    write_field("Email", f"{name.lower().replace(' ', '.')}@email.com")

    write_section("CAUSE OF LOSS")
    write_wrapped(scenario["cause"])

    write_section("DAMAGE DESCRIPTION")
    write_wrapped(scenario["damage"])

    write_section("COST ESTIMATE")
    write_field("Estimated Repair Cost", f"${amount:,.2f}")
    write_field("Emergency Repairs Done", random.choice([
        "Yes - Emergency plumber called",
        "Yes - Board-up service deployed",
        "Yes - Temporary tarp installed",
        "No emergency repairs needed"
    ]))
    write_field("Photos Attached", "Yes - 12 photos")
    write_field("Contractor Estimate", random.choice(["Pending", "Attached", "Scheduled for inspection"]))

    y -= 0.3*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y, "Property Owner Signature: ________________________")
    c.drawString(4.5*inch, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    c.save()
    return amount


def generate_medical_claim_pdf(output_path, claim_number, name, address, date_service, scenario_idx):
    """Generate a realistic medical insurance claim PDF."""
    scenario = MEDICAL_SCENARIOS[scenario_idx % len(MEDICAL_SCENARIOS)]
    amount = scenario.get("cost", random.randint(200, 5000))
    policy_num = f"MED-{random.randint(100000, 999999)}"

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(1*inch, height - 0.8*inch, "MEDICAL INSURANCE CLAIM FORM")
    c.setFont("Helvetica", 9)
    c.drawString(1*inch, height - 1.05*inch, "Springfield Mutual Insurance Company - Health Claims Processing")
    c.line(1*inch, height - 1.15*inch, width - 1*inch, height - 1.15*inch)

    c.setFont("Helvetica", 10)
    y = height - 1.5*inch

    def write_field(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*inch, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(3.2*inch, y, str(value))
        y -= 0.22*inch

    def write_section(title):
        nonlocal y
        y -= 0.15*inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, y, title)
        c.line(1*inch, y - 0.05*inch, width - 1*inch, y - 0.05*inch)
        y -= 0.3*inch
        c.setFont("Helvetica", 10)

    def write_wrapped(text, max_width=6.5):
        nonlocal y
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", 10) < max_width * inch:
                line = test
            else:
                c.drawString(1*inch, y, line)
                y -= 0.18*inch
                line = word
        if line:
            c.drawString(1*inch, y, line)
            y -= 0.18*inch

    write_section("CLAIM INFORMATION")
    write_field("Claim Number", claim_number)
    write_field("Date of Service", date_service.strftime("%Y-%m-%d"))
    write_field("Policy Number", policy_num)
    write_field("Group Number", f"GRP-{random.randint(1000, 9999)}")

    write_section("PATIENT INFORMATION")
    write_field("Patient Name", name)
    write_field("Date of Birth", f"{random.randint(1960, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}")
    write_field("Address", address)
    write_field("Phone", f"(555) {random.randint(100,999)}-{random.randint(1000,9999)}")

    write_section("PROVIDER INFORMATION")
    write_field("Provider Name", scenario["provider"])
    write_field("Attending Physician", scenario["doctor"])
    write_field("Provider NPI", scenario["npi"])
    write_field("Tax ID", f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}")

    write_section("DIAGNOSIS AND TREATMENT")
    write_field("Diagnosis", "")
    write_wrapped(scenario["diagnosis"])
    y -= 0.1*inch
    write_field("Services Rendered", "")
    write_wrapped(scenario["service"])

    write_section("CHARGES")
    write_field("Total Charges", f"${amount:,.2f}")
    copay = random.choice([20, 30, 40, 50, 75])
    write_field("Patient Copay", f"${copay:.2f}")
    write_field("Amount Claimed", f"${amount - copay:,.2f}")
    write_field("Prior Authorization", random.choice(["Not Required", f"Auth #{random.randint(100000, 999999)}"]))

    y -= 0.3*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y, "Patient Signature: ________________________")
    c.drawString(4.5*inch, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    c.save()
    return amount


def generate_construction_sinistre_pdf(output_path):
    """Generate the construction damage claim PDF (CLM-ENT-001)."""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 0.8*inch, "DECLARATION DE SINISTRE")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, height - 1.1*inch, "Entreprise Construction IDF")
    c.setFont("Helvetica", 9)
    c.drawString(1*inch, height - 1.3*inch, "Tous Risques Chantier - Contrat CTR-ENT-RC-2024")
    c.line(1*inch, height - 1.4*inch, width - 1*inch, height - 1.4*inch)

    y = height - 1.8*inch
    c.setFont("Helvetica", 10)

    def write_field(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*inch, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(3.2*inch, y, str(value))
        y -= 0.22*inch

    def write_section(title):
        nonlocal y
        y -= 0.15*inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, y, title)
        c.line(1*inch, y - 0.05*inch, width - 1*inch, y - 0.05*inch)
        y -= 0.3*inch
        c.setFont("Helvetica", 10)

    def write_text(text):
        nonlocal y
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", 10) < 6.5 * inch:
                line = test
            else:
                c.drawString(1*inch, y, line)
                y -= 0.18*inch
                line = word
        if line:
            c.drawString(1*inch, y, line)
            y -= 0.18*inch

    def write_bullet(text):
        nonlocal y
        c.drawString(1.2*inch, y, f"- {text}")
        y -= 0.2*inch

    write_section("INFORMATIONS GENERALES")
    write_field("Assure", "Entreprise Construction IDF")
    write_field("Contrat", "CTR-ENT-RC-2024 (Tous Risques Chantier)")
    write_field("Declarant", "Jean Martin, Directeur de Projets")
    write_field("Contact", "jean.martin@company-btp.fr / 06 12 34 56 78")
    write_field("Date du sinistre", "20/07/2025")
    write_field("Lieu", "Chantier complexe sportif, Cergy-Pontoise (95)")
    write_field("Ref. Projet", "PROJ-2025-CERGY-001")

    write_section("DESCRIPTION DES FAITS")
    write_text(
        "Le 20 juillet 2025 a 14h30, lors des travaux de coffrage du premier etage du batiment "
        "principal, une dalle de plancher de 120m2 s'est effondree partiellement. L'effondrement "
        "est survenu dans la zone B du batiment, affectant la structure porteuse sur environ 200m2."
    )
    y -= 0.1*inch
    write_text(
        "Aucun blesse n'a ete a deplorer grace a l'evacuation preventive ordonnee par le chef de "
        "chantier M. Philippe Leroy (06 98 76 54 32) qui avait detecte des fissures suspectes "
        "30 minutes avant l'incident."
    )

    write_section("DOMMAGES CONSTATES")
    write_bullet("Dalle de plancher R+1 zone B: destruction totale (120m2)")
    write_bullet("Etaiements et coffrages: destruction")
    write_bullet("Ferraillage: deformation, a remplacer")
    write_bullet("Structure porteuse: fissuration, expertise necessaire")
    write_bullet("Materiel de chantier enseveli: grue a tour endommagee")

    write_section("ESTIMATION PROVISOIRE DES DOMMAGES: 850 000 EUR")
    write_bullet("Reconstruction dalle et structure: 520 000 EUR")
    write_bullet("Reparation/remplacement materiel: 180 000 EUR")
    write_bullet("Retard chantier (penalites): 150 000 EUR")

    write_section("MESURES PRISES")
    write_bullet("Arret immediat du chantier zone B")
    write_bullet("Mise en securite du perimetre")
    write_bullet("Expert BET missionne (Bureau Veritas)")
    write_bullet("Declaration CRAM effectuee")

    y -= 0.3*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y, "Signature du declarant: ________________________")
    c.drawString(4.5*inch, y, "Date: 22/07/2025")

    c.save()


def main():
    # Resolve output directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    output_dir = os.path.join(project_root, "documents", "claims")
    os.makedirs(output_dir, exist_ok=True)

    base_date = datetime(2025, 10, 1)
    count = 0

    print(f"Generating claim PDFs to: {output_dir}\n")

    # 20 auto claims
    print("Auto Insurance Claims (20):")
    for i in range(1, 21):
        claim_number = f"CLM-2024-AUTO-{i:03d}"
        name = NAMES[(i - 1) % len(NAMES)]
        address = ADDRESSES[(i - 1) % len(ADDRESSES)]
        date_incident = base_date + timedelta(days=random.randint(0, 120))
        pdf_path = os.path.join(output_dir, f"claim_auto_{i:03d}.pdf")
        generate_auto_claim_pdf(pdf_path, claim_number, name, address, date_incident, i - 1)
        size = os.path.getsize(pdf_path)
        print(f"  {claim_number} -> claim_auto_{i:03d}.pdf ({size:,} bytes)")
        count += 1

    # 15 home claims
    print("\nHome Insurance Claims (15):")
    for i in range(1, 16):
        claim_number = f"CLM-2024-HOME-{i:03d}"
        name = NAMES[(i - 1) % len(NAMES)]
        address = ADDRESSES[(i - 1) % len(ADDRESSES)]
        date_loss = base_date + timedelta(days=random.randint(0, 120))
        pdf_path = os.path.join(output_dir, f"claim_home_{i:03d}.pdf")
        generate_home_claim_pdf(pdf_path, claim_number, name, address, date_loss, i - 1)
        size = os.path.getsize(pdf_path)
        print(f"  {claim_number} -> claim_home_{i:03d}.pdf ({size:,} bytes)")
        count += 1

    # 15 medical claims
    print("\nMedical Insurance Claims (15):")
    for i in range(1, 16):
        claim_number = f"CLM-2024-MED-{i:03d}"
        name = NAMES[(i - 1) % len(NAMES)]
        address = ADDRESSES[(i - 1) % len(ADDRESSES)]
        date_service = base_date + timedelta(days=random.randint(0, 120))
        pdf_path = os.path.join(output_dir, f"claim_medical_{i:03d}.pdf")
        generate_medical_claim_pdf(pdf_path, claim_number, name, address, date_service, i - 1)
        size = os.path.getsize(pdf_path)
        print(f"  {claim_number} -> claim_medical_{i:03d}.pdf ({size:,} bytes)")
        count += 1

    # Construction sinistre (harmonized scenario)
    print("\nConstruction Damage Claim:")
    pdf_path = os.path.join(output_dir, "clm-ent-001-sinistre.pdf")
    generate_construction_sinistre_pdf(pdf_path)
    size = os.path.getsize(pdf_path)
    print(f"  CLM-ENT-001 -> clm-ent-001-sinistre.pdf ({size:,} bytes)")
    count += 1

    print(f"\nGenerated {count} claim PDFs in {output_dir}")


if __name__ == "__main__":
    main()
