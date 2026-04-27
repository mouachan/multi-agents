#!/usr/bin/env python3
"""
Generate realistic tender (Appel d'Offres) PDF documents for the multi-agents platform.
Outputs to documents/tenders/ with filenames matching the seed data.

Each PDF is a DCE (Dossier de Consultation des Entreprises) formatted
as a French public procurement document.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ============================================================================
# Tender data matching seed SQL (002_tender_seed_data.sql + 004_harmonized)
# ============================================================================
TENDERS = [
    {
        "filename": "ao-2025-idf-003-dce.pdf",
        "numero": "AO-2025-IDF-003",
        "titre": "Construction d'un complexe sportif municipal",
        "maitre_ouvrage": "Ville de Cergy-Pontoise",
        "representant": "M. Pierre Dubois, Maire",
        "contact": "p.dubois@cergy-pontoise.fr / 01 34 25 00 00",
        "nature": "Marche public de travaux - Lot unique - Tous corps d'etat",
        "montant": "4 200 000 EUR HT",
        "delai": "18 mois a compter de l'ordre de service",
        "date_limite": "28/02/2025 a 12h00",
        "criteres": {"Valeur technique": "60%", "Prix": "30%", "Delai": "10%"},
        "description": (
            "Le present marche a pour objet la construction d'un complexe sportif municipal "
            "comprenant une salle omnisports de type B (40m x 20m), une salle de gymnastique, "
            "des vestiaires et sanitaires, un hall d'accueil, des bureaux administratifs et un "
            "parking de 80 places. La structure sera en beton arme avec charpente bois lamelle-colle "
            "pour la couverture du hall principal."
        ),
        "exigences": [
            "Certification Qualibat 2111 (Gros oeuvre)",
            "Certification NF EN ISO 14001",
            "References similaires (3 minimum sur 5 ans)",
            "Chiffre d'affaires minimum: 10M EUR/an",
            "Garantie decennale en cours de validite",
        ],
        "pieces": [
            "Acte d'engagement (AE)",
            "Cahier des Clauses Administratives Particulieres (CCAP)",
            "Cahier des Clauses Techniques Particulieres (CCTP)",
            "Bordereau des Prix Unitaires (BPU)",
            "Detail Quantitatif Estimatif (DQE)",
            "Plans architecturaux et techniques",
            "Rapport geotechnique G2 AVP",
        ],
        "region": "Ile-de-France",
    },
    {
        "filename": "ao_2026_0042.pdf",
        "numero": "AO-2026-0042",
        "titre": "Construction de 80 logements collectifs - Programme ANRU Nanterre",
        "maitre_ouvrage": "Etablissement Public Territorial Paris Ouest La Defense",
        "representant": "Mme. Sophie Bernard, Directrice de l'Amenagement",
        "contact": "s.bernard@pold.fr / 01 47 21 55 00",
        "nature": "Marche public de travaux - Allotissement",
        "montant": "8 000 000 EUR HT (estimation tous lots)",
        "delai": "24 mois a compter de l'ordre de service",
        "date_limite": "15/03/2026 a 12h00",
        "criteres": {"Valeur technique": "50%", "Prix": "40%", "Delai": "10%"},
        "description": (
            "Construction de 80 logements collectifs dont 30% en logement social dans le "
            "cadre du programme ANRU du quartier du Parc Sud a Nanterre. Le projet comprend "
            "deux batiments R+6 et R+4 sur un parking souterrain commun. Certification NF "
            "Habitat HQE et label E+C- niveau E3C1 exiges. Les batiments seront realises en "
            "beton bas carbone CEM III/B avec facades a ossature bois et isolation biosourcee."
        ),
        "exigences": [
            "NF Habitat HQE",
            "Label E+C- niveau E3C1",
            "Beton bas carbone CEM III",
            "References en logements collectifs (3 operations > 50 logements)",
            "Chiffre d'affaires minimum: 15M EUR/an",
        ],
        "pieces": [
            "Acte d'engagement (AE) par lot",
            "CCAP",
            "CCTP - Lot 1 Gros oeuvre",
            "CCTP - Lot 2 Charpente couverture",
            "CCTP - Lot 3 Facades",
            "BPU et DQE par lot",
            "Plans architecturaux (APD)",
            "Etude thermique RE2020",
        ],
        "region": "Ile-de-France",
    },
    {
        "filename": "ao_2026_0043.pdf",
        "numero": "AO-2026-0043",
        "titre": "Rehabilitation de l'immeuble de bureaux Tour Sequoia - La Defense",
        "maitre_ouvrage": "Gecina",
        "representant": "M. Laurent Michaud, Directeur Technique",
        "contact": "l.michaud@gecina.fr / 01 40 40 52 00",
        "nature": "Marche prive - Lot unique TCE hors CVC",
        "montant": "3 500 000 EUR HT",
        "delai": "10 mois a compter de l'ordre de service",
        "date_limite": "28/03/2026 a 17h00",
        "criteres": {"Valeur technique": "45%", "Prix": "45%", "Delai": "10%"},
        "description": (
            "Rehabilitation des niveaux 3 a 8 de la Tour Sequoia (6 plateaux de 800 m2 chacun). "
            "Les travaux comprennent le curage complet des plateaux, la reprise des faux planchers "
            "techniques et faux plafonds acoustiques, le remplacement integral du reseau electrique "
            "courants forts et courants faibles, les peintures et les revetements de sol. Les travaux "
            "seront realises en site partiellement occupe (niveaux 9 a 15 en activite)."
        ),
        "exigences": [
            "Experience en travaux en site occupe obligatoire",
            "Horaires de travail decales autorises: 6h-22h",
            "Certification ISO 14001 exigee",
            "References en rehabilitation tertiaire (3 operations > 3000 m2)",
            "Plan de gestion des dechets (objectif 70% valorisation)",
        ],
        "pieces": [
            "Acte d'engagement",
            "CCAP",
            "CCTP",
            "BPU et DQE",
            "Plans de reperage par niveau",
            "Diagnostic amiante avant travaux (DAT)",
            "Rapport d'audit energetique",
        ],
        "region": "Ile-de-France",
    },
    {
        "filename": "ao_2026_0044.pdf",
        "numero": "AO-2026-0044",
        "titre": "Conception-realisation du gymnase municipal Nelson Mandela - Villeurbanne",
        "maitre_ouvrage": "Ville de Villeurbanne",
        "representant": "M. Ahmed Benaissa, Adjoint a l'Urbanisme",
        "contact": "a.benaissa@villeurbanne.fr / 04 78 54 32 10",
        "nature": "Marche public - Conception-realisation",
        "montant": "5 000 000 EUR HT",
        "delai": "18 mois (conception + realisation)",
        "date_limite": "10/04/2026 a 12h00",
        "criteres": {"Valeur technique": "55%", "Prix": "35%", "Delai": "10%"},
        "description": (
            "Conception et realisation d'un gymnase multisports de type B avec tribune de 500 places, "
            "salle de danse (200 m2), dojo (150 m2) et locaux associatifs. La structure sera mixte "
            "beton/bois lamelle-colle avec couverture photovoltaique en toiture (objectif 30 kWc). "
            "Le projet doit respecter les exigences RE2020 anticipees et integrer un systeme de "
            "recuperation des eaux de pluie pour l'arrosage des espaces verts."
        ),
        "exigences": [
            "Equipe de conception integree obligatoire (architecte + BET structure + BET fluides)",
            "RE2020 anticipee",
            "Qualibat 2112 exigee pour le gros oeuvre",
            "Experience en equipements sportifs (2 references minimum)",
            "Certification BREEAM ou HQE souhaitee",
        ],
        "pieces": [
            "Acte d'engagement",
            "CCAP",
            "Programme fonctionnel detaille",
            "Note methodologique et planning",
            "Esquisse architecturale (plans + perspectives)",
            "Note technique structure et fluides",
            "Estimation financiere detaillee",
        ],
        "region": "Auvergne-Rhone-Alpes",
    },
    {
        "filename": "ao_2026_0045.pdf",
        "numero": "AO-2026-0045",
        "titre": "Remplacement de l'ouvrage d'art n47 - Echangeur A86/A4 Joinville-le-Pont",
        "maitre_ouvrage": "Direction Interdepartementale des Routes d'Ile-de-France (DiRIF)",
        "representant": "M. Francois Lemoine, Chef du Service Ouvrages d'Art",
        "contact": "francois.lemoine@dirif.gouv.fr / 01 49 77 14 00",
        "nature": "Marche public de travaux - Lot unique",
        "montant": "12 000 000 EUR HT",
        "delai": "28 mois a compter de l'ordre de service",
        "date_limite": "25/04/2026 a 12h00",
        "criteres": {"Valeur technique": "55%", "Prix": "35%", "Delai": "10%"},
        "description": (
            "Demolition et reconstruction de l'ouvrage d'art n47 (pont-dalle en beton precontraint "
            "par post-tension, 3 travees, longueur totale 85 m, largeur 14 m) a l'echangeur A86/A4 "
            "a Joinville-le-Pont. Les travaux seront realises sous circulation avec basculements de "
            "voies et coupures de nuit. Les fondations profondes seront realisees sur pieux fores "
            "de 18 m dans les alluvions de la Marne. Contrainte forte de proximite de la Marne "
            "(risque inondation, batardeaux necessaires)."
        ),
        "exigences": [
            "MASE obligatoire",
            "Qualibat 2112 exigee (technicite superieure)",
            "Plan de signalisation temporaire approuve par la DiRIF",
            "Experience en travaux de nuit et sous circulation",
            "References en ouvrages d'art (3 OA > 50 m sur 5 ans)",
            "Agrements beton precontraint",
        ],
        "pieces": [
            "Acte d'engagement",
            "CCAP et CCTP",
            "BPU et DQE",
            "Plans d'execution de l'ouvrage (PEO)",
            "Note de calcul beton precontraint",
            "Etude geotechnique G2 PRO",
            "Plan de phasage et signalisation temporaire",
            "Plan d'Assurance Qualite (PAQ)",
        ],
        "region": "Ile-de-France",
    },
    {
        "filename": "ao_2026_0046.pdf",
        "numero": "AO-2026-0046",
        "titre": "Amenagement de la ZAC Bordeaux Euratlantique - Secteur Armagnac Phase 3",
        "maitre_ouvrage": "EPA Bordeaux Euratlantique",
        "representant": "Mme. Catherine Dufour, Directrice des Operations",
        "contact": "c.dufour@bordeaux-euratlantique.fr / 05 56 93 65 00",
        "nature": "Marche public de travaux - Allotissement",
        "montant": "7 000 000 EUR HT (estimation tous lots)",
        "delai": "16 mois a compter de l'ordre de service",
        "date_limite": "05/05/2026 a 12h00",
        "criteres": {"Valeur technique": "40%", "Prix": "45%", "Delai": "15%"},
        "description": (
            "Amenagement VRD de la phase 3 du secteur Armagnac (8,5 hectares) comprenant: "
            "voiries structurantes et de desserte (2 400 ml), reseaux d'assainissement separatifs "
            "avec gestion integree des eaux pluviales (noues vegetalisees, jardins de pluie), "
            "reseaux secs (electricite HTA/BT, telecoms FTTH, gaz), eclairage public LED intelligent "
            "(120 points lumineux), espaces verts (12 000 m2) et promenade paysagere le long de "
            "la Garonne (800 ml). Clause d'insertion sociale obligatoire (10% des heures)."
        ),
        "exigences": [
            "ISO 14001 exigee",
            "Qualibat 1311 exigee (VRD)",
            "Reemploi des materiaux de deconstruction > 50%",
            "Clause d'insertion sociale: 10% des heures de production",
            "References en amenagement urbain (3 operations > 5 ha)",
            "Plan de gestion environnementale du chantier",
        ],
        "pieces": [
            "Acte d'engagement par lot",
            "CCAP",
            "CCTP - Lot 1 Voirie et assainissement",
            "CCTP - Lot 2 Reseaux secs et eclairage public",
            "CCTP - Lot 3 Espaces verts et mobilier urbain",
            "BPU et DQE par lot",
            "Plans des reseaux existants",
            "Plan de coordination des reseaux",
            "Notice environnementale",
        ],
        "region": "Nouvelle-Aquitaine",
    },
]

# ============================================================================
# Additional tenders (0047-0071) - compact format with defaults
# ============================================================================
_EXTRA_TENDERS = [
    ("ao_2026_0047.pdf", "AO-2026-0047", "Construction du quai de croisiere du Port de Toulon", "Port Autonome de Toulon", "Provence-Alpes-Cote d'Azur", "25 000 000 EUR HT", 30, "Construction d'un nouveau quai de croisiere en eau profonde de 400 ml avec terre-plein sur pieux fores en milieu marin."),
    ("ao_2026_0048.pdf", "AO-2026-0048", "Construction ecole primaire Paul Eluard - Saint-Pierre de la Reunion", "Commune de Saint-Pierre (974)", "La Reunion", "3 200 000 EUR HT", 14, "Construction d'une ecole primaire de 12 classes avec cantine et preau. Structure paracyclonique et parasismique."),
    ("ao_2026_0049.pdf", "AO-2026-0049", "Confortement radier et enceinte de confinement - CNPE du Blayais", "EDF - Division Production Nucleaire", "Nouvelle-Aquitaine", "18 000 000 EUR HT", 36, "Confortement du radier et de l'enceinte de confinement du reacteur n2 du CNPE du Blayais dans le cadre du Grand Carenage."),
    ("ao_2026_0050.pdf", "AO-2026-0050", "Construction de 95 logements collectifs - ZAC des Girondins Lyon", "Lyon Metropole Habitat", "Auvergne-Rhone-Alpes", "11 500 000 EUR HT", 22, "Construction de 95 logements collectifs en 2 batiments R+7 et R+5 avec commerces en RDC et parking souterrain R-2."),
    ("ao_2026_0051.pdf", "AO-2026-0051", "Construction data center hyperscale - Campus digital de Lisses", "Equinix France", "Ile-de-France", "42 000 000 EUR HT", 20, "Construction d'un data center hyperscale de 8 000 m2 IT avec puissance electrique de 32 MW."),
    ("ao_2026_0052.pdf", "AO-2026-0052", "Construction college 600 eleves - Tourcoing", "Departement du Nord", "Hauts-de-France", "9 500 000 EUR HT", 20, "Construction d'un college de 600 eleves avec demi-pension, gymnase et espaces exterieurs."),
    ("ao_2026_0053.pdf", "AO-2026-0053", "Amenagement place de la Comedie - Montpellier", "Montpellier Mediterranee Metropole", "Occitanie", "4 800 000 EUR HT", 12, "Reamenagement de la place de la Comedie avec pietonisation et reprise des reseaux."),
    ("ao_2026_0054.pdf", "AO-2026-0054", "Extension usine agroalimentaire Fleury Michon - Pouzauges", "Fleury Michon SA", "Pays de la Loire", "15 000 000 EUR HT", 16, "Extension de 5 000 m2 avec chambres froides et zone de production."),
    ("ao_2026_0055.pdf", "AO-2026-0055", "Construction passerelle pietonne sur l'Ill - Strasbourg", "Eurometropole de Strasbourg", "Grand Est", "6 500 000 EUR HT", 14, "Passerelle pietonne et cyclable de 120 m en structure mixte acier-beton."),
    ("ao_2026_0056.pdf", "AO-2026-0056", "Accord-cadre maintenance ouvrages d'art - DIRIF", "Direction Interdepartementale des Routes IDF", "Ile-de-France", "8 000 000 EUR HT", 48, "Accord-cadre de 4 ans pour la maintenance et reparation des ouvrages d'art du reseau routier national en Ile-de-France."),
    ("ao_2026_0057.pdf", "AO-2026-0057", "EHPAD 120 lits - Aix-en-Provence", "ARS Provence-Alpes-Cote d'Azur", "Provence-Alpes-Cote d'Azur", "12 000 000 EUR HT", 24, "Construction d'un EHPAD de 120 lits en R+3 avec jardins therapeutiques."),
    ("ao_2026_0058.pdf", "AO-2026-0058", "Piscine olympique intercommunale - Chambery", "Grand Chambery Agglomeration", "Auvergne-Rhone-Alpes", "18 000 000 EUR HT", 26, "Piscine olympique avec bassin 50 m de competition, bassin ludique et espace bien-etre."),
    ("ao_2026_0059.pdf", "AO-2026-0059", "Tramway ligne D - Section Bordeaux Lac", "Bordeaux Metropole", "Nouvelle-Aquitaine", "35 000 000 EUR HT", 30, "Construction de 3,5 km de plateforme tramway avec 4 stations et 2 ouvrages de genie civil."),
    ("ao_2026_0060.pdf", "AO-2026-0060", "Rehabilitation caserne Vauban - Lille", "Ville de Lille", "Hauts-de-France", "7 500 000 EUR HT", 18, "Rehabilitation de la caserne Vauban pour creer un centre culturel et associatif."),
    ("ao_2026_0061.pdf", "AO-2026-0061", "Tour de logements R+25 - Ivry-sur-Seine", "Nexity Immobilier", "Ile-de-France", "28 000 000 EUR HT", 28, "Tour de 180 logements R+25 avec parking souterrain R-3. Structure en beton arme avec noyaux voiles."),
    ("ao_2026_0062.pdf", "AO-2026-0062", "Station d'epuration 80 000 EH - Perpignan", "Perpignan Mediterranee Metropole", "Occitanie", "22 000 000 EUR HT", 30, "Construction d'une station d'epuration de 80 000 EH avec traitement biologique et desodorisation."),
    ("ao_2026_0063.pdf", "AO-2026-0063", "Residence etudiante 250 logements - Rennes", "CROUS de Bretagne", "Bretagne", "14 000 000 EUR HT", 20, "Residence etudiante de 250 logements en studios et T1 en R+6 avec espaces communs et local velos."),
    ("ao_2026_0064.pdf", "AO-2026-0064", "Contournement routier RD83 - Colmar", "Conseil Departemental du Haut-Rhin", "Grand Est", "16 000 000 EUR HT", 24, "Contournement routier de 4,2 km en 2x1 voie avec giratoire et passage inferieur."),
    ("ao_2026_0065.pdf", "AO-2026-0065", "Hotel 5 etoiles 200 chambres - Cannes Croisette", "Groupe Barriere", "Provence-Alpes-Cote d'Azur", "45 000 000 EUR HT", 30, "Construction d'un hotel de luxe 5 etoiles de 200 chambres en R+8 avec spa et restaurant panoramique."),
    ("ao_2026_0066.pdf", "AO-2026-0066", "Parking silo 800 places - Gare Part-Dieu Lyon", "SPL Lyon Part-Dieu", "Auvergne-Rhone-Alpes", "20 000 000 EUR HT", 22, "Parking silo de 800 places en R+6 avec structure en beton precontraint et facade vegetalisee."),
    ("ao_2026_0067.pdf", "AO-2026-0067", "Groupe scolaire 15 classes - Saclay", "EPA Paris-Saclay", "Ile-de-France", "8 000 000 EUR HT", 18, "Groupe scolaire de 15 classes avec restaurant scolaire et gymnase type C."),
    ("ao_2026_0068.pdf", "AO-2026-0068", "Centre aquatique intercommunal - Anglet", "Communaute d'Agglomeration Pays Basque", "Nouvelle-Aquitaine", "15 000 000 EUR HT", 24, "Centre aquatique avec bassin 25 m de competition, bassin ludique et espace bien-etre."),
    ("ao_2026_0069.pdf", "AO-2026-0069", "Accord-cadre renovation energetique lycees - Region HDF", "Region Hauts-de-France", "Hauts-de-France", "30 000 000 EUR HT", 48, "Accord-cadre de 4 ans pour la renovation energetique de 25 lycees."),
    ("ao_2026_0070.pdf", "AO-2026-0070", "Pont hauban sur le Tarn - Millau", "DREAL Occitanie", "Occitanie", "25 000 000 EUR HT", 36, "Pont a haubans avec travee principale de 250 m et pylone de 80 m de hauteur."),
    ("ao_2026_0071.pdf", "AO-2026-0071", "Centre logistique Amazon - Metz Actipole", "Amazon France Logistique", "Grand Est", "35 000 000 EUR HT", 18, "Centre logistique de 45 000 m2 avec mezzanine et quais de chargement."),
]

for _fn, _num, _titre, _mo, _reg, _mt, _delai, _desc in _EXTRA_TENDERS:
    TENDERS.append({
        "filename": _fn, "numero": _num, "titre": _titre,
        "maitre_ouvrage": _mo, "region": _reg, "montant": _mt,
        "delai": f"{_delai} mois a compter de l'ordre de service",
        "date_limite": "30/04/2026 a 12h00",
        "representant": f"Service marches publics, {_mo}",
        "contact": f"marches@{_mo.lower().replace(' ', '-')[:20]}.fr / 01 00 00 00 00",
        "nature": "Marche public de travaux",
        "description": _desc,
        "exigences": ["Qualibat requise", "ISO 14001 souhaitee", "References similaires exigees"],
        "criteres": {"Valeur technique": "50%", "Prix": "40%", "Delai": "10%"},
        "pieces": ["Acte d'engagement", "CCAP", "CCTP", "BPU et DQE", "Plans"],
    })


def generate_tender_pdf(tender_data, output_path):
    """Generate a realistic French DCE tender PDF."""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 1.5*cm

    def write_header():
        nonlocal y
        # Top header
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.5*cm, y, "REPUBLIQUE FRANCAISE")
        y -= 0.5*cm
        c.setFont("Helvetica", 8)
        c.drawString(1.5*cm, y, tender_data["maitre_ouvrage"])
        y -= 1*cm

        # Title block
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, y, "AVIS D'APPEL PUBLIC A LA CONCURRENCE")
        y -= 0.7*cm
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(width / 2, y, f"Marche n {tender_data['numero']}")
        y -= 1*cm

        # Horizontal line
        c.line(1.5*cm, y, width - 1.5*cm, y)
        y -= 0.5*cm

    def write_section(title):
        nonlocal y
        if y < 3*cm:
            c.showPage()
            y = height - 2*cm
        y -= 0.3*cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1.5*cm, y, title)
        c.line(1.5*cm, y - 0.1*cm, width - 1.5*cm, y - 0.1*cm)
        y -= 0.6*cm
        c.setFont("Helvetica", 9)

    def write_field(label, value):
        nonlocal y
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.5*cm, y, f"{label} :")
        c.setFont("Helvetica", 9)
        # If value fits on same line
        label_width = c.stringWidth(f"{label} : ", "Helvetica-Bold", 9)
        remaining = width - 1.5*cm - label_width - 1.5*cm
        if c.stringWidth(str(value), "Helvetica", 9) < remaining:
            c.drawString(1.5*cm + label_width, y, str(value))
            y -= 0.45*cm
        else:
            y -= 0.4*cm
            write_text(str(value))

    def write_text(text):
        nonlocal y
        words = text.split()
        line = ""
        max_w = width - 3*cm
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", 9) < max_w:
                line = test
            else:
                if y < 2*cm:
                    c.showPage()
                    y = height - 2*cm
                c.drawString(1.5*cm, y, line)
                y -= 0.38*cm
                line = word
        if line:
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm
            c.drawString(1.5*cm, y, line)
            y -= 0.38*cm

    def write_bullet(text):
        nonlocal y
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm
        # Wrap bullet text
        words = text.split()
        line = ""
        max_w = width - 4*cm
        first = True
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", 9) < max_w:
                line = test
            else:
                if y < 2*cm:
                    c.showPage()
                    y = height - 2*cm
                prefix = "  - " if first else "    "
                c.drawString(1.5*cm, y, f"{prefix}{line}")
                y -= 0.38*cm
                line = word
                first = False
        if line:
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm
            prefix = "  - " if first else "    "
            c.drawString(1.5*cm, y, f"{prefix}{line}")
            y -= 0.38*cm

    # === Build the PDF ===
    write_header()

    # Title
    c.setFont("Helvetica-Bold", 10)
    write_text(f"Objet : {tender_data['titre']}")
    y -= 0.3*cm

    # Section 1: Identification
    write_section("ARTICLE 1 - IDENTIFICATION DU POUVOIR ADJUDICATEUR")
    write_field("Maitre d'ouvrage", tender_data["maitre_ouvrage"])
    write_field("Representant", tender_data["representant"])
    write_field("Contact", tender_data["contact"])
    write_field("Region", tender_data["region"])

    # Section 2: Objet du marche
    write_section("ARTICLE 2 - OBJET DU MARCHE")
    write_field("Nature du marche", tender_data["nature"])
    write_field("Montant estimatif", tender_data["montant"])
    write_field("Delai d'execution", tender_data["delai"])
    y -= 0.2*cm
    write_text(tender_data["description"])

    # Section 3: Conditions de participation
    write_section("ARTICLE 3 - CONDITIONS DE PARTICIPATION")
    c.setFont("Helvetica", 9)
    write_text("Les candidats devront satisfaire aux exigences suivantes :")
    y -= 0.1*cm
    for exigence in tender_data["exigences"]:
        write_bullet(exigence)

    # Section 4: Criteres d'attribution
    write_section("ARTICLE 4 - CRITERES D'ATTRIBUTION")
    write_text("Les offres seront jugees selon les criteres ponderes suivants :")
    y -= 0.1*cm
    for critere, poids in tender_data["criteres"].items():
        write_bullet(f"{critere} : {poids}")

    # Section 5: Modalites
    write_section("ARTICLE 5 - MODALITES DE REMISE DES OFFRES")
    write_field("Date limite de remise", tender_data["date_limite"])
    write_text(
        "Les offres devront etre transmises par voie electronique via la plateforme "
        "de dematerialisation des marches publics. Les candidats sont invites a "
        "deposer leurs plis dans les delais impartis. Tout pli recu hors delai "
        "sera declare irrecevable."
    )
    y -= 0.2*cm
    write_text(
        "Les variantes sont autorisees sous reserve de presenter une offre de base "
        "conforme au cahier des charges. Les offres seront redigees en langue francaise. "
        "Le delai de validite des offres est fixe a 120 jours."
    )

    # Section 6: Pieces du dossier
    write_section("ARTICLE 6 - COMPOSITION DU DOSSIER DE CONSULTATION (DCE)")
    write_text("Le dossier de consultation comprend les pieces suivantes :")
    y -= 0.1*cm
    for i, piece in enumerate(tender_data["pieces"], 1):
        write_bullet(f"Piece {i} - {piece}")

    # Section 7: Renseignements complementaires
    write_section("ARTICLE 7 - RENSEIGNEMENTS COMPLEMENTAIRES")
    write_text(
        "Pour tout renseignement complementaire, les candidats sont invites a adresser "
        f"leurs questions par ecrit a {tender_data['contact'].split('/')[0].strip()} "
        "au plus tard 10 jours avant la date limite de remise des offres."
    )
    y -= 0.3*cm
    write_text(
        "Les reponses aux questions seront communiquees a l'ensemble des candidats "
        "via la plateforme de dematerialisation."
    )

    # Footer
    y -= 0.8*cm
    if y < 3*cm:
        c.showPage()
        y = height - 2*cm
    c.line(1.5*cm, y, width - 1.5*cm, y)
    y -= 0.5*cm
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, y, f"Marche {tender_data['numero']} - {tender_data['maitre_ouvrage']}")
    y -= 0.4*cm
    c.drawCentredString(width / 2, y, "Document genere dans le cadre de la procedure de mise en concurrence")

    c.save()


def main():
    import shutil

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    output_dir = os.path.join(project_root, "documents", "tenders")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating tender PDFs to: {output_dir}\n")

    en_count = 0
    for tender in TENDERS:
        pdf_path = os.path.join(output_dir, tender["filename"])
        generate_tender_pdf(tender, pdf_path)
        size = os.path.getsize(pdf_path)
        print(f"  {tender['numero']} -> {tender['filename']} ({size:,} bytes)")

        # Generate EN version (copy with _en suffix)
        en_file = tender["filename"].replace(".pdf", "_en.pdf")
        en_path = os.path.join(output_dir, en_file)
        shutil.copy2(pdf_path, en_path)
        en_count += 1

    print(f"\nGenerated {len(TENDERS)} tender PDFs + {en_count} EN versions in {output_dir}")


if __name__ == "__main__":
    main()
