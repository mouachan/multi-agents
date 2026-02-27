"""Pre-defined decisions for the 10 claims and 10 tenders to be processed."""

# 10 claim decisions: 4 approve, 3 deny, 3 manual_review
CLAIM_DECISIONS = [
    {
        "claim_number": "CLM-2024-0001",
        "recommendation": "approve",
        "confidence": 0.92,
        "reasoning": (
            "Sinistre medical valide pour le demandeur Pierre Dupont. "
            "Les factures medicales sont detaillees et conformes aux codes CCAM. "
            "Le contrat CNT-2024-0001 (Assurance Sante) couvre bien les soins declares. "
            "Montant dans les limites du plafond annuel. Franchise de 300 EUR appliquee. "
            "Aucun antecedent de fraude detecte. Recommandation: APPROUVER."
        ),
    },
    {
        "claim_number": "CLM-2024-0002",
        "recommendation": "approve",
        "confidence": 0.88,
        "reasoning": (
            "Collision documentee pour Marie Leroy. Constat amiable signe par les deux parties, "
            "PV de police disponible. Le contrat CNT-2024-0003 (Auto tous risques) couvre "
            "les degats de collision. Expertise vehicule conforme aux photos. "
            "Franchise de 350 EUR deduite. Vehicule de remplacement accorde. "
            "Recommandation: APPROUVER."
        ),
    },
    {
        "claim_number": "CLM-2024-0003",
        "recommendation": "deny",
        "confidence": 0.85,
        "reasoning": (
            "Sinistre auto de Jean Moreau survenu lors d'une course automobile amateur. "
            "Le contrat CNT-2024-0005 comporte une exclusion explicite 'course et competition' "
            "(clause 4.2). Les photos montrent un circuit ferme. "
            "Le conducteur a admis participer a un rallye amateur. "
            "L'exclusion contractuelle s'applique. Recommandation: REFUSER."
        ),
    },
    {
        "claim_number": "CLM-2024-0004",
        "recommendation": "approve",
        "confidence": 0.90,
        "reasoning": (
            "Degats de tempete documentes pour Sophie Bernard. "
            "Arrete de catastrophe naturelle publie au JO pour la commune de Lyon le 15/11/2025. "
            "Le contrat CNT-2024-0007 (Habitation multirisque) couvre les degats de tempete. "
            "Photos des degats (toiture, fenetres) coherentes avec les conditions meteo. "
            "Expertise confirmant 15 000 EUR de dommages. Franchise 500 EUR appliquee. "
            "Recommandation: APPROUVER."
        ),
    },
    {
        "claim_number": "CLM-2024-0005",
        "recommendation": "manual_review",
        "confidence": 0.65,
        "reasoning": (
            "Sinistre medical de Thomas Petit necessitant une revue manuelle. "
            "Circonstances suspectes: declaration tardive (85 jours apres le soin), "
            "montant eleve (47 000 EUR) pour une hospitalisation de 3 jours. "
            "Le contrat CNT-2024-0009 couvre les frais, mais les factures presentent "
            "des incoherences (dates, codes CCAM). "
            "Expertise medicale complementaire necessaire. "
            "Recommandation: REVUE MANUELLE."
        ),
    },
    {
        "claim_number": "CLM-2024-0006",
        "recommendation": "approve",
        "confidence": 0.94,
        "reasoning": (
            "Accident auto d'Isabelle Durand avec tiers identifie. "
            "Constat amiable signe, tiers reconnu responsable a 100%. "
            "Le contrat CNT-2024-0011 (Auto tous risques) couvre les degats. "
            "Expertise vehicule: 8 500 EUR de reparations, conforme aux photos. "
            "Recours subrogatoire contre l'assureur du tiers initie. "
            "Recommandation: APPROUVER."
        ),
    },
    {
        "claim_number": "CLM-2024-0007",
        "recommendation": "deny",
        "confidence": 0.82,
        "reasoning": (
            "Degats des eaux declares par Nicolas Lambert dans sa maison de Toulouse. "
            "L'expertise revele un defaut d'entretien manifeste: joints de douche non remplaces "
            "depuis 8 ans, fuite progressive documentee par le plombier. "
            "Le contrat CNT-2024-0013 exclut explicitement le defaut d'entretien (clause 4.7). "
            "Les degats ne sont pas soudains et accidentels mais progressifs. "
            "Recommandation: REFUSER."
        ),
    },
    {
        "claim_number": "CLM-2024-0008",
        "recommendation": "manual_review",
        "confidence": 0.58,
        "reasoning": (
            "Sinistre medical de Claire Fontaine. Factures incompletes: "
            "manque le detail des actes CCAM pour 3 consultations specialistes. "
            "Le montant total (12 300 EUR) est plausible mais necessite verification. "
            "Le contrat CNT-2024-0015 couvre les soins declares. "
            "Demande de pieces complementaires necessaire avant decision finale. "
            "Expertise medicale recommandee pour valider la coherence des soins. "
            "Recommandation: REVUE MANUELLE."
        ),
    },
    {
        "claim_number": "CLM-2024-0009",
        "recommendation": "deny",
        "confidence": 0.80,
        "reasoning": (
            "Sinistre auto d'Antoine Rousseau. Le rapport de police indique "
            "une alcoolemie de 0.8 g/L au moment de l'accident (seuil legal: 0.5 g/L). "
            "Le contrat CNT-2024-0017 comporte une exclusion contractuelle alcoolemie (art. 8.3). "
            "L'exclusion est opposable: le conducteur etait en infraction. "
            "Recommandation: REFUSER."
        ),
    },
    {
        "claim_number": "CLM-2024-0010",
        "recommendation": "manual_review",
        "confidence": 0.62,
        "reasoning": (
            "Sinistre habitation de Julie Martin a Lille. "
            "Pattern suspect: 3eme sinistre declare en 18 mois sur le meme bien. "
            "Les deux premiers sinistres (degats des eaux, vol) ont ete indemnises. "
            "Le contrat CNT-2024-0019 est actif et couvre les degats declares (incendie partiel). "
            "Cependant, la frequence des sinistres justifie une enquete complementaire. "
            "Contre-expertise recommandee. "
            "Recommandation: REVUE MANUELLE."
        ),
    },
]


# 10 tender decisions: 4 go, 3 no_go, 3 a_approfondir
TENDER_DECISIONS = [
    {
        "tender_number": "AO-2026-0042",
        "recommendation": "go",
        "confidence": 0.87,
        "reasoning": (
            "Recommandation GO pour l'AO Construction 80 logements Nanterre. "
            "References directement comparables: REF-2023-001 (120 logements Villeurbanne, 18.5M EUR), "
            "AO-HIS-2024-001 (65 logements, GAGNE). "
            "Certifications OK: Qualibat 2112, NF Habitat HQE, ISO 14001. "
            "Equipe gros oeuvre IDF disponible. Budget 8M EUR dans notre fourchette. "
            "Taux de reussite historique logements IDF: 45%. "
            "Points de vigilance: label E+C- niveau E3C1 exigeant."
        ),
    },
    {
        "tender_number": "AO-2026-0043",
        "recommendation": "go",
        "confidence": 0.82,
        "reasoning": (
            "Recommandation GO pour la rehabilitation Tour Sequoia La Defense. "
            "Reference solide: REF-2023-004 (rehabilitation Hotel des Postes Marseille), "
            "AO-HIS-2024-005 (rehabilitation CHU Bordeaux, GAGNE). "
            "Experience en site occupe demontree. ISO 14001 valide. "
            "Budget modeste (3.5M EUR), bon ratio risque/marge. "
            "Horaires decales 6h-22h geres par nos equipes IDF. "
            "Attention: lot unique TCE hors CVC, bien dimensionner la sous-traitance."
        ),
    },
    {
        "tender_number": "AO-2026-0044",
        "recommendation": "a_approfondir",
        "confidence": 0.65,
        "reasoning": (
            "A APPROFONDIR pour le gymnase Villeurbanne. "
            "Reference partielle: REF-2023-008 (gymnase olympique Creteil) est comparable "
            "mais en IDF, pas en ARA. Qualibat 2112 OK. "
            "Point bloquant: conception-realisation necessite une equipe architecturale integree. "
            "Verifier la disponibilite de notre bureau d'etudes et identifier un architecte partenaire. "
            "Budget 5M EUR correct. Capacite ARA a valider (grue Potain occupee jusqu'a 06/2026). "
            "Decision finale apres verification des capacites."
        ),
    },
    {
        "tender_number": "AO-2026-0045",
        "recommendation": "go",
        "confidence": 0.90,
        "reasoning": (
            "Recommandation GO pour l'ouvrage d'art A86/A4 Joinville. "
            "Reference forte: REF-2023-002 (pont Garonne, 12.8M EUR), REF-2023-006 (tunnel metro). "
            "AO-HIS-2024-002 (pont-rail SNCF, GAGNE) et AO-HIS-2024-007 (GPE, GAGNE). "
            "MASE valide, Qualibat 2112 OK, expertise genie civil IDF confirmee. "
            "Budget 12M EUR alignee avec nos references. Critere technique dominant (55%). "
            "Travaux de nuit et sous circulation: experience demontree."
        ),
    },
    {
        "tender_number": "AO-2026-0046",
        "recommendation": "no_go",
        "confidence": 0.78,
        "reasoning": (
            "Recommandation NO-GO pour la ZAC Bordeaux Euratlantique. "
            "Reference VRD: REF-2023-005 est a Bordeaux mais l'equipe VRD Nouvelle-Aquitaine "
            "est la seule disponible et insuffisante pour un projet de 7M EUR. "
            "Le critere prix est dominant (45%) et notre implantation locale est limitee. "
            "AO-HIS-2024-008 perdu en PACA pour raison similaire (pas de carriere locale). "
            "Clause d'insertion sociale 10% difficile a satisfaire sans sous-traitants locaux. "
            "Risque commercial trop eleve."
        ),
    },
    {
        "tender_number": "AO-2026-0047",
        "recommendation": "no_go",
        "confidence": 0.85,
        "reasoning": (
            "Recommandation NO-GO pour le quai de croisiere Toulon. "
            "AUCUNE reference en travaux maritimes. AO-HIS-2024-010 (quai Fos) perdu "
            "pour absence de references portuaires. "
            "Exigences bloquantes: plongeurs classe II-B, Natura 2000, batardeau marin. "
            "Equipements specialises non disponibles (barge, grue maritime). "
            "Budget 25M EUR avec un critere technique a 60%: impossible de concurrencer "
            "les specialistes maritimes (Bouygues TP, Eiffage Maritime)."
        ),
    },
    {
        "tender_number": "AO-2026-0048",
        "recommendation": "no_go",
        "confidence": 0.80,
        "reasoning": (
            "Recommandation NO-GO pour l'ecole Saint-Pierre de La Reunion. "
            "Pas de presence locale a La Reunion. "
            "AO-HIS-2024-013 (Saint-Denis 974) abandonne pour la meme raison. "
            "Couts de mobilisation prohibitifs (materiel + personnel). "
            "Critere prix dominant (55%) rend l'offre non competitive "
            "face aux entreprises implantees localement. "
            "Budget serre (3.2M EUR) ne permet pas d'absorber les surcouts logistiques."
        ),
    },
    {
        "tender_number": "AO-2026-0049",
        "recommendation": "a_approfondir",
        "confidence": 0.60,
        "reasoning": (
            "A APPROFONDIR pour le confortement nucleaire CNPE Blayais. "
            "Marche strategique: nucleaire = diversification et marges elevees. "
            "Pas de reference nucleaire directe, mais expertise genie civil lourd "
            "(REF-2023-006 tunnel, REF-2023-010 Sanofi site Seveso). "
            "MASE valide. Points bloquants: habilitation PR1-CC et RCC-G a obtenir. "
            "Critere technique tres dominant (65%). "
            "Explorer partenariat avec un acteur nucleaire pour un premier marche. "
            "Decision apres etude de faisabilite habilitations."
        ),
    },
    {
        "tender_number": "AO-2026-0050",
        "recommendation": "go",
        "confidence": 0.88,
        "reasoning": (
            "Recommandation GO pour les 95 logements Lyon ZAC Girondins. "
            "Reference directe: REF-2023-001 (120 logements Villeurbanne), meme region ARA. "
            "AO-HIS-2024-001 (65 logements IDF, GAGNE), AO-HIS-2024-006 (lycee ARA, GAGNE). "
            "Qualibat 2112 et NF Habitat HQE: valides. ISO 14001 souhaitee: valide. "
            "Budget 11.5M EUR dans notre coeur de metier. "
            "Verifier disponibilite grue Potain ARA (occupee chantier Annecy). "
            "Forte probabilite de succes: profil ideal pour notre equipe ARA."
        ),
    },
    {
        "tender_number": "AO-2026-0051",
        "recommendation": "a_approfondir",
        "confidence": 0.55,
        "reasoning": (
            "A APPROFONDIR pour le data center Equinix Lisses. "
            "Marche strategique: data centers en forte croissance, montant eleve (42M EUR). "
            "Pas de reference data center directe, mais REF-2023-007 (plateforme logistique) "
            "et REF-2023-010 (extension pharmaceutique Sanofi) sont partiellement comparables. "
            "Qualibat 2112 et ISO OK. "
            "Point de vigilance: critere prix dominant (50%) et planning agressif (20 mois). "
            "Opportunite strategique de se positionner sur un segment porteur. "
            "Etudier un partenariat ou un recrutement d'expertise data center."
        ),
    },
]
