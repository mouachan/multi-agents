"""Generate realistic PDF documents for claims and tenders using reportlab."""

import logging
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

STYLES = getSampleStyleSheet()


def _title_style():
    return ParagraphStyle(
        "CustomTitle", parent=STYLES["Title"], fontSize=16, spaceAfter=12
    )


def _heading_style():
    return ParagraphStyle(
        "CustomHeading", parent=STYLES["Heading2"], fontSize=12, spaceAfter=8
    )


def _body_style():
    return ParagraphStyle(
        "CustomBody", parent=STYLES["Normal"], fontSize=10, leading=14
    )


# ============================================================================
# Claim PDF content templates
# ============================================================================

CLAIM_TEMPLATES = {
    "Medical": {
        "title": "DECLARATION DE SINISTRE MEDICAL",
        "sections": [
            ("Informations patient", [
                "Patient: {user_name}",
                "Contrat: {contract_number}",
                "Date du sinistre: {date}",
            ]),
            ("Description des soins", [
                "Motif: Consultation et soins necessitant prise en charge",
                "Etablissement: Centre hospitalier regional",
                "Nature des soins: Consultation specialiste, examens complementaires",
                "Actes CCAM: YYYY001, YYYY042, YYYY187",
            ]),
            ("Montants", [
                "Honoraires medecin: 150,00 EUR",
                "Frais hospitalisation: 2 800,00 EUR",
                "Pharmacie: 245,50 EUR",
                "Total: 3 195,50 EUR",
            ]),
            ("Pieces jointes", [
                "- Factures detaillees",
                "- Feuille de soins",
                "- Justificatif Securite sociale",
                "- Ordonnances",
            ]),
        ],
    },
    "Auto": {
        "title": "DECLARATION DE SINISTRE AUTOMOBILE",
        "sections": [
            ("Informations conducteur", [
                "Conducteur: {user_name}",
                "Contrat: {contract_number}",
                "Date du sinistre: {date}",
                "Lieu: Voie publique",
            ]),
            ("Circonstances de l'accident", [
                "Description: Collision entre vehicules",
                "Conditions: Chaussee seche, visibilite normale",
                "Vehicule assure: {vehicle}",
                "Tiers implique: Oui / Non selon rapport",
            ]),
            ("Degats constates", [
                "Pare-chocs avant: endommage",
                "Capot: deforme",
                "Phare droit: casse",
                "Estimation reparations: 4 500,00 EUR",
            ]),
            ("Documents fournis", [
                "- Constat amiable signe",
                "- Photos des degats (6 photos)",
                "- Rapport de police si applicable",
                "- Carte grise du vehicule",
            ]),
        ],
    },
    "Home": {
        "title": "DECLARATION DE SINISTRE HABITATION",
        "sections": [
            ("Informations assure", [
                "Assure: {user_name}",
                "Contrat: {contract_number}",
                "Date du sinistre: {date}",
                "Adresse du bien: {address}",
            ]),
            ("Description des degats", [
                "Nature: Degats des eaux / Tempete / Vol",
                "Zone affectee: Parties communes et/ou privatives",
                "Etendue: Plusieurs pieces touchees",
                "Cause identifiee: A determiner par expert",
            ]),
            ("Estimation des dommages", [
                "Structure: 3 200,00 EUR",
                "Mobilier: 1 800,00 EUR",
                "Frais de remise en etat: 2 500,00 EUR",
                "Total estime: 7 500,00 EUR",
            ]),
            ("Mesures conservatoires", [
                "- Mise en securite du bien",
                "- Photos avant/apres (12 photos jointes)",
                "- Factures des reparations d'urgence",
                "- Devis de remise en etat",
            ]),
        ],
    },
    "Life": {
        "title": "DECLARATION DE SINISTRE ASSURANCE VIE",
        "sections": [
            ("Informations beneficiaire", [
                "Beneficiaire: {user_name}",
                "Contrat: {contract_number}",
                "Date de l'evenement: {date}",
            ]),
            ("Nature de la declaration", [
                "Type: Invalidite permanente / Deces",
                "Circonstances: Declaration conforme aux conditions du contrat",
                "Certificat medical: Joint a la declaration",
            ]),
            ("Capital souscrit", [
                "Capital: Selon conditions du contrat",
                "Franchise: Aucune",
                "Delai de carence: Echu",
            ]),
            ("Pieces jointes", [
                "- Certificat medical ou acte de deces",
                "- Justificatif d'identite du beneficiaire",
                "- RIB pour versement",
            ]),
        ],
    },
}


TENDER_TEMPLATES = {
    "default": {
        "title": "APPEL D'OFFRES - {tender_number}",
        "sections": [
            ("Identification du marche", [
                "Numero: {tender_number}",
                "Maitre d'ouvrage: {maitre_ouvrage}",
                "Nature des travaux: {nature_travaux}",
                "Type de marche: {tender_type}",
            ]),
            ("Caracteristiques du projet", [
                "Localisation: {commune}, {region}",
                "Montant estimatif: {montant_estime} EUR HT",
                "Delai d'execution: {delai_mois} mois",
                "Date limite de remise: {date_limite}",
            ]),
            ("Criteres d'attribution", [
                "- Valeur technique: {technique}%",
                "- Prix: {prix}%",
                "- Delai: {delai_pct}%",
            ]),
            ("Description des travaux", [
                "{description}",
            ]),
            ("Exigences specifiques", [
                "{exigences}",
            ]),
        ],
    },
}


# Vehicle names for variety
VEHICLES = [
    "Peugeot 3008", "Renault Megane", "BMW Serie 3", "Toyota Yaris",
    "Audi A4", "Citroen C4", "Volkswagen Golf", "Ford Focus",
    "Mercedes Classe A", "Dacia Sandero", "Peugeot 308",
]


def _build_claim_pdf(filepath: str, claim_number: str, claim_type: str,
                     user_name: str, contract_number: str, submitted_at: str,
                     address: str = "Lyon, France"):
    """Generate a single claim PDF."""
    template = CLAIM_TEMPLATES.get(claim_type, CLAIM_TEMPLATES["Medical"])

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    # Title
    story.append(Paragraph(template["title"], _title_style()))
    story.append(Spacer(1, 0.5 * cm))

    # Reference box
    ref_data = [
        ["Reference", claim_number],
        ["Type", claim_type],
        ["Date", submitted_at[:10] if submitted_at else "2025-11-15"],
    ]
    ref_table = Table(ref_data, colWidths=[4 * cm, 10 * cm])
    ref_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 0.8 * cm))

    # Idx for vehicle selection
    idx = int(claim_number.split("-")[-1]) if "-" in claim_number else 0
    vehicle = VEHICLES[idx % len(VEHICLES)]

    # Sections
    for heading, lines in template["sections"]:
        story.append(Paragraph(heading, _heading_style()))
        for line in lines:
            formatted = line.format(
                user_name=user_name,
                contract_number=contract_number,
                date=submitted_at[:10] if submitted_at else "2025-11-15",
                vehicle=vehicle,
                address=address,
            )
            story.append(Paragraph(formatted, _body_style()))
        story.append(Spacer(1, 0.4 * cm))

    # Footer
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"Document genere pour la demande {claim_number}. "
        "Ce document est confidentiel et destine exclusivement a l'usage interne.",
        ParagraphStyle("Footer", parent=STYLES["Normal"], fontSize=8,
                       textColor=colors.grey),
    ))

    doc.build(story)
    logger.debug(f"Generated claim PDF: {filepath}")


def _build_tender_pdf(filepath: str, tender_number: str, metadata: dict):
    """Generate a single tender PDF."""
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    titre = metadata.get("titre", f"Appel d'offres {tender_number}")

    # Title
    story.append(Paragraph(
        f"APPEL D'OFFRES - {tender_number}", _title_style()
    ))
    story.append(Paragraph(titre, _heading_style()))
    story.append(Spacer(1, 0.5 * cm))

    # Reference box
    criteres = metadata.get("criteres_attribution", {})
    ref_data = [
        ["Numero", tender_number],
        ["Maitre d'ouvrage", metadata.get("maitre_ouvrage", "N/A")],
        ["Nature travaux", metadata.get("nature_travaux", "N/A")],
        ["Region", metadata.get("region", "N/A")],
        ["Montant estime", f"{metadata.get('montant_estime', 0):,.0f} EUR HT"],
        ["Delai", f"{metadata.get('delai_execution_mois', 0)} mois"],
        ["Date limite", metadata.get("date_limite_remise", "N/A")],
    ]
    ref_table = Table(ref_data, colWidths=[4 * cm, 10 * cm])
    ref_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 0.8 * cm))

    # Criteres d'attribution
    story.append(Paragraph("Criteres d'attribution", _heading_style()))
    for k, v in criteres.items():
        story.append(Paragraph(f"- {k.capitalize()}: {v}%", _body_style()))
    story.append(Spacer(1, 0.4 * cm))

    # Lots
    lots = metadata.get("lots", [])
    if lots:
        story.append(Paragraph("Lots", _heading_style()))
        for lot in lots:
            story.append(Paragraph(f"- {lot}", _body_style()))
        story.append(Spacer(1, 0.4 * cm))

    # Description
    description = metadata.get("description", "")
    if description:
        story.append(Paragraph("Description des travaux", _heading_style()))
        story.append(Paragraph(description, _body_style()))
        story.append(Spacer(1, 0.4 * cm))

    # Exigences
    exigences = metadata.get("exigences_specifiques", [])
    if exigences:
        story.append(Paragraph("Exigences specifiques", _heading_style()))
        for ex in exigences:
            story.append(Paragraph(f"- {ex}", _body_style()))
        story.append(Spacer(1, 0.4 * cm))

    # Maitre d'oeuvre
    moe = metadata.get("maitre_oeuvre", "")
    if moe:
        story.append(Paragraph("Maitre d'oeuvre", _heading_style()))
        story.append(Paragraph(moe, _body_style()))
        story.append(Spacer(1, 0.4 * cm))

    # Footer
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"Document de consultation - {tender_number}. "
        f"Source: {metadata.get('source', 'plateforme PLACE marches publics')}",
        ParagraphStyle("Footer", parent=STYLES["Normal"], fontSize=8,
                       textColor=colors.grey),
    ))

    doc.build(story)
    logger.debug(f"Generated tender PDF: {filepath}")


def generate_all_pdfs(
    claims_data: list[dict],
    tenders_data: list[dict],
    output_dir: str = "/tmp/documents",
) -> tuple[list[str], list[str]]:
    """
    Generate all claim and tender PDFs.

    Args:
        claims_data: list of dicts with keys: claim_number, claim_type, user_name,
                     contract_number, submitted_at, document_path, address
        tenders_data: list of dicts with keys: tender_number, metadata, document_path
        output_dir: base directory for generated PDFs

    Returns:
        (claim_pdf_paths, tender_pdf_paths)
    """
    claims_dir = os.path.join(output_dir, "claims")
    tenders_dir = os.path.join(output_dir, "tenders")
    os.makedirs(claims_dir, exist_ok=True)
    os.makedirs(tenders_dir, exist_ok=True)

    claim_paths = []
    for claim in claims_data:
        filename = Path(claim["document_path"]).name
        filepath = os.path.join(claims_dir, filename)
        _build_claim_pdf(
            filepath=filepath,
            claim_number=claim["claim_number"],
            claim_type=claim["claim_type"],
            user_name=claim.get("user_name", "Assure"),
            contract_number=claim.get("contract_number", "N/A"),
            submitted_at=claim.get("submitted_at", "2025-11-15"),
            address=claim.get("address", "France"),
        )
        claim_paths.append(filepath)

    tender_paths = []
    for tender in tenders_data:
        filename = Path(tender["document_path"]).name
        filepath = os.path.join(tenders_dir, filename)
        _build_tender_pdf(
            filepath=filepath,
            tender_number=tender["tender_number"],
            metadata=tender.get("metadata", {}),
        )
        tender_paths.append(filepath)

    logger.info(f"Generated {len(claim_paths)} claim PDFs and {len(tender_paths)} tender PDFs")
    return claim_paths, tender_paths
