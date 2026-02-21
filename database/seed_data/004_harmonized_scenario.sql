-- ============================================================================
-- Seed Data 004: Harmonized AO -> Claim Scenario
--
-- Coherent scenario:
-- 1. Company as user with construction insurance contract
-- 2. AO-2025-IDF-003: "Construction complexe sportif municipal Cergy-Pontoise"
-- 3. Agent AO analyses -> Decision Go (good references, certs OK)
-- 4. 6 months later: incident on site (collapsed slab)
-- 5. CLM-ENT-001: Insurance claim for site damages
-- 6. Agent Claims analyses -> Manual Review (high amount, complex liability)
-- 7. Linked via metadata.project_reference = "PROJ-2025-CERGY-001"
-- 8. PII _redacted fields pre-populated
-- ============================================================================

-- User: Entreprise Construction IDF
INSERT INTO users (
    id, user_id, email, full_name, date_of_birth, phone_number, address,
    email_redacted, full_name_redacted, phone_number_redacted, date_of_birth_redacted, address_redacted,
    is_active, metadata
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'ENT-IDF-001',
    'jean.martin@company-btp.fr',
    'Jean Martin',
    '1975-03-22',
    '06 12 34 56 78',
    '{"street": "1 cours Ferdinand de Lesseps", "city": "Rueil-Malmaison", "zip": "92500", "country": "France"}',
    'j***@***.fr',
    'J*** M***',
    '** ** ** ** **',
    '****-**-**',
    '{"street": "1 ***", "city": "Rueil-Malmaison", "zip": "*****", "country": "France"}',
    true,
    '{"company": "Entreprise Construction IDF", "role": "Directeur de Projets", "certifications": ["ISO 9001", "ISO 14001", "MASE"]}'
) ON CONFLICT (user_id) DO NOTHING;

-- User contract: Construction All-Risk Insurance
INSERT INTO user_contracts (
    id, user_id, contract_number, contract_type,
    start_date, end_date, coverage_amount, premium_amount, payment_frequency,
    full_text, key_terms, coverage_details, exclusions,
    is_active, metadata
) VALUES (
    'b2c3d4e5-f6a7-8901-bcde-f12345678901',
    'ENT-IDF-001',
    'CTR-ENT-RC-2024',
    'construction_all_risk',
    '2024-01-01',
    '2026-12-31',
    5000000.00,
    125000.00,
    'annual',
    'Police Tous Risques Chantier (TRC) couvrant l''ensemble des travaux de construction entrepris par Entreprise Construction IDF. Couverture: dommages materiels, effondrement, incendie, vol, vandalisme. Franchise: 50 000 EUR par sinistre. Plafond: 5 000 000 EUR par projet.',
    '{"type": "TRC", "franchise": 50000, "plafond": 5000000, "couverture_decennale": true}',
    '{"dommages_materiels": true, "effondrement": true, "incendie": true, "vol": true, "responsabilite_civile": true, "decennale": true}',
    '{"guerre": true, "nucleaire": true, "faute_intentionnelle": true, "defaut_entretien_apres_reception": true}',
    true,
    '{"assureur": "Assureur Partenaire", "courtier": "Marsh", "project_reference": "PROJ-2025-CERGY-001"}'
) ON CONFLICT (contract_number) DO NOTHING;


-- ============================================================================
-- PART 1: TENDER (Appel d'Offres) - AO-2025-IDF-003
-- Decision: GO (bonnes references, certifications OK)
-- ============================================================================

INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path,
    status, submitted_at, processed_at, total_processing_time_ms,
    is_archived, metadata, agent_logs
) VALUES (
    'c3d4e5f6-a7b8-9012-cdef-123456789012',
    'ENT-IDF',
    'AO-2025-IDF-003',
    'marche_public',
    'tenders/ao-2025-idf-003-dce.pdf',
    'completed',
    '2025-01-15 09:00:00+00',
    '2025-01-15 09:05:30+00',
    330000,
    false,
    '{"project_reference": "PROJ-2025-CERGY-001", "maitre_ouvrage": "Ville de Cergy-Pontoise", "objet": "Construction complexe sportif municipal", "montant_estime": 4200000, "delai_execution_mois": 18, "date_remise": "2025-02-28", "region": "Ile-de-France"}',
    '[]'
) ON CONFLICT (tender_number) DO NOTHING;

-- Tender document with OCR
INSERT INTO tender_documents (
    id, tender_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    'd4e5f6a7-b8c9-0123-defa-234567890123',
    'c3d4e5f6-a7b8-9012-cdef-123456789012',
    'dce',
    'tenders/ao-2025-idf-003-dce.pdf',
    2450000,
    'application/pdf',
    'MARCHE PUBLIC - VILLE DE CERGY-PONTOISE
Objet: Construction d''un complexe sportif municipal
Lot unique - Tous corps d''etat
Maitre d''ouvrage: Ville de Cergy-Pontoise, representee par M. Pierre Dubois, Maire
Contact: p.dubois@cergy-pontoise.fr / 01 34 25 00 00

Montant estimatif: 4 200 000 EUR HT
Delai d''execution: 18 mois a compter de l''ordre de service
Date limite de remise des offres: 28/02/2025 a 12h00

Criteres d''attribution:
- Valeur technique: 60%
- Prix: 30%
- Delai: 10%

Exigences techniques:
- Certification Qualibat 2111 (Gros oeuvre)
- Certification NF EN ISO 14001
- References similaires (3 minimum sur 5 ans)
- Chiffre d''affaires minimum: 10M EUR/an',
    'MARCHE PUBLIC - VILLE DE CERGY-PONTOISE
Objet: Construction d''un complexe sportif municipal
Lot unique - Tous corps d''etat
Maitre d''ouvrage: Ville de Cergy-Pontoise, representee par M. P*** D***, Maire
Contact: p***@***.fr / ** ** ** ** **

Montant estimatif: 4 200 000 EUR HT
Delai d''execution: 18 mois a compter de l''ordre de service
Date limite de remise des offres: **/**/****  a 12h00

Criteres d''attribution:
- Valeur technique: 60%
- Prix: 30%
- Delai: 10%

Exigences techniques:
- Certification Qualibat 2111 (Gros oeuvre)
- Certification NF EN ISO 14001
- References similaires (3 minimum sur 5 ans)
- Chiffre d''affaires minimum: 10M EUR/an',
    '{"maitre_ouvrage": "Ville de Cergy-Pontoise", "objet": "Construction complexe sportif municipal", "montant_ht": 4200000, "delai_mois": 18, "criteres": {"technique": 60, "prix": 30, "delai": 10}}',
    0.92,
    '2025-01-15 09:01:00+00',
    24,
    'fra'
) ON CONFLICT DO NOTHING;

-- Tender decision: GO
INSERT INTO tender_decisions (
    id, tender_id,
    initial_decision, initial_confidence, initial_reasoning, initial_decided_at,
    decision, confidence, reasoning,
    risk_analysis, similar_references, historical_ao_analysis, internal_capabilities,
    llm_model, requires_manual_review
) VALUES (
    'e5f6a7b8-c9d0-1234-efab-345678901234',
    'c3d4e5f6-a7b8-9012-cdef-123456789012',
    'go', 0.85,
    'Recommandation GO pour l''AO Construction complexe sportif Cergy-Pontoise. Entreprise Construction IDF dispose de references solides en equipements sportifs (3 projets similaires sur 5 ans), toutes les certifications requises (Qualibat 2111, ISO 14001), et les capacites internes sont disponibles. Le montant de 4.2M EUR est dans notre fourchette habituelle. Le taux de reussite historique sur ce type de marche public en IDF est de 42%. Points de vigilance: delai serre de 18 mois et forte concurrence attendue (Bouygues, Eiffage).',
    '2025-01-15 09:05:30+00',
    'go', 0.85,
    'Recommandation GO pour l''AO Construction complexe sportif Cergy-Pontoise.',
    '{"technical": "Faible - Certifications OK, experience confirmee", "financial": "Moyen - Marge estimee 8-12%, franchise TRC a considerer", "resource": "Faible - Equipes disponibles Q2 2025", "competition": "Moyen - 3-4 concurrents attendus"}',
    '[{"project": "Gymnase municipal Pontoise", "montant": 3800000, "annee": 2023, "resultat": "Termine avec succes"}, {"project": "Centre aquatique Osny", "montant": 5200000, "annee": 2022, "resultat": "Termine, reception sans reserve"}]',
    '{"taux_reussite": 0.42, "nombre_ao_similaires": 7, "montant_moyen": 4100000}',
    '{"certifications": ["Qualibat 2111", "ISO 14001", "ISO 9001", "MASE"], "materiel_disponible": true, "equipes_disponibles": true, "sous_traitants_identifies": true}',
    'vllm-inference-1/llama-instruct-32-3b',
    false
) ON CONFLICT DO NOTHING;


-- ============================================================================
-- PART 2: CLAIM - CLM-ENT-001 (6 months after AO Go)
-- Incident: Collapsed slab during construction
-- Decision: MANUAL_REVIEW (high amount, complex liability)
-- ============================================================================

INSERT INTO claims (
    id, user_id, claim_number, claim_type, document_path,
    status, submitted_at, processed_at, total_processing_time_ms,
    is_archived, metadata, agent_logs
) VALUES (
    'f6a7b8c9-d0e1-2345-fabc-456789012345',
    'ENT-IDF-001',
    'CLM-ENT-001',
    'construction_damage',
    'claims/clm-ent-001-sinistre.pdf',
    'manual_review',
    '2025-07-22 14:30:00+00',
    '2025-07-22 14:35:45+00',
    345000,
    false,
    '{"project_reference": "PROJ-2025-CERGY-001", "tender_number": "AO-2025-IDF-003", "incident_date": "2025-07-20", "incident_type": "effondrement_dalle", "lieu": "Chantier complexe sportif Cergy-Pontoise", "montant_estime_dommages": 850000, "blessures": false, "arret_chantier": true}',
    '[]'
) ON CONFLICT (claim_number) DO NOTHING;

-- Claim document with OCR
INSERT INTO claim_documents (
    id, claim_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    'a7b8c9d0-e1f2-3456-abcd-567890123456',
    'f6a7b8c9-d0e1-2345-fabc-456789012345',
    'sinistre_declaration',
    'claims/clm-ent-001-sinistre.pdf',
    1850000,
    'application/pdf',
    'DECLARATION DE SINISTRE - Entreprise Construction IDF

Assure: Entreprise Construction IDF
Contrat: CTR-ENT-RC-2024 (Tous Risques Chantier)
Declarant: Jean Martin, Directeur de Projets
Contact: jean.martin@company-btp.fr / 06 12 34 56 78

Date du sinistre: 20/07/2025
Lieu: Chantier complexe sportif municipal, Cergy-Pontoise (95)
N reference projet: PROJ-2025-CERGY-001

DESCRIPTION DES FAITS:
Le 20 juillet 2025 a 14h30, lors des travaux de coffrage du premier etage du batiment principal, une dalle de plancher de 120m2 s''est effondree partiellement. L''effondrement est survenu dans la zone B du batiment, affectant la structure porteuse sur environ 200m2.

Aucun blesse n''a ete a deplorer grace a l''evacuation preventive ordonnee par le chef de chantier M. Philippe Leroy (06 98 76 54 32) qui avait detecte des fissures suspectes 30 minutes avant l''incident.

DOMMAGES CONSTATES:
- Dalle de plancher R+1 zone B: destruction totale (120m2)
- Etaiements et coffrages: destruction
- Ferraillage: deformation, a remplacer
- Structure porteuse: fissuration, expertise necessaire
- Materiel de chantier enseveli: grue a tour endommagee

ESTIMATION PROVISOIRE DES DOMMAGES: 850 000 EUR
- Reconstruction dalle et structure: 520 000 EUR
- Reparation/remplacement materiel: 180 000 EUR
- Retard chantier (penalites): 150 000 EUR

MESURES PRISES:
- Arret immediat du chantier zone B
- Mise en securite du perimetre
- Expert BET missionne (Bureau Veritas)
- Declaration CRAM effectuee',
    'DECLARATION DE SINISTRE - Entreprise Construction IDF

Assure: Entreprise Construction IDF
Contrat: CTR-ENT-RC-2024 (Tous Risques Chantier)
Declarant: J*** M***, Directeur de Projets
Contact: j***@***.fr / ** ** ** ** **

Date du sinistre: **/**/****
Lieu: Chantier complexe sportif municipal, Cergy-Pontoise (95)
N reference projet: PROJ-2025-CERGY-001

DESCRIPTION DES FAITS:
Le ** juillet **** a 14h30, lors des travaux de coffrage du premier etage du batiment principal, une dalle de plancher de 120m2 s''est effondree partiellement. L''effondrement est survenu dans la zone B du batiment, affectant la structure porteuse sur environ 200m2.

Aucun blesse n''a ete a deplorer grace a l''evacuation preventive ordonnee par le chef de chantier M. P*** L*** (** ** ** ** **) qui avait detecte des fissures suspectes 30 minutes avant l''incident.

DOMMAGES CONSTATES:
- Dalle de plancher R+1 zone B: destruction totale (120m2)
- Etaiements et coffrages: destruction
- Ferraillage: deformation, a remplacer
- Structure porteuse: fissuration, expertise necessaire
- Materiel de chantier enseveli: grue a tour endommagee

ESTIMATION PROVISOIRE DES DOMMAGES: 850 000 EUR
- Reconstruction dalle et structure: 520 000 EUR
- Reparation/remplacement materiel: 180 000 EUR
- Retard chantier (penalites): 150 000 EUR

MESURES PRISES:
- Arret immediat du chantier zone B
- Mise en securite du perimetre
- Expert BET missionne (Bureau Veritas)
- Declaration CRAM effectuee',
    '{"assure": "Entreprise Construction IDF", "contrat": "CTR-ENT-RC-2024", "date_sinistre": "2025-07-20", "lieu": "Cergy-Pontoise", "type_sinistre": "effondrement_dalle", "montant_estime": 850000}',
    0.94,
    '2025-07-22 14:31:30+00',
    8,
    'fra'
) ON CONFLICT DO NOTHING;

-- Claim decision: MANUAL_REVIEW
INSERT INTO claim_decisions (
    id, claim_id,
    initial_decision, initial_confidence, initial_reasoning, initial_decided_at,
    decision, confidence, reasoning, reasoning_redacted,
    relevant_policies, llm_model, requires_manual_review
) VALUES (
    'b8c9d0e1-f2a3-4567-bcde-678901234567',
    'f6a7b8c9-d0e1-2345-fabc-456789012345',
    'manual_review', 0.72,
    'Recommandation MANUAL_REVIEW pour le sinistre CLM-ENT-001 (effondrement dalle, chantier Cergy-Pontoise). Le montant estime de 850 000 EUR est eleve et depasse le seuil de validation automatique. Le contrat CTR-ENT-RC-2024 couvre bien les dommages materiels et effondrements (couverture TRC). Cependant, la responsabilite est complexe: il faut determiner si l''effondrement est du a un defaut de conception (responsabilite BET), un defaut d''execution (responsabilite entreprise), ou un vice de materiaux (responsabilite fournisseur). L''expertise Bureau Veritas est en cours. Points favorables: mesures de securite appropriees, aucun blesse, declaration dans les delais. Le chef de chantier Jean Martin a reagi rapidement. Contact: jean.martin@company-btp.fr.',
    '2025-07-22 14:35:45+00',
    'manual_review', 0.72,
    'Recommandation MANUAL_REVIEW pour le sinistre CLM-ENT-001.',
    'Recommandation MANUAL_REVIEW pour le sinistre CLM-ENT-001 (effondrement dalle, chantier Cergy-Pontoise). Le montant estime de 850 000 EUR est eleve et depasse le seuil de validation automatique. Le contrat CTR-ENT-RC-2024 couvre bien les dommages materiels et effondrements (couverture TRC). Cependant, la responsabilite est complexe: il faut determiner si l''effondrement est du a un defaut de conception (responsabilite BET), un defaut d''execution (responsabilite entreprise), ou un vice de materiaux (responsabilite fournisseur). L''expertise Bureau Veritas est en cours. Points favorables: mesures de securite appropriees, aucun blesse, declaration dans les delais. Le chef de chantier J*** M*** a reagi rapidement. Contact: j***@***.fr.',
    '{"contrat": "CTR-ENT-RC-2024", "couverture": "TRC - Tous Risques Chantier", "franchise": 50000, "plafond": 5000000, "couvert": true}',
    'vllm-inference-1/llama-instruct-32-3b',
    true
) ON CONFLICT DO NOTHING;

-- PII guardrails detections for the claim
INSERT INTO guardrails_detections (id, claim_id, detection_type, severity, action_taken, detected_at, metadata) VALUES
    (uuid_generate_v4(), 'f6a7b8c9-d0e1-2345-fabc-456789012345', 'EMAIL', 'medium', 'redacted', '2025-07-22 14:32:00+00',
     '{"field_name": "ocr_text", "source": "regex", "entity_type": "claim", "entity_id": "f6a7b8c9-d0e1-2345-fabc-456789012345"}'),
    (uuid_generate_v4(), 'f6a7b8c9-d0e1-2345-fabc-456789012345', 'PHONE_FR', 'medium', 'redacted', '2025-07-22 14:32:00+00',
     '{"field_name": "ocr_text", "source": "regex", "entity_type": "claim", "entity_id": "f6a7b8c9-d0e1-2345-fabc-456789012345"}'),
    (uuid_generate_v4(), 'f6a7b8c9-d0e1-2345-fabc-456789012345', 'DATE_FR', 'low', 'redacted', '2025-07-22 14:32:00+00',
     '{"field_name": "ocr_text", "source": "regex", "entity_type": "claim", "entity_id": "f6a7b8c9-d0e1-2345-fabc-456789012345"}');
