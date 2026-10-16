"""English versions of the tender documents (generate_tender_pdfs.py renders them as <file>_en.pdf).

The French documents are the originals: the agent reads them, the English ones are for English
readers. Names (clients, places, regions, certifications) are not translated.
"""
import re

# Text of the form itself, in both languages (French: as in the original documents)
FORM = {
    "fr": {
        "country": "REPUBLIQUE FRANCAISE", "notice": "AVIS D'APPEL PUBLIC A LA CONCURRENCE", "contract": "Marche n",
        "subject": "Objet", "a1": "ARTICLE 1 - IDENTIFICATION DU POUVOIR ADJUDICATEUR", "client": "Maitre d'ouvrage",
        "representative": "Representant", "contact": "Contact", "region": "Region",
        "a2": "ARTICLE 2 - OBJET DU MARCHE", "nature": "Nature du marche", "amount": "Montant estimatif",
        "delay": "Delai d'execution",
        "a3": "ARTICLE 3 - CONDITIONS DE PARTICIPATION",
        "requirements": "Les candidats devront satisfaire aux exigences suivantes :",
        "a4": "ARTICLE 4 - CRITERES D'ATTRIBUTION",
        "criteria": "Les offres seront jugees selon les criteres ponderes suivants :",
        "a5": "ARTICLE 5 - MODALITES DE REMISE DES OFFRES", "deadline": "Date limite de remise",
        "submission": ("Les offres devront etre transmises par voie electronique via la plateforme "
                       "de dematerialisation des marches publics. Les candidats sont invites a "
                       "deposer leurs plis dans les delais impartis. Tout pli recu hors delai "
                       "sera declare irrecevable."),
        "variants": ("Les variantes sont autorisees sous reserve de presenter une offre de base "
                     "conforme au cahier des charges. Les offres seront redigees en langue francaise. "
                     "Le delai de validite des offres est fixe a 120 jours."),
        "a6": "ARTICLE 6 - COMPOSITION DU DOSSIER DE CONSULTATION (DCE)",
        "documents": "Le dossier de consultation comprend les pieces suivantes :", "document": "Piece",
        "a7": "ARTICLE 7 - RENSEIGNEMENTS COMPLEMENTAIRES",
        "questions": ("Pour tout renseignement complementaire, les candidats sont invites a adresser "
                      "leurs questions par ecrit a {contact} "
                      "au plus tard 10 jours avant la date limite de remise des offres."),
        "answers": ("Les reponses aux questions seront communiquees a l'ensemble des candidats "
                    "via la plateforme de dematerialisation."),
        "footer_contract": "Marche", "footer": "Document genere dans le cadre de la procedure de mise en concurrence",
    },
    "en": {
        "country": "FRENCH REPUBLIC", "notice": "CONTRACT NOTICE - CALL FOR TENDERS", "contract": "Contract no.",
        "subject": "Subject", "a1": "ARTICLE 1 - CONTRACTING AUTHORITY", "client": "Client",
        "representative": "Representative", "contact": "Contact", "region": "Region",
        "a2": "ARTICLE 2 - SUBJECT OF THE CONTRACT", "nature": "Type of contract", "amount": "Estimated amount",
        "delay": "Completion time",
        "a3": "ARTICLE 3 - CONDITIONS OF PARTICIPATION",
        "requirements": "Candidates must meet the following requirements:",
        "a4": "ARTICLE 4 - AWARD CRITERIA",
        "criteria": "Tenders will be assessed against the following weighted criteria:",
        "a5": "ARTICLE 5 - SUBMISSION OF TENDERS", "deadline": "Submission deadline",
        "submission": ("Tenders must be submitted electronically through the public procurement platform. "
                       "Candidates are asked to submit their bids within the time limit. Any bid received "
                       "after the deadline will be rejected."),
        "variants": ("Variants are allowed provided that a base tender compliant with the specifications is "
                     "also submitted. Tenders shall be written in French. Tenders remain valid for 120 days."),
        "a6": "ARTICLE 6 - TENDER DOCUMENTS (DCE)",
        "documents": "The tender file contains the following documents:", "document": "Document",
        "a7": "ARTICLE 7 - FURTHER INFORMATION",
        "questions": ("For any further information, candidates should send their questions in writing to "
                      "{contact} no later than 10 days before the submission deadline."),
        "answers": "The answers will be sent to all candidates through the procurement platform.",
        "footer_contract": "Contract", "footer": "Document issued as part of the competitive tendering procedure",
    },
}

CRITERIA = {"Valeur technique": "Technical merit", "Prix": "Price", "Delai": "Lead time"}

# Values shared by the compact tenders (generate_tender_pdfs._EXTRA_TENDERS)
COMMON = {
    "Marche public de travaux": "Public works contract",
    "Qualibat requise": "Qualibat certification required",
    "ISO 14001 souhaitee": "ISO 14001 preferred",
    "References similaires exigees": "Similar references required",
    "Acte d'engagement": "Tender form (AE)",
    "CCAP": "Special administrative clauses (CCAP)",
    "CCTP": "Special technical clauses (CCTP)",
    "BPU et DQE": "Unit price schedule and bill of quantities (BPU, DQE)",
    "Plans": "Drawings",
}

DETAILED = {
    "AO-2025-IDF-003": {
        "titre": "Construction of a municipal sports complex",
        "representant": "Mr Pierre Dubois, Mayor",
        "nature": "Public works contract - Single lot - All trades",
        "description": ("The contract covers the construction of a municipal sports complex with a type B "
                        "multi-sports hall (40 m x 20 m), a gymnastics hall, changing rooms and toilets, a "
                        "reception hall, offices and an 80-space car park. The structure will be reinforced "
                        "concrete with a glued laminated timber frame for the roof of the main hall."),
        "exigences": ["Qualibat 2111 certification (structural works)", "NF EN ISO 14001 certification",
                      "Similar references (at least 3 over 5 years)", "Minimum turnover: EUR 10M per year",
                      "Valid ten-year liability insurance (garantie decennale)"],
        "pieces": ["Tender form (AE)", "Special administrative clauses (CCAP)", "Special technical clauses (CCTP)",
                   "Unit price schedule (BPU)", "Bill of quantities (DQE)", "Architectural and technical drawings",
                   "G2 AVP geotechnical report"],
    },
    "AO-2026-0042": {
        "titre": "Construction of 80 flats - ANRU programme in Nanterre",
        "representant": "Mrs Sophie Bernard, Director of Planning",
        "nature": "Public works contract - Several lots",
        "description": ("Construction of 80 flats, 30% of them social housing, as part of the ANRU programme of "
                        "the Parc Sud district in Nanterre. The project comprises two buildings (7 and 5 storeys) "
                        "over a shared underground car park. NF Habitat HQE certification and the E+C- label at "
                        "level E3C1 are required. The buildings will use low-carbon CEM III/B concrete with "
                        "timber-frame facades and bio-sourced insulation."),
        "exigences": ["NF Habitat HQE", "E+C- label, level E3C1", "Low-carbon CEM III concrete",
                      "References in multi-family housing (3 projects of more than 50 flats)",
                      "Minimum turnover: EUR 15M per year"],
        "pieces": ["Tender form (AE) per lot", "CCAP", "CCTP - Lot 1 Structural works", "CCTP - Lot 2 Roof structure",
                   "CCTP - Lot 3 Facades", "BPU and DQE per lot", "Architectural drawings (APD)",
                   "RE2020 thermal study"],
    },
    "AO-2026-0043": {
        "titre": "Refurbishment of the Sequoia office tower - La Defense",
        "representant": "Mr Laurent Michaud, Technical Director",
        "nature": "Private contract - Single lot, all trades except HVAC",
        "description": ("Refurbishment of floors 3 to 8 of the Sequoia tower (6 floors of 800 m2 each). The works "
                        "include full strip-out of the floors, repair of the raised technical floors and acoustic "
                        "ceilings, complete replacement of the power and low-voltage networks, painting and floor "
                        "coverings. The works will be carried out in a partly occupied building (floors 9 to 15 "
                        "in use)."),
        "exigences": ["Experience of works in occupied buildings required", "Shifted working hours allowed: 6:00-22:00",
                      "ISO 14001 certification required",
                      "References in office refurbishment (3 projects over 3,000 m2)",
                      "Waste management plan (target: 70% recovered)"],
        "pieces": ["Tender form (AE)", "CCAP", "CCTP", "BPU and DQE", "Floor location plans",
                   "Asbestos survey before works (DAT)", "Energy audit report"],
    },
    "AO-2026-0044": {
        "titre": "Design and build of the Nelson Mandela municipal gymnasium - Villeurbanne",
        "representant": "Mr Ahmed Benaissa, Deputy Mayor for Urban Planning",
        "nature": "Public contract - Design and build",
        "description": ("Design and build of a type B multi-sports gymnasium with a 500-seat stand, a dance hall "
                        "(200 m2), a dojo (150 m2) and rooms for local associations. The structure will combine "
                        "concrete and glued laminated timber, with photovoltaic panels on the roof (target: 30 kWp). "
                        "The project must meet the RE2020 requirements in advance and include rainwater harvesting "
                        "for watering the green spaces."),
        "exigences": ["Integrated design team required (architect + structural and building services engineers)",
                      "RE2020 in advance", "Qualibat 2112 required for the structural works",
                      "Experience in sports facilities (at least 2 references)", "BREEAM or HQE certification preferred"],
        "pieces": ["Tender form (AE)", "CCAP", "Detailed functional programme", "Method statement and schedule",
                   "Architectural sketch (plans and perspectives)", "Technical note on structure and services",
                   "Detailed cost estimate"],
    },
    "AO-2026-0045": {
        "titre": "Replacement of engineering structure no. 47 - A86/A4 interchange, Joinville-le-Pont",
        "representant": "Mr Francois Lemoine, Head of the Engineering Structures Department",
        "nature": "Public works contract - Single lot",
        "description": ("Demolition and reconstruction of engineering structure no. 47 (post-tensioned prestressed "
                        "concrete slab bridge, 3 spans, 85 m long, 14 m wide) at the A86/A4 interchange in "
                        "Joinville-le-Pont. The works will be carried out under traffic, with lane switches and "
                        "night closures. Deep foundations on 18 m bored piles in the Marne alluvium. Strong "
                        "constraint: the nearby Marne (flood risk, cofferdams needed)."),
        "exigences": ["MASE certification required", "Qualibat 2112 required (higher technical level)",
                      "Temporary signage plan approved by the DiRIF", "Experience of night works under traffic",
                      "References in engineering structures (3 structures over 50 m in 5 years)",
                      "Prestressed concrete approvals"],
        "pieces": ["Tender form (AE)", "CCAP and CCTP", "BPU and DQE", "Structure execution drawings (PEO)",
                   "Prestressed concrete calculation note", "G2 PRO geotechnical study",
                   "Phasing and temporary signage plan", "Quality assurance plan (PAQ)"],
    },
    "AO-2026-0046": {
        "titre": "Development of the Bordeaux Euratlantique ZAC - Armagnac sector, phase 3",
        "representant": "Mrs Catherine Dufour, Director of Operations",
        "nature": "Public works contract - Several lots",
        "description": ("Roads and utilities for phase 3 of the Armagnac sector (8.5 hectares): main and access roads "
                        "(2,400 m), separate sewer networks with integrated rainwater management (planted swales, "
                        "rain gardens), dry networks (HV/LV power, FTTH telecoms, gas), smart LED street lighting "
                        "(120 lighting points), green spaces (12,000 m2) and a landscaped promenade along the Garonne "
                        "(800 m). Social inclusion clause required (10% of the hours)."),
        "exigences": ["ISO 14001 required", "Qualibat 1311 required (roads and utilities)",
                      "Reuse of demolition materials above 50%", "Social inclusion clause: 10% of production hours",
                      "References in urban development (3 projects over 5 ha)", "Site environmental management plan"],
        "pieces": ["Tender form (AE) per lot", "CCAP", "CCTP - Lot 1 Roads and drainage",
                   "CCTP - Lot 2 Dry networks and street lighting", "CCTP - Lot 3 Green spaces and street furniture",
                   "BPU and DQE per lot", "Existing networks drawings", "Networks coordination plan",
                   "Environmental notice"],
    },
}

# Compact tenders: (title, description)
EXTRA = {
    "AO-2026-0047": ("Construction of the cruise quay of the Port of Toulon",
                     "Construction of a new 400 m deep-water cruise quay with a platform on bored piles in the sea."),
    "AO-2026-0048": ("Construction of the Paul Eluard primary school - Saint-Pierre, La Reunion",
                     "Construction of a 12-class primary school with a canteen and a covered playground. "
                     "Cyclone- and earthquake-resistant structure."),
    "AO-2026-0049": ("Reinforcement of the raft and containment building - Blayais nuclear power plant",
                     "Reinforcement of the raft and the containment building of reactor no. 2 of the Blayais nuclear "
                     "power plant, as part of the Grand Carenage programme."),
    "AO-2026-0050": ("Construction of 95 flats - ZAC des Girondins, Lyon",
                     "Construction of 95 flats in two buildings (8 and 6 storeys) with shops on the ground floor and a "
                     "two-level underground car park."),
    "AO-2026-0051": ("Construction of a hyperscale data centre - Lisses digital campus",
                     "Construction of a hyperscale data centre with 8,000 m2 of IT space and 32 MW of power."),
    "AO-2026-0052": ("Construction of a 600-pupil secondary school - Tourcoing",
                     "Construction of a secondary school for 600 pupils with a canteen, a gymnasium and outdoor areas."),
    "AO-2026-0053": ("Redevelopment of the place de la Comedie - Montpellier",
                     "Redevelopment of the place de la Comedie into a pedestrian area, with the networks renewed."),
    "AO-2026-0054": ("Extension of the Fleury Michon food factory - Pouzauges",
                     "5,000 m2 extension with cold rooms and a production area."),
    "AO-2026-0055": ("Construction of a footbridge over the Ill - Strasbourg",
                     "120 m pedestrian and cycle bridge in composite steel and concrete."),
    "AO-2026-0056": ("Framework agreement for the maintenance of engineering structures - DIRIF",
                     "4-year framework agreement for the maintenance and repair of the engineering structures of "
                     "the national road network in Ile-de-France."),
    "AO-2026-0057": ("120-bed nursing home (EHPAD) - Aix-en-Provence",
                     "Construction of a 120-bed nursing home on 4 storeys with therapeutic gardens."),
    "AO-2026-0058": ("Olympic swimming pool - Chambery",
                     "Olympic swimming pool with a 50 m competition pool, a leisure pool and a wellness area."),
    "AO-2026-0059": ("Tramway line D - Bordeaux Lac section",
                     "Construction of 3.5 km of tramway track with 4 stations and 2 civil engineering structures."),
    "AO-2026-0060": ("Refurbishment of the Vauban barracks - Lille",
                     "Refurbishment of the Vauban barracks into a cultural and community centre."),
    "AO-2026-0061": ("26-storey residential tower - Ivry-sur-Seine",
                     "Tower of 180 flats on 26 storeys with a three-level underground car park. Reinforced concrete "
                     "structure with shear-wall cores."),
    "AO-2026-0062": ("80,000 PE wastewater treatment plant - Perpignan",
                     "Construction of a wastewater treatment plant for 80,000 population equivalent with biological "
                     "treatment and odour control."),
    "AO-2026-0063": ("250-unit student residence - Rennes",
                     "Student residence of 250 studios and one-bedroom flats on 7 storeys with shared areas and a "
                     "bicycle room."),
    "AO-2026-0064": ("RD83 bypass - Colmar",
                     "4.2 km single-carriageway bypass with a roundabout and an underpass."),
    "AO-2026-0065": ("5-star hotel with 200 rooms - Cannes, La Croisette",
                     "Construction of a 5-star luxury hotel with 200 rooms on 9 storeys, with a spa and a panoramic "
                     "restaurant."),
    "AO-2026-0066": ("800-space multi-storey car park - Part-Dieu station, Lyon",
                     "Multi-storey car park with 800 spaces on 7 levels, prestressed concrete structure and green "
                     "facade."),
    "AO-2026-0067": ("15-class school group - Saclay",
                     "School group of 15 classes with a school restaurant and a type C gymnasium."),
    "AO-2026-0068": ("Intermunicipal aquatic centre - Anglet",
                     "Aquatic centre with a 25 m competition pool, a leisure pool and a wellness area."),
    "AO-2026-0069": ("Framework agreement for the energy renovation of high schools - Hauts-de-France region",
                     "4-year framework agreement for the energy renovation of 25 high schools."),
    "AO-2026-0070": ("Cable-stayed bridge over the Tarn - Millau",
                     "Cable-stayed bridge with a 250 m main span and an 80 m pylon."),
    "AO-2026-0071": ("Amazon logistics centre - Metz Actipole",
                     "45,000 m2 logistics centre with a mezzanine and loading docks."),
}


def amount_en(amount: str) -> str:
    """"8 000 000 EUR HT (estimation tous lots)" -> "EUR 8,000,000 excl. VAT (estimate, all lots)"."""
    match = re.match(r"([\d ]+) EUR HT(.*)", amount)
    value = int(match.group(1).replace(" ", ""))
    extra = match.group(2).replace("(estimation tous lots)", "(estimate, all lots)")
    return f"EUR {value:,} excl. VAT{extra}"


def delay_en(delay: str) -> str:
    """"18 mois a compter de l'ordre de service" -> "18 months from the start order"."""
    return (delay.replace(" mois a compter de l'ordre de service", " months from the start order")
                 .replace(" mois (conception + realisation)", " months (design + build)"))


def english(tender: dict) -> dict:
    """The tender's fields in English."""
    number = tender["numero"]
    if number in DETAILED:
        translated = dict(DETAILED[number])
    else:
        title, description = EXTRA[number]
        translated = {
            "titre": title, "description": description,
            "representant": tender["representant"].replace("Service marches publics", "Procurement department"),
            "nature": COMMON[tender["nature"]],
            "exigences": [COMMON[e] for e in tender["exigences"]],
            "pieces": [COMMON[p] for p in tender["pieces"]],
        }
    return {**tender, **translated,
            "montant": amount_en(tender["montant"]),
            "delai": delay_en(tender["delai"]),
            "date_limite": tender["date_limite"].replace(" a ", " at ").replace("h", ":"),
            "criteres": {CRITERIA[k]: v for k, v in tender["criteres"].items()}}
