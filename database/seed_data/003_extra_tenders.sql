-- Extra tenders with varied profiles for demo
-- NO_GO: travaux maritimes (pas de references)
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES (
    gen_random_uuid(),
    'VINCI-PACA',
    'AO-2026-0047',
    'Marche public',
    '/claim_documents/ao/ao_2026_0047.pdf',
    'pending',
    '{"titre": "Construction du quai de croisiere du Port de Toulon", "maitre_ouvrage": "Port Autonome de Toulon", "maitre_oeuvre": "Egis Ports", "nature_travaux": "Genie civil maritime - Ouvrage portuaire", "montant_estime": 25000000, "delai_execution_mois": 30, "date_limite_remise": "2026-04-15", "criteres_attribution": {"prix": 30, "technique": 60, "delai": 10}, "lots": ["Lot unique - Genie civil maritime"], "region": "Provence-Alpes-Cote d Azur", "commune": "Toulon", "description": "Construction d un nouveau quai de croisiere en eau profonde (tirant d eau -12 m) de 400 ml avec terre-plein sur pieux fores en milieu marin. Dragage de 150 000 m3, batardeau en palplanches, beton en milieu subaquatique. Expertise maritime et sous-marine requise.", "exigences_specifiques": ["Experience travaux maritimes exigee (3 ref min)", "Plongeurs certifies classe II-B", "Autorisation Natura 2000", "MASE obligatoire", "Certification maritime ISO 45001"], "source": "plateforme PLACE marches publics"}'::jsonb,
    NOW()
);

-- NO_GO: La Reunion (pas de moyens locaux) + critere prix dominant
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES (
    gen_random_uuid(),
    'VINCI-DROM',
    'AO-2026-0048',
    'Marche public',
    '/claim_documents/ao/ao_2026_0048.pdf',
    'pending',
    '{"titre": "Construction ecole primaire Paul Eluard - Saint-Pierre de la Reunion", "maitre_ouvrage": "Commune de Saint-Pierre (974)", "maitre_oeuvre": "Cabinet Bourbon Architectes", "nature_travaux": "Gros oeuvre - Construction neuve equipement scolaire", "montant_estime": 3200000, "delai_execution_mois": 14, "date_limite_remise": "2026-03-20", "criteres_attribution": {"prix": 55, "technique": 35, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre", "Lot 2 - Charpente metallique"], "region": "La Reunion", "commune": "Saint-Pierre", "description": "Construction d une ecole primaire de 12 classes avec cantine et preau dans le quartier Terre Sainte. Structure paracyclonique et parasismique en beton arme R+1. Budget serre, critere prix dominant.", "exigences_specifiques": ["Normes paracycloniques NV65", "Normes parasismiques PS92 zone 5", "Implantation locale obligatoire", "Critere prix dominant 55%"], "source": "plateforme BOAMP DOM-TOM"}'::jsonb,
    NOW()
);

-- A_APPROFONDIR: nucleaire (strategique mais pas de ref directe)
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES (
    gen_random_uuid(),
    'VINCI-NAQ',
    'AO-2026-0049',
    'Marche public',
    '/claim_documents/ao/ao_2026_0049.pdf',
    'pending',
    '{"titre": "Confortement radier et enceinte de confinement - CNPE du Blayais", "maitre_ouvrage": "EDF - Division Production Nucleaire", "maitre_oeuvre": "Assystem Nuclear", "nature_travaux": "Genie civil nucleaire - Confortement structures", "montant_estime": 18000000, "delai_execution_mois": 36, "date_limite_remise": "2026-05-30", "criteres_attribution": {"prix": 25, "technique": 65, "delai": 10}, "lots": ["Lot unique - Genie civil confortement"], "region": "Nouvelle-Aquitaine", "commune": "Braud-et-Saint-Louis", "description": "Confortement du radier et de l enceinte de confinement du reacteur n2 du CNPE du Blayais dans le cadre du Grand Carenage. Travaux en zone controlee avec intervention en periode d arret de tranche. Exigences nucleaires strictes.", "exigences_specifiques": ["Habilitation nucleaire PR1-CC", "Formation RP1-RN", "Qualite nucleaire RCC-G", "MASE exige", "3 references nucleaires exigees"], "source": "consultation EDF"}'::jsonb,
    NOW()
);

-- GO: logements similaires a REF-2023-001
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES (
    gen_random_uuid(),
    'VINCI-ARA',
    'AO-2026-0050',
    'Marche public',
    '/claim_documents/ao/ao_2026_0050.pdf',
    'pending',
    '{"titre": "Construction de 95 logements collectifs - ZAC des Girondins Lyon 7eme", "maitre_ouvrage": "Lyon Metropole Habitat", "maitre_oeuvre": "Agence Tectoniques Architectes", "nature_travaux": "Gros oeuvre - Construction neuve logements collectifs", "montant_estime": 11500000, "delai_execution_mois": 22, "date_limite_remise": "2026-04-20", "criteres_attribution": {"prix": 40, "technique": 50, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre et VRD", "Lot 2 - Enveloppe"], "region": "Auvergne-Rhone-Alpes", "commune": "Lyon", "description": "Construction de 95 logements collectifs en 2 batiments R+7 et R+5 avec commerces en RDC et parking souterrain R-2. Structure beton arme classique, facades a isolation par l exterieur avec bardage bois. Certification NF Habitat HQE visee.", "exigences_specifiques": ["NF Habitat HQE", "Qualibat 2112 exigee", "ISO 14001 souhaitee", "Beton bas carbone privilegie"], "source": "plateforme PLACE marches publics"}'::jsonb,
    NOW()
);

-- A_APPROFONDIR: data center (strategique, gros montant, mais pas de ref directe + prix dominant)
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES (
    gen_random_uuid(),
    'VINCI-IDF',
    'AO-2026-0051',
    'Marche prive',
    '/claim_documents/ao/ao_2026_0051.pdf',
    'pending',
    '{"titre": "Construction data center hyperscale - Campus digital de Lisses", "maitre_ouvrage": "Equinix France", "maitre_oeuvre": "ADP Ingenierie", "nature_travaux": "Batiment industriel - Data center haute densite", "montant_estime": 42000000, "delai_execution_mois": 20, "date_limite_remise": "2026-05-15", "criteres_attribution": {"prix": 50, "technique": 40, "delai": 10}, "lots": ["Lot unique - Gros oeuvre et enveloppe"], "region": "Ile-de-France", "commune": "Lisses", "description": "Construction d un data center hyperscale de 8 000 m2 IT avec puissance electrique de 32 MW. Structure beton arme surdimensionnee pour charges serveurs (15 kN/m2). Marche strategique pour se positionner sur le segment data centers en forte croissance.", "exigences_specifiques": ["Experience data center souhaitee (non obligatoire)", "Qualibat 2112", "ISO 9001 et 14001", "Critere prix dominant 50%", "Planning agressif 20 mois"], "source": "consultation directe Equinix"}'::jsonb,
    NOW()
);
