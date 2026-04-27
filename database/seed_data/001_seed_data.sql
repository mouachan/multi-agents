-- ============================================================================
-- Unified Seed Data for Multi-Agents Platform
-- Contains: Claims domain (users, contracts, claims, knowledge base)
--           Tenders domain (references, capabilities, historical, tenders)
--           Courrier & Colis domain (reclamations, tracking, knowledge base)
--           Cross-domain harmonized scenario (AO -> Claim)
-- ============================================================================

-- Clean ALL data (order matters for foreign keys)
DELETE FROM guardrails_detections;
DELETE FROM processing_logs;
DELETE FROM claim_decisions;
DELETE FROM claim_documents;
DELETE FROM claims;
DELETE FROM tender_processing_logs;
DELETE FROM tender_decisions;
DELETE FROM tender_documents;
DELETE FROM tenders;
DELETE FROM knowledge_base;
DELETE FROM user_contracts;
DELETE FROM users;
DELETE FROM company_references;
DELETE FROM company_capabilities;
DELETE FROM historical_tenders;
DELETE FROM reclamation_processing_logs;
DELETE FROM reclamation_decisions;
DELETE FROM reclamation_documents;
DELETE FROM reclamations;
DELETE FROM tracking_events;
DELETE FROM courrier_knowledge_base;


-- ============================================================================
-- 30 USERS (French names for insurance domain)
-- ============================================================================
INSERT INTO users (user_id, email, full_name, date_of_birth, phone_number, address, is_active) VALUES
('USR001', 'pierre.dupont@email.fr', 'Pierre Dupont', '1982-03-15', '06 12 34 56 01', '{"street": "12 rue de la Paix", "city": "Paris", "zip": "75002", "country": "France"}'::jsonb, true),
('USR002', 'marie.leroy@email.fr', 'Marie Leroy', '1990-07-22', '06 12 34 56 02', '{"street": "45 avenue Victor Hugo", "city": "Lyon", "zip": "69006", "country": "France"}'::jsonb, true),
('USR003', 'jean.moreau@email.fr', 'Jean Moreau', '1975-11-08', '06 12 34 56 03', '{"street": "8 boulevard Haussmann", "city": "Paris", "zip": "75009", "country": "France"}'::jsonb, true),
('USR004', 'sophie.bernard@email.fr', 'Sophie Bernard', '1988-01-30', '06 12 34 56 04', '{"street": "23 rue Garibaldi", "city": "Lyon", "zip": "69003", "country": "France"}'::jsonb, true),
('USR005', 'thomas.petit@email.fr', 'Thomas Petit', '1995-06-14', '06 12 34 56 05', '{"street": "156 route de Vannes", "city": "Nantes", "zip": "44000", "country": "France"}'::jsonb, true),
('USR006', 'isabelle.durand@email.fr', 'Isabelle Durand', '1978-09-03', '06 12 34 56 06', '{"street": "3 place Bellecour", "city": "Lyon", "zip": "69002", "country": "France"}'::jsonb, true),
('USR007', 'nicolas.lambert@email.fr', 'Nicolas Lambert', '1985-12-25', '06 12 34 56 07', '{"street": "67 avenue Jean Jaures", "city": "Toulouse", "zip": "31000", "country": "France"}'::jsonb, true),
('USR008', 'claire.fontaine@email.fr', 'Claire Fontaine', '1992-04-18', '06 12 34 56 08', '{"street": "14 rue de Seze", "city": "Lyon", "zip": "69006", "country": "France"}'::jsonb, true),
('USR009', 'antoine.rousseau@email.fr', 'Antoine Rousseau', '1970-08-07', '06 12 34 56 09', '{"street": "29 quai de la Tournelle", "city": "Paris", "zip": "75005", "country": "France"}'::jsonb, true),
('USR010', 'julie.martin@email.fr', 'Julie Martin', '1987-02-11', '06 12 34 56 10', '{"street": "88 rue Nationale", "city": "Lille", "zip": "59000", "country": "France"}'::jsonb, true),
('USR011', 'philippe.garcia@email.fr', 'Philippe Garcia', '1968-05-20', '06 12 34 56 11', '{"street": "5 rue du Faubourg", "city": "Marseille", "zip": "13001", "country": "France"}'::jsonb, true),
('USR012', 'nathalie.thomas@email.fr', 'Nathalie Thomas', '1983-10-09', '06 12 34 56 12', '{"street": "41 avenue de la Republique", "city": "Bordeaux", "zip": "33000", "country": "France"}'::jsonb, true),
('USR013', 'francois.robert@email.fr', 'Francois Robert', '1991-01-14', '06 12 34 56 13', '{"street": "17 rue des Lices", "city": "Rennes", "zip": "35000", "country": "France"}'::jsonb, true),
('USR014', 'catherine.richard@email.fr', 'Catherine Richard', '1976-07-28', '06 12 34 56 14', '{"street": "62 cours Mirabeau", "city": "Aix-en-Provence", "zip": "13100", "country": "France"}'::jsonb, true),
('USR015', 'david.simon@email.fr', 'David Simon', '1989-03-05', '06 12 34 56 15', '{"street": "9 place du Capitole", "city": "Toulouse", "zip": "31000", "country": "France"}'::jsonb, true),
('USR016', 'valerie.michel@email.fr', 'Valerie Michel', '1980-11-17', '06 12 34 56 16', '{"street": "33 rue de la Liberte", "city": "Nice", "zip": "06000", "country": "France"}'::jsonb, true),
('USR017', 'arnaud.lefebvre@email.fr', 'Arnaud Lefebvre', '1993-08-21', '06 12 34 56 17', '{"street": "71 avenue Foch", "city": "Strasbourg", "zip": "67000", "country": "France"}'::jsonb, true),
('USR018', 'christine.dubois@email.fr', 'Christine Dubois', '1973-04-12', '06 12 34 56 18', '{"street": "25 rue de Vesle", "city": "Reims", "zip": "51100", "country": "France"}'::jsonb, true),
('USR019', 'sebastien.roux@email.fr', 'Sebastien Roux', '1986-06-30', '06 12 34 56 19', '{"street": "48 boulevard Gambetta", "city": "Montpellier", "zip": "34000", "country": "France"}'::jsonb, true),
('USR020', 'emilie.girard@email.fr', 'Emilie Girard', '1994-12-03', '06 12 34 56 20', '{"street": "16 rue Saint-Jean", "city": "Lyon", "zip": "69005", "country": "France"}'::jsonb, true),
('USR021', 'laurent.martinez@email.fr', 'Laurent Martinez', '1971-09-16', '06 12 34 56 21', '{"street": "54 avenue de Toulouse", "city": "Bordeaux", "zip": "33000", "country": "France"}'::jsonb, true),
('USR022', 'sandrine.lopez@email.fr', 'Sandrine Lopez', '1984-02-08', '06 12 34 56 22', '{"street": "7 rue du Port", "city": "Nantes", "zip": "44000", "country": "France"}'::jsonb, true),
('USR023', 'christophe.muller@email.fr', 'Christophe Muller', '1979-05-25', '06 12 34 56 23', '{"street": "39 place Kleber", "city": "Strasbourg", "zip": "67000", "country": "France"}'::jsonb, true),
('USR024', 'helene.fournier@email.fr', 'Helene Fournier', '1996-10-19', '06 12 34 56 24', '{"street": "82 rue de Paris", "city": "Lille", "zip": "59000", "country": "France"}'::jsonb, true),
('USR025', 'benoit.giraud@email.fr', 'Benoit Giraud', '1981-07-04', '06 12 34 56 25', '{"street": "11 rue Emile Zola", "city": "Grenoble", "zip": "38000", "country": "France"}'::jsonb, true),
('USR026', 'cecile.andre@email.fr', 'Cecile Andre', '1990-03-28', '06 12 34 56 26', '{"street": "60 avenue Jean Perrot", "city": "Grenoble", "zip": "38000", "country": "France"}'::jsonb, true),
('USR027', 'guillaume.mercier@email.fr', 'Guillaume Mercier', '1974-08-15', '06 12 34 56 27', '{"street": "22 cours Lafayette", "city": "Lyon", "zip": "69003", "country": "France"}'::jsonb, true),
('USR028', 'delphine.blanc@email.fr', 'Delphine Blanc', '1997-01-22', '06 12 34 56 28', '{"street": "35 rue de la Gare", "city": "Dijon", "zip": "21000", "country": "France"}'::jsonb, true),
('USR029', 'fabrice.guerin@email.fr', 'Fabrice Guerin', '1969-06-10', '06 12 34 56 29', '{"street": "19 place de la Comedie", "city": "Montpellier", "zip": "34000", "country": "France"}'::jsonb, true),
('USR030', 'audrey.chevalier@email.fr', 'Audrey Chevalier', '1988-11-07', '06 12 34 56 30', '{"street": "44 rue Paradis", "city": "Marseille", "zip": "13006", "country": "France"}'::jsonb, true);

-- ============================================================================
-- 60 CONTRACTS (2 per user, matching claim types for first 10)
-- ============================================================================
INSERT INTO user_contracts (user_id, contract_number, contract_type, start_date, end_date, coverage_amount, premium_amount, payment_frequency, full_text, key_terms, coverage_details, exclusions, is_active) VALUES
-- USR001: Health (claim 1 = Medical) + Auto
('USR001', 'CNT-2024-0001', 'Health Insurance', '2024-01-01', '2025-12-31', 50000.00, 280.00, 'monthly', 'Assurance sante complementaire. Hospitalisation, medecine de ville, dentaire, optique. Franchise 300 EUR.', '{"franchise": 300, "copay": 25, "hospitalisation": "100%"}'::jsonb, '{"hospitalisation": true, "medecine_ville": true, "dentaire": true, "optique": true, "maternite": true}'::jsonb, '{"chirurgie_esthetique": true, "medecine_douce_non_conventionnelle": true}'::jsonb, true),
('USR001', 'CNT-2024-0002', 'Auto Insurance', '2024-01-01', '2025-12-31', 35000.00, 95.00, 'monthly', 'Assurance auto tous risques. Vehicule: Peugeot 3008. Franchise 400 EUR.', '{"franchise": 400, "responsabilite_civile": 100000, "bris_glace": true}'::jsonb, '{"tous_risques": true, "vol": true, "incendie": true, "bris_glace": true}'::jsonb, '{"course_competition": true, "transport_marchandises_dangereuses": true}'::jsonb, true),
-- USR002: Auto (claim 2 = Auto) + Home
('USR002', 'CNT-2024-0003', 'Auto Insurance', '2024-01-01', '2025-12-31', 40000.00, 110.00, 'monthly', 'Assurance auto tous risques. Vehicule: Renault Megane. Franchise 350 EUR collision.', '{"franchise": 350, "responsabilite_civile": 150000}'::jsonb, '{"tous_risques": true, "assistance_0km": true, "vehicule_remplacement": true}'::jsonb, '{"course_competition": true, "alcoolemie": true}'::jsonb, true),
('USR002', 'CNT-2024-0004', 'Home Insurance', '2024-01-01', '2025-12-31', 250000.00, 45.00, 'monthly', 'Assurance habitation multirisque. Appartement T3 Lyon 6eme.', '{"franchise": 300, "valeur_mobilier": 30000}'::jsonb, '{"incendie": true, "degats_eaux": true, "vol": true, "responsabilite_civile": true}'::jsonb, '{"inondation_zone_rouge": true}'::jsonb, true),
-- USR003: Auto (claim 3 = Auto) + Health
('USR003', 'CNT-2024-0005', 'Auto Insurance', '2024-01-01', '2025-12-31', 45000.00, 130.00, 'monthly', 'Assurance auto tous risques. Vehicule: BMW Serie 3. Franchise 500 EUR. Exclusion course.', '{"franchise": 500, "responsabilite_civile": 200000}'::jsonb, '{"tous_risques": true, "vol": true, "incendie": true}'::jsonb, '{"course_competition": true, "circuit": true}'::jsonb, true),
('USR003', 'CNT-2024-0006', 'Health Insurance', '2024-01-01', '2025-12-31', 60000.00, 310.00, 'monthly', 'Assurance sante famille. 3 ayants droit. Hospitalisation 100%.', '{"franchise": 200, "copay": 20}'::jsonb, '{"hospitalisation": true, "specialistes": true, "urgences": true}'::jsonb, '{"chirurgie_esthetique": true}'::jsonb, true),
-- USR004: Home (claim 4 = Home) + Life
('USR004', 'CNT-2024-0007', 'Home Insurance', '2024-01-01', '2025-12-31', 350000.00, 55.00, 'monthly', 'Assurance habitation multirisque. Maison individuelle Lyon. Couverture tempete incluse.', '{"franchise": 500, "valeur_mobilier": 50000, "dependances": true}'::jsonb, '{"incendie": true, "degats_eaux": true, "tempete": true, "vol": true, "catastrophe_naturelle": true}'::jsonb, '{"defaut_entretien": true, "piscine_non_securisee": true}'::jsonb, true),
('USR004', 'CNT-2024-0008', 'Life Insurance', '2024-01-01', '2034-12-31', 500000.00, 150.00, 'monthly', 'Assurance vie capital deces. Beneficiaire: conjoint.', '{"duree": "10 ans", "beneficiaire": "conjoint"}'::jsonb, '{"deces": true, "invalidite_permanente": true}'::jsonb, '{"suicide_premiere_annee": true, "guerre": true}'::jsonb, true),
-- USR005: Health (claim 5 = Medical) + Auto
('USR005', 'CNT-2024-0009', 'Health Insurance', '2024-01-01', '2025-12-31', 75000.00, 350.00, 'monthly', 'Assurance sante premium. Chambre particuliere, depassements honoraires 200%.', '{"franchise": 0, "depassements": "200%"}'::jsonb, '{"hospitalisation": true, "chambre_particuliere": true, "medecine_douce": true}'::jsonb, '{"chirurgie_esthetique": true}'::jsonb, true),
('USR005', 'CNT-2024-0010', 'Auto Insurance', '2024-01-01', '2025-12-31', 30000.00, 85.00, 'monthly', 'Assurance auto tiers etendu. Vehicule: Toyota Yaris.', '{"franchise": 300}'::jsonb, '{"responsabilite_civile": true, "vol": true, "incendie": true}'::jsonb, '{"collision": false}'::jsonb, true),
-- USR006: Auto (claim 6 = Auto) + Home
('USR006', 'CNT-2024-0011', 'Auto Insurance', '2024-01-01', '2025-12-31', 55000.00, 140.00, 'monthly', 'Assurance auto tous risques. Vehicule: Audi A4. Constat amiable inclus.', '{"franchise": 400, "responsabilite_civile": 200000}'::jsonb, '{"tous_risques": true, "protection_juridique": true}'::jsonb, '{"alcoolemie": true, "stupefiants": true}'::jsonb, true),
('USR006', 'CNT-2024-0012', 'Home Insurance', '2024-01-01', '2025-12-31', 280000.00, 50.00, 'monthly', 'Assurance habitation. Appartement T4 Lyon.', '{"franchise": 350}'::jsonb, '{"incendie": true, "degats_eaux": true, "vol": true}'::jsonb, '{"negligence_grave": true}'::jsonb, true),
-- USR007: Home (claim 7 = Home) + Health
('USR007', 'CNT-2024-0013', 'Home Insurance', '2024-01-01', '2025-12-31', 300000.00, 48.00, 'monthly', 'Assurance habitation multirisque. Maison Toulouse. Exclusion defaut entretien explicite clause 4.7.', '{"franchise": 400, "valeur_mobilier": 40000}'::jsonb, '{"incendie": true, "degats_eaux": true, "vol": true, "tempete": true}'::jsonb, '{"defaut_entretien": true, "vice_construction": true}'::jsonb, true),
('USR007', 'CNT-2024-0014', 'Health Insurance', '2024-01-01', '2025-12-31', 45000.00, 240.00, 'monthly', 'Assurance sante basique. Hospitalisation et soins courants.', '{"franchise": 400, "copay": 30}'::jsonb, '{"hospitalisation": true, "medecine_ville": true}'::jsonb, '{"medecine_douce": true}'::jsonb, true),
-- USR008: Health (claim 8 = Medical) + Life
('USR008', 'CNT-2024-0015', 'Health Insurance', '2024-01-01', '2025-12-31', 55000.00, 290.00, 'monthly', 'Assurance sante complementaire. Franchise 250 EUR.', '{"franchise": 250, "copay": 25}'::jsonb, '{"hospitalisation": true, "specialistes": true, "pharmacie": true}'::jsonb, '{"chirurgie_esthetique": true}'::jsonb, true),
('USR008', 'CNT-2024-0016', 'Life Insurance', '2024-01-01', '2034-12-31', 400000.00, 120.00, 'monthly', 'Assurance vie mixte. Capital deces + epargne.', '{"duree": "10 ans"}'::jsonb, '{"deces": true, "invalidite": true, "epargne": true}'::jsonb, '{"guerre": true}'::jsonb, true),
-- USR009: Auto (claim 9 = Auto) + Home
('USR009', 'CNT-2024-0017', 'Auto Insurance', '2024-01-01', '2025-12-31', 38000.00, 100.00, 'monthly', 'Assurance auto tous risques. Vehicule: Citroen C4. Exclusion contractuelle alcoolemie art. 8.3.', '{"franchise": 350, "responsabilite_civile": 150000}'::jsonb, '{"tous_risques": true, "assistance": true}'::jsonb, '{"alcoolemie": true, "stupefiants": true, "permis_invalide": true}'::jsonb, true),
('USR009', 'CNT-2024-0018', 'Home Insurance', '2024-01-01', '2025-12-31', 220000.00, 42.00, 'monthly', 'Assurance habitation. Appartement T2 Paris 5eme.', '{"franchise": 300}'::jsonb, '{"incendie": true, "degats_eaux": true, "vol": true}'::jsonb, '{"negligence_grave": true}'::jsonb, true),
-- USR010: Home (claim 10 = Home) + Auto
('USR010', 'CNT-2024-0019', 'Home Insurance', '2024-01-01', '2025-12-31', 320000.00, 52.00, 'monthly', 'Assurance habitation multirisque. Maison Lille. Historique sinistres multiple.', '{"franchise": 500, "valeur_mobilier": 45000}'::jsonb, '{"incendie": true, "degats_eaux": true, "vol": true, "tempete": true}'::jsonb, '{"defaut_entretien": true}'::jsonb, true),
('USR010', 'CNT-2024-0020', 'Auto Insurance', '2024-01-01', '2025-12-31', 32000.00, 90.00, 'monthly', 'Assurance auto tiers etendu. Vehicule: Dacia Sandero.', '{"franchise": 300}'::jsonb, '{"responsabilite_civile": true, "vol": true}'::jsonb, '{"collision": false}'::jsonb, true),
-- USR011 to USR030: 2 contracts each (varied types)
('USR011', 'CNT-2024-0021', 'Health Insurance', '2024-01-01', '2025-12-31', 48000.00, 260.00, 'monthly', 'Assurance sante complementaire.', '{"franchise": 300}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR011', 'CNT-2024-0022', 'Auto Insurance', '2024-01-01', '2025-12-31', 35000.00, 95.00, 'monthly', 'Assurance auto tiers.', '{"franchise": 400}'::jsonb, '{"responsabilite_civile": true}'::jsonb, '{}'::jsonb, true),
('USR012', 'CNT-2024-0023', 'Home Insurance', '2024-01-01', '2025-12-31', 270000.00, 47.00, 'monthly', 'Assurance habitation multirisque.', '{"franchise": 350}'::jsonb, '{"incendie": true, "degats_eaux": true}'::jsonb, '{}'::jsonb, true),
('USR012', 'CNT-2024-0024', 'Life Insurance', '2024-01-01', '2034-12-31', 300000.00, 100.00, 'monthly', 'Assurance vie capital deces.', '{"duree": "10 ans"}'::jsonb, '{"deces": true}'::jsonb, '{}'::jsonb, true),
('USR013', 'CNT-2024-0025', 'Auto Insurance', '2024-01-01', '2025-12-31', 42000.00, 115.00, 'monthly', 'Assurance auto tous risques.', '{"franchise": 350}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR013', 'CNT-2024-0026', 'Health Insurance', '2024-01-01', '2025-12-31', 52000.00, 275.00, 'monthly', 'Assurance sante famille.', '{"franchise": 250}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR014', 'CNT-2024-0027', 'Home Insurance', '2024-01-01', '2025-12-31', 380000.00, 60.00, 'monthly', 'Assurance habitation villa.', '{"franchise": 500}'::jsonb, '{"incendie": true, "vol": true}'::jsonb, '{}'::jsonb, true),
('USR014', 'CNT-2024-0028', 'Auto Insurance', '2024-01-01', '2025-12-31', 50000.00, 125.00, 'monthly', 'Assurance auto tous risques.', '{"franchise": 400}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR015', 'CNT-2024-0029', 'Health Insurance', '2024-01-01', '2025-12-31', 55000.00, 295.00, 'monthly', 'Assurance sante complementaire.', '{"franchise": 300}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR015', 'CNT-2024-0030', 'Life Insurance', '2024-01-01', '2034-12-31', 450000.00, 135.00, 'monthly', 'Assurance vie.', '{"duree": "10 ans"}'::jsonb, '{"deces": true}'::jsonb, '{}'::jsonb, true),
('USR016', 'CNT-2024-0031', 'Auto Insurance', '2024-01-01', '2025-12-31', 48000.00, 120.00, 'monthly', 'Assurance auto tous risques.', '{"franchise": 400}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR016', 'CNT-2024-0032', 'Home Insurance', '2024-01-01', '2025-12-31', 310000.00, 53.00, 'monthly', 'Assurance habitation.', '{"franchise": 400}'::jsonb, '{"incendie": true}'::jsonb, '{}'::jsonb, true),
('USR017', 'CNT-2024-0033', 'Health Insurance', '2024-01-01', '2025-12-31', 50000.00, 270.00, 'monthly', 'Assurance sante.', '{"franchise": 300}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR017', 'CNT-2024-0034', 'Auto Insurance', '2024-01-01', '2025-12-31', 36000.00, 92.00, 'monthly', 'Assurance auto tiers etendu.', '{"franchise": 350}'::jsonb, '{"responsabilite_civile": true}'::jsonb, '{}'::jsonb, true),
('USR018', 'CNT-2024-0035', 'Home Insurance', '2024-01-01', '2025-12-31', 290000.00, 49.00, 'monthly', 'Assurance habitation.', '{"franchise": 400}'::jsonb, '{"incendie": true, "degats_eaux": true}'::jsonb, '{}'::jsonb, true),
('USR018', 'CNT-2024-0036', 'Life Insurance', '2024-01-01', '2034-12-31', 350000.00, 110.00, 'monthly', 'Assurance vie.', '{"duree": "10 ans"}'::jsonb, '{"deces": true}'::jsonb, '{}'::jsonb, true),
('USR019', 'CNT-2024-0037', 'Auto Insurance', '2024-01-01', '2025-12-31', 40000.00, 105.00, 'monthly', 'Assurance auto tous risques.', '{"franchise": 400}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR019', 'CNT-2024-0038', 'Health Insurance', '2024-01-01', '2025-12-31', 47000.00, 255.00, 'monthly', 'Assurance sante.', '{"franchise": 350}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR020', 'CNT-2024-0039', 'Home Insurance', '2024-01-01', '2025-12-31', 260000.00, 44.00, 'monthly', 'Assurance habitation.', '{"franchise": 350}'::jsonb, '{"incendie": true}'::jsonb, '{}'::jsonb, true),
('USR020', 'CNT-2024-0040', 'Auto Insurance', '2024-01-01', '2025-12-31', 33000.00, 88.00, 'monthly', 'Assurance auto tiers.', '{"franchise": 300}'::jsonb, '{"responsabilite_civile": true}'::jsonb, '{}'::jsonb, true),
('USR021', 'CNT-2024-0041', 'Health Insurance', '2024-01-01', '2025-12-31', 52000.00, 280.00, 'monthly', 'Assurance sante.', '{"franchise": 300}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR021', 'CNT-2024-0042', 'Life Insurance', '2024-01-01', '2034-12-31', 400000.00, 125.00, 'monthly', 'Assurance vie.', '{"duree": "10 ans"}'::jsonb, '{"deces": true}'::jsonb, '{}'::jsonb, true),
('USR022', 'CNT-2024-0043', 'Auto Insurance', '2024-01-01', '2025-12-31', 44000.00, 112.00, 'monthly', 'Assurance auto tous risques.', '{"franchise": 400}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR022', 'CNT-2024-0044', 'Home Insurance', '2024-01-01', '2025-12-31', 285000.00, 48.00, 'monthly', 'Assurance habitation.', '{"franchise": 350}'::jsonb, '{"incendie": true}'::jsonb, '{}'::jsonb, true),
('USR023', 'CNT-2024-0045', 'Health Insurance', '2024-01-01', '2025-12-31', 49000.00, 265.00, 'monthly', 'Assurance sante.', '{"franchise": 300}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR023', 'CNT-2024-0046', 'Auto Insurance', '2024-01-01', '2025-12-31', 37000.00, 96.00, 'monthly', 'Assurance auto.', '{"franchise": 350}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR024', 'CNT-2024-0047', 'Home Insurance', '2024-01-01', '2025-12-31', 240000.00, 42.00, 'monthly', 'Assurance habitation.', '{"franchise": 300}'::jsonb, '{"incendie": true}'::jsonb, '{}'::jsonb, true),
('USR024', 'CNT-2024-0048', 'Life Insurance', '2024-01-01', '2034-12-31', 350000.00, 105.00, 'monthly', 'Assurance vie.', '{"duree": "10 ans"}'::jsonb, '{"deces": true}'::jsonb, '{}'::jsonb, true),
('USR025', 'CNT-2024-0049', 'Auto Insurance', '2024-01-01', '2025-12-31', 41000.00, 108.00, 'monthly', 'Assurance auto tous risques.', '{"franchise": 400}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR025', 'CNT-2024-0050', 'Health Insurance', '2024-01-01', '2025-12-31', 53000.00, 285.00, 'monthly', 'Assurance sante.', '{"franchise": 250}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR026', 'CNT-2024-0051', 'Home Insurance', '2024-01-01', '2025-12-31', 275000.00, 46.00, 'monthly', 'Assurance habitation.', '{"franchise": 350}'::jsonb, '{"incendie": true, "degats_eaux": true}'::jsonb, '{}'::jsonb, true),
('USR026', 'CNT-2024-0052', 'Auto Insurance', '2024-01-01', '2025-12-31', 39000.00, 102.00, 'monthly', 'Assurance auto.', '{"franchise": 350}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR027', 'CNT-2024-0053', 'Health Insurance', '2024-01-01', '2025-12-31', 51000.00, 278.00, 'monthly', 'Assurance sante.', '{"franchise": 300}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR027', 'CNT-2024-0054', 'Life Insurance', '2024-01-01', '2034-12-31', 380000.00, 115.00, 'monthly', 'Assurance vie.', '{"duree": "10 ans"}'::jsonb, '{"deces": true}'::jsonb, '{}'::jsonb, true),
('USR028', 'CNT-2024-0055', 'Auto Insurance', '2024-01-01', '2025-12-31', 34000.00, 90.00, 'monthly', 'Assurance auto tiers etendu.', '{"franchise": 300}'::jsonb, '{"responsabilite_civile": true}'::jsonb, '{}'::jsonb, true),
('USR028', 'CNT-2024-0056', 'Home Insurance', '2024-01-01', '2025-12-31', 230000.00, 40.00, 'monthly', 'Assurance habitation.', '{"franchise": 300}'::jsonb, '{"incendie": true}'::jsonb, '{}'::jsonb, true),
('USR029', 'CNT-2024-0057', 'Health Insurance', '2024-01-01', '2025-12-31', 46000.00, 250.00, 'monthly', 'Assurance sante.', '{"franchise": 350}'::jsonb, '{"hospitalisation": true}'::jsonb, '{}'::jsonb, true),
('USR029', 'CNT-2024-0058', 'Auto Insurance', '2024-01-01', '2025-12-31', 43000.00, 118.00, 'monthly', 'Assurance auto tous risques.', '{"franchise": 400}'::jsonb, '{"tous_risques": true}'::jsonb, '{}'::jsonb, true),
('USR030', 'CNT-2024-0059', 'Home Insurance', '2024-01-01', '2025-12-31', 340000.00, 56.00, 'monthly', 'Assurance habitation multirisque.', '{"franchise": 450}'::jsonb, '{"incendie": true, "degats_eaux": true, "vol": true}'::jsonb, '{}'::jsonb, true),
('USR030', 'CNT-2024-0060', 'Life Insurance', '2024-01-01', '2034-12-31', 420000.00, 130.00, 'monthly', 'Assurance vie.', '{"duree": "10 ans"}'::jsonb, '{"deces": true}'::jsonb, '{}'::jsonb, true);

-- ============================================================================
-- 30 CLAIMS (all pending, init_data.py processes first 10)
-- Distribution: Medical (8), Auto (10), Home (9), Life (3)
-- ============================================================================
INSERT INTO claims (user_id, claim_number, claim_type, document_path, status, submitted_at) VALUES
-- 10 claims to be processed by init_data.py
('USR001', 'CLM-2024-0001', 'Medical', 'claims/claim_medical_001.pdf', 'pending', '2025-11-15 09:30:00'),
('USR002', 'CLM-2024-0002', 'Auto', 'claims/claim_auto_001.pdf', 'pending', '2025-11-18 14:15:00'),
('USR003', 'CLM-2024-0003', 'Auto', 'claims/claim_auto_002.pdf', 'pending', '2025-11-20 10:45:00'),
('USR004', 'CLM-2024-0004', 'Home', 'claims/claim_home_001.pdf', 'pending', '2025-11-22 16:00:00'),
('USR005', 'CLM-2024-0005', 'Medical', 'claims/claim_medical_002.pdf', 'pending', '2025-11-25 08:20:00'),
('USR006', 'CLM-2024-0006', 'Auto', 'claims/claim_auto_003.pdf', 'pending', '2025-11-27 11:30:00'),
('USR007', 'CLM-2024-0007', 'Home', 'claims/claim_home_002.pdf', 'pending', '2025-11-29 13:45:00'),
('USR008', 'CLM-2024-0008', 'Medical', 'claims/claim_medical_003.pdf', 'pending', '2025-12-01 09:10:00'),
('USR009', 'CLM-2024-0009', 'Auto', 'claims/claim_auto_004.pdf', 'pending', '2025-12-03 15:30:00'),
('USR010', 'CLM-2024-0010', 'Home', 'claims/claim_home_003.pdf', 'pending', '2025-12-05 10:00:00'),
-- 20 remaining claims (stay pending)
('USR011', 'CLM-2024-0011', 'Medical', 'claims/claim_medical_004.pdf', 'pending', '2025-12-07 08:45:00'),
('USR012', 'CLM-2024-0012', 'Auto', 'claims/claim_auto_005.pdf', 'pending', '2025-12-09 14:20:00'),
('USR013', 'CLM-2024-0013', 'Home', 'claims/claim_home_004.pdf', 'pending', '2025-12-11 11:15:00'),
('USR014', 'CLM-2024-0014', 'Auto', 'claims/claim_auto_006.pdf', 'pending', '2025-12-13 16:30:00'),
('USR015', 'CLM-2024-0015', 'Medical', 'claims/claim_medical_005.pdf', 'pending', '2025-12-15 09:00:00'),
('USR016', 'CLM-2024-0016', 'Auto', 'claims/claim_auto_007.pdf', 'pending', '2025-12-17 13:45:00'),
('USR017', 'CLM-2024-0017', 'Home', 'claims/claim_home_005.pdf', 'pending', '2025-12-19 10:30:00'),
('USR018', 'CLM-2024-0018', 'Life', 'claims/claim_life_001.pdf', 'pending', '2025-12-21 15:00:00'),
('USR019', 'CLM-2024-0019', 'Auto', 'claims/claim_auto_008.pdf', 'pending', '2025-12-23 08:15:00'),
('USR020', 'CLM-2024-0020', 'Home', 'claims/claim_home_006.pdf', 'pending', '2025-12-25 12:00:00'),
('USR021', 'CLM-2024-0021', 'Medical', 'claims/claim_medical_006.pdf', 'pending', '2025-12-27 14:30:00'),
('USR022', 'CLM-2024-0022', 'Auto', 'claims/claim_auto_009.pdf', 'pending', '2025-12-29 09:45:00'),
('USR023', 'CLM-2024-0023', 'Home', 'claims/claim_home_007.pdf', 'pending', '2026-01-02 11:00:00'),
('USR024', 'CLM-2024-0024', 'Life', 'claims/claim_life_002.pdf', 'pending', '2026-01-04 16:15:00'),
('USR025', 'CLM-2024-0025', 'Medical', 'claims/claim_medical_007.pdf', 'pending', '2026-01-06 08:30:00'),
('USR026', 'CLM-2024-0026', 'Auto', 'claims/claim_auto_010.pdf', 'pending', '2026-01-08 13:00:00'),
('USR027', 'CLM-2024-0027', 'Home', 'claims/claim_home_008.pdf', 'pending', '2026-01-10 10:45:00'),
('USR028', 'CLM-2024-0028', 'Medical', 'claims/claim_medical_008.pdf', 'pending', '2026-01-12 15:30:00'),
('USR029', 'CLM-2024-0029', 'Life', 'claims/claim_life_003.pdf', 'pending', '2026-01-14 09:15:00'),
('USR030', 'CLM-2024-0030', 'Auto', 'claims/claim_auto_011.pdf', 'pending', '2026-01-16 14:00:00');

-- ============================================================================
-- BILINGUAL METADATA FOR CLAIMS
-- ============================================================================
UPDATE claims SET metadata = '{"description": "Examen physique annuel avec bilan sanguin complet, ECG realise en raison d''antecedents familiaux.", "description_en": "Annual physical examination with comprehensive blood work panel, EKG performed due to family history.", "document_path_en": "claims/claim_medical_001_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0001';
UPDATE claims SET metadata = '{"description": "Collision par l''arriere a l''intersection de Route 66 et Main St. L''autre conducteur a grille un feu rouge.", "description_en": "Rear-end collision at intersection of Route 66 and Main St. The other driver ran a red light.", "document_path_en": "claims/claim_auto_001_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0002';
UPDATE claims SET metadata = '{"description": "Collision laterale sur l''autoroute I-55 lors d''un changement de voie.", "description_en": "Side-swipe collision on highway I-55 during lane change. Other vehicle merged without checking blind spot.", "document_path_en": "claims/claim_auto_002_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0003';
UPDATE claims SET metadata = '{"description": "Tuyau eclate dans la cuisine sous l''evier. Tuyauterie datant de 1985.", "description_en": "Burst pipe in kitchen under the sink. Pipe corroded due to age (original 1985 plumbing). Water flowed for approximately 4 hours before discovery.", "document_path_en": "claims/claim_home_001_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0004';
UPDATE claims SET metadata = '{"description": "Visite aux urgences pour douleur thoracique aigue. Angioscanner, dosage troponine.", "description_en": "Emergency room visit for acute chest pain. CT angiogram, troponin levels x3, cardiac monitoring 6 hours.", "document_path_en": "claims/claim_medical_002_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0005';
UPDATE claims SET metadata = '{"description": "Collision par l''arriere sur le parking de Walmart en reculant.", "description_en": "Rear-end collision in Walmart parking lot while backing out of space. Low speed impact.", "document_path_en": "claims/claim_auto_003_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0006';
UPDATE claims SET metadata = '{"description": "Orage violent avec vents de 110 km/h causant des dommages aux bardeaux de toiture.", "description_en": "Severe thunderstorm with 70mph winds caused roof shingle damage and subsequent leak.", "document_path_en": "claims/claim_home_002_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0007';
UPDATE claims SET metadata = '{"description": "Chirurgie de reconstruction du LCA par arthroscopie avec autogreffe.", "description_en": "Arthroscopic ACL reconstruction surgery with hamstring autograft. Pre-op MRI, anesthesia, 2-night hospital stay.", "document_path_en": "claims/claim_medical_003_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0008';
UPDATE claims SET metadata = '{"description": "Delit de fuite pendant que le vehicule etait stationne dans la rue Elm durant la nuit.", "description_en": "Hit-and-run incident while vehicle was parked on Elm Street overnight. Discovered damage in the morning.", "document_path_en": "claims/claim_auto_004_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0009';
UPDATE claims SET metadata = '{"description": "Incendie electrique dans le garage (circuit surcharge). Degats de fumee au rez-de-chaussee.", "description_en": "Electrical fire originated in garage outlet (overloaded circuit). Fire contained to garage but smoke damage throughout first floor.", "document_path_en": "claims/claim_home_003_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0010';
UPDATE claims SET metadata = '{"description": "IRM diagnostique du rachis lombaire avec et sans injection de produit de contraste.", "description_en": "Diagnostic MRI of lumbar spine with and without contrast. Radiologist interpretation and report.", "document_path_en": "claims/claim_medical_004_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0011';
UPDATE claims SET metadata = '{"description": "Accrochage au feu rouge sur 5th et Main. Le vehicule devant s''est arrete brusquement.", "description_en": "Fender bender at stoplight on 5th and Main. Vehicle ahead stopped suddenly for pedestrian.", "document_path_en": "claims/claim_auto_005_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0012';
UPDATE claims SET metadata = '{"description": "Grand chene tombe sur la maison lors d''une tempete de verglas.", "description_en": "Large oak tree fell on house during ice storm. Tree was approximately 60 feet tall and landed across the roof ridge.", "document_path_en": "claims/claim_home_004_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0013';
UPDATE claims SET metadata = '{"description": "Carambolage sur la Highway 66 a cause d''un brouillard soudain.", "description_en": "Multi-vehicle pileup on Highway 66 due to sudden fog. Chain reaction involving 4 vehicles.", "document_path_en": "claims/claim_auto_006_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0014';
UPDATE claims SET metadata = '{"description": "Kinesitherapie - 12 seances post-reconstruction du LCA.", "description_en": "Physical therapy - 12 sessions post ACL reconstruction. Includes ROM exercises, strengthening, gait training.", "document_path_en": "claims/claim_medical_005_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0015';
UPDATE claims SET metadata = '{"description": "Collision avec un cerf traversant une route de campagne au crepuscule.", "description_en": "Collision with deer crossing rural road at dusk. Animal appeared suddenly from wooded area.", "document_path_en": "claims/claim_auto_007_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0016';
UPDATE claims SET metadata = '{"description": "Inondation du sous-sol suite a une panne de pompe de relevage lors de fortes pluies.", "description_en": "Basement flooding from sump pump failure during heavy rainfall. Pump motor burned out, backup battery also dead.", "document_path_en": "claims/claim_home_005_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0017';
UPDATE claims SET metadata = '{"description": "Accident de la route - collision frontale sur autoroute A4. Hospitalisation en soins intensifs.", "description_en": "Road accident - head-on collision on the A4 highway. Hospitalized in intensive care for 3 weeks. Permanent after-effects with partial disability assessed at 40%.", "document_path_en": "claims/claim_life_001_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0018';
UPDATE claims SET metadata = '{"description": "Marche arriere contre un poteau en beton dans un parking couvert.", "description_en": "Backed into concrete pole in shopping center parking garage. Limited visibility due to pillar obstruction.", "document_path_en": "claims/claim_auto_008_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0019';
UPDATE claims SET metadata = '{"description": "Vandalisme - pierres lancees a travers la baie vitree du salon. Rapport de police depose.", "description_en": "Vandalism - rocks thrown through living room bay window. Incident occurred during nighttime. Police report filed.", "document_path_en": "claims/claim_home_006_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0020';
UPDATE claims SET metadata = '{"description": "Remplacement de couronne dentaire - couronne ceramique-metal sur molaire n30.", "description_en": "Dental crown replacement - porcelain-fused-to-metal crown on molar #30. Includes impression, temporary crown, and final placement.", "document_path_en": "claims/claim_medical_006_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0021';
UPDATE claims SET metadata = '{"description": "Collision en T a une intersection sans signalisation.", "description_en": "T-bone collision at uncontrolled intersection. Other driver failed to yield right of way.", "document_path_en": "claims/claim_auto_009_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0022';
UPDATE claims SET metadata = '{"description": "Rupture du flexible d''alimentation du lave-vaisselle. Fuite d''eau pendant 8 heures.", "description_en": "Dishwasher supply line failed (braided stainless steel connector burst). Water leaked for estimated 8 hours overnight.", "document_path_en": "claims/claim_home_007_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0023';
UPDATE claims SET metadata = '{"description": "Maladie grave diagnostiquee - cancer du poumon stade III. Chimiotherapie en cours.", "description_en": "Severe illness diagnosed - stage III lung cancer. Chemotherapy and radiation treatment ongoing. Extended work leave.", "document_path_en": "claims/claim_life_002_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0024';
UPDATE claims SET metadata = '{"description": "Bilan allergologique complet (environnemental et alimentaire) - 60 tests cutanes.", "description_en": "Comprehensive allergy testing panel (environmental and food) - 60 allergen skin prick test plus specific IgE blood panel.", "document_path_en": "claims/claim_medical_007_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0025';
UPDATE claims SET metadata = '{"description": "Perte de controle sur route verglacee et glissade contre la glissiere de securite.", "description_en": "Lost control on icy road and slid into guardrail. Black ice conditions, temperature was 28F.", "document_path_en": "claims/claim_auto_010_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0026';
UPDATE claims SET metadata = '{"description": "Foudre tombee sur la cheminee lors d''un violent orage. Surtension electrique.", "description_en": "Lightning strike hit chimney during severe thunderstorm. Electrical surge destroyed electronics and caused small fire in attic.", "document_path_en": "claims/claim_home_008_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0027';
UPDATE claims SET metadata = '{"description": "Coloscopie de depistage avec ablation de polypes. Sedation moderee.", "description_en": "Screening colonoscopy with polyp removal (2 sessile polyps removed via snare polypectomy). Moderate sedation.", "document_path_en": "claims/claim_medical_008_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0028';
UPDATE claims SET metadata = '{"description": "Accident domestique grave - chute d''une echelle lors de travaux de toiture.", "description_en": "Serious domestic accident - fell from a ladder during roofing work. Severe head trauma and multiple fractures. Emergency surgery performed.", "document_path_en": "claims/claim_life_003_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0029';
UPDATE claims SET metadata = '{"description": "Collision par l''arriere alors que le vehicule etait arrete a un passage a niveau.", "description_en": "Rear-ended while stopped at railroad crossing. Following vehicle distracted by phone.", "document_path_en": "claims/claim_auto_011_en.pdf"}'::jsonb WHERE claim_number = 'CLM-2024-0030';

-- ============================================================================
-- KNOWLEDGE BASE ARTICLES
-- ============================================================================
INSERT INTO knowledge_base (title, content, category, tags, is_active, effective_date) VALUES
('Procedure de declaration de sinistre medical', 'Toute declaration de sinistre medical doit etre effectuee dans les 90 jours suivant le soin. Documents requis: factures detaillees, codes CCAM/NGAP, justificatif de paiement. Les sinistres superieurs a 5000 EUR necessitent un accord prealable.', 'Traitement sinistres', ARRAY['medical', 'declaration'], true, '2024-01-01'),
('Services medicaux couverts', 'Couverture: medecine de ville, specialistes, urgences, hospitalisation, chirurgie, pharmacie, soins preventifs, imagerie. Exclusions: chirurgie esthetique, traitements experimentaux.', 'Couverture', ARRAY['medical', 'couverture'], true, '2024-01-01'),
('Procedure sinistre automobile', 'Etapes: 1) Constat amiable sous 5 jours, 2) Photos et rapport police si necessaire, 3) Declaration sous 30 jours, 4) Expertise vehicule, 5) Indemnisation ou reparation.', 'Traitement sinistres', ARRAY['auto', 'procedure'], true, '2024-01-01'),
('Franchises et participations forfaitaires', 'La franchise est le montant restant a la charge de l''assure. Participation forfaitaire de 1 EUR par acte medical. La franchise se reinitialise au 1er janvier de chaque annee.', 'Conditions generales', ARRAY['franchise', 'participation'], true, '2024-01-01'),
('Accord prealable et entente prealable', 'Accord prealable requis pour: IRM/scanner, chirurgie non urgente, protheses, cures thermales, hospitalisation programmee. Demande a soumettre 15 jours avant le soin.', 'Autorisation', ARRAY['accord_prealable', 'approbation'], true, '2024-01-01'),
('Couverture habitation multirisque', 'Couvre: structure, biens mobiliers, responsabilite civile, frais de relogement. Franchise applicable par sinistre. Inondation couverte uniquement si declaration catastrophe naturelle.', 'Couverture', ARRAY['habitation', 'couverture'], true, '2024-01-01'),
('Capital deces assurance vie', 'Le capital deces est verse au(x) beneficiaire(s) designe(s) au deces de l''assure. Documents requis: acte de deces, formulaire de declaration. Versement sous 30 jours apres acceptation.', 'Traitement sinistres', ARRAY['vie', 'capital_deces'], true, '2024-01-01'),
('Vol de vehicule', 'Declaration de vol a la police sous 24h obligatoire. Fournir cles, carte grise, recepisse de plainte. Delai de carence 30 jours. Indemnisation en valeur venale si non retrouve.', 'Traitement sinistres', ARRAY['auto', 'vol'], true, '2024-01-01'),
('Degats des eaux', 'Degats des eaux soudains et accidentels couverts. Exclusions: inondation hors catastrophe naturelle, infiltrations progressives, defaut d''entretien. Declaration immediate obligatoire.', 'Couverture', ARRAY['habitation', 'degats_eaux'], true, '2024-01-01'),
('Prise en charge chirurgicale', 'Interventions chirurgicales couvertes apres franchise. Comprend sejour hospitalier, honoraires chirurgien, anesthesie. Accord prealable non requis pour les urgences.', 'Couverture', ARRAY['medical', 'chirurgie'], true, '2024-01-01'),
('Formulaire pharmacie', 'Niveau 1 (generiques): 10 EUR, Niveau 2 (marque preferee): 30 EUR, Niveau 3 (non preferee): 60 EUR. Envoi courrier 90 jours disponible.', 'Couverture', ARRAY['pharmacie', 'medicaments'], true, '2024-01-01'),
('Cambriolage et vol', 'Depot de plainte sous 48h obligatoire. Fournir factures ou preuves de propriete. Remplacement serrures pris en charge. Vetuste deduite selon grille.', 'Traitement sinistres', ARRAY['habitation', 'vol'], true, '2024-01-01'),
('Garantie collision', 'Couvre les dommages resultant d''une collision quel que soit le responsable. Franchise applicable. Inclut vehicule de remplacement jusqu''a 40 EUR/jour pendant 30 jours.', 'Couverture', ARRAY['auto', 'collision'], true, '2024-01-01'),
('Orientation vers specialiste', 'Lettre d''orientation du medecin traitant necessaire. Specialiste dans le reseau de soins. Participation 35 EUR. Accord prealable pour certains actes.', 'Conditions generales', ARRAY['medical', 'specialiste'], true, '2024-01-01'),
('Plafonds de garantie', 'Medical: 1M EUR plafond annuel. Auto: 100K EUR dommages materiels. Habitation: montant souscrit en police. Vie: valeur nominale du contrat.', 'Conditions generales', ARRAY['plafonds', 'limites'], true, '2024-01-01');

-- ============================================================================
-- 1. COMPANY REFERENCES — 10 completed projects
-- ============================================================================
INSERT INTO company_references (
    id, reference_number, project_name, maitre_ouvrage, nature_travaux,
    montant, date_debut, date_fin, region, description,
    certifications_used, key_metrics, is_active
) VALUES

-- REF-2023-001: Gros oeuvre — Logements collectifs
(
    gen_random_uuid(),
    'REF-2023-001',
    'Construction de 120 logements collectifs - Eco-quartier des Musiciens',
    'Metropole de Lyon',
    'Gros oeuvre - Construction neuve logements collectifs',
    18500000.00,
    '2021-03-15',
    '2023-09-30',
    'Auvergne-Rhone-Alpes',
    'Construction de 120 logements collectifs repartis sur 3 batiments R+7 dans le cadre de l''eco-quartier des Musiciens a Villeurbanne. Fondations profondes sur pieux, structure beton arme, facade a isolation par l''exterieur. Demarche HQE avec objectif RT2012 -20% et label E+C- niveau E2C1.',
    '["ISO 9001:2015", "ISO 14001:2015", "Qualibat 2112", "NF Habitat HQE"]'::jsonb,
    '{"surface_plancher_m2": 9600, "nombre_batiments": 3, "nombre_niveaux": 8, "duree_mois": 30, "effectif_moyen": 45, "taux_sinistralite": 0.0, "satisfaction_client": 4.5}'::jsonb,
    true
),

-- REF-2023-002: Genie civil — Pont
(
    gen_random_uuid(),
    'REF-2023-002',
    'Reconstruction du pont de la Garonne - RD813',
    'Conseil Departemental de la Gironde',
    'Genie civil - Ouvrage d''art courant',
    12800000.00,
    '2021-06-01',
    '2023-12-15',
    'Nouvelle-Aquitaine',
    'Reconstruction complete du pont de la Garonne sur la RD813, ouvrage a 4 travees en beton precontraint par post-tension. Longueur totale 180 m, largeur 12 m. Travaux realises en site aquatique avec batardeaux et palplanches. Maintien partiel de la circulation pendant les travaux avec mise en place d''un pont provisoire Bailey.',
    '["ISO 9001:2015", "Qualibat 2112", "MASE"]'::jsonb,
    '{"longueur_ouvrage_m": 180, "largeur_m": 12, "nombre_travees": 4, "volume_beton_m3": 3200, "tonnage_acier_t": 450, "duree_mois": 30, "effectif_moyen": 35, "taux_sinistralite": 0.0}'::jsonb,
    true
),

-- REF-2023-003: Gros oeuvre — Immeuble bureaux
(
    gen_random_uuid(),
    'REF-2023-003',
    'Construction immeuble de bureaux "Le Mirabeau" - La Defense',
    'Unibail-Rodamco-Westfield',
    'Gros oeuvre - Construction neuve tertiaire',
    45000000.00,
    '2020-09-01',
    '2023-06-30',
    'Ile-de-France',
    'Construction d''un immeuble de bureaux de grande hauteur (IGH) R+22 sur 3 niveaux de sous-sol a La Defense. Surface totale de 28 000 m2 SHON. Structure mixte acier-beton avec noyau central en beton arme. Certification BREEAM Excellent visee, equipements CVC haute performance, facade double peau ventilee.',
    '["ISO 9001:2015", "ISO 14001:2015", "Qualibat 2112", "CSTB Avis Technique"]'::jsonb,
    '{"surface_shon_m2": 28000, "nombre_niveaux": 25, "sous_sols": 3, "volume_beton_m3": 18000, "tonnage_acier_t": 2800, "duree_mois": 33, "effectif_moyen": 120, "satisfaction_client": 4.7}'::jsonb,
    true
),

-- REF-2023-004: Rehabilitation — Renovation batiment
(
    gen_random_uuid(),
    'REF-2023-004',
    'Rehabilitation de l''ancien Hotel des Postes - Centre-ville de Marseille',
    'Ville de Marseille',
    'Rehabilitation - Renovation lourde batiment patrimonial',
    8200000.00,
    '2022-01-10',
    '2023-11-30',
    'Provence-Alpes-Cote d''Azur',
    'Rehabilitation complete de l''ancien Hotel des Postes classe Monument Historique pour transformation en mediatheque municipale. Renforcement structurel par micropieux et chemisage poteaux, reprise integrale des planchers, creation d''un ascenseur et mise aux normes accessibilite PMR. Travaux de restauration des facades en pierre de taille et des elements decoratifs d''epoque.',
    '["ISO 9001:2015", "Qualibat 2112", "Qualibat 1311"]'::jsonb,
    '{"surface_plancher_m2": 4500, "nombre_niveaux": 4, "duree_mois": 22, "effectif_moyen": 30, "elements_patrimoniaux_restaures": 45, "satisfaction_client": 4.8}'::jsonb,
    true
),

-- REF-2023-005: VRD — Amenagement urbain
(
    gen_random_uuid(),
    'REF-2023-005',
    'Amenagement de la ZAC Bastide-Niel - Phase 2 VRD',
    'Bordeaux Metropole',
    'Voirie et Reseaux Divers - Amenagement urbain',
    6500000.00,
    '2022-04-01',
    '2023-10-15',
    'Nouvelle-Aquitaine',
    'Amenagement VRD complet de la phase 2 de la ZAC Bastide-Niel sur 12 hectares : voiries structurantes, reseaux d''assainissement separatifs (EU/EP), reseaux secs (electricite, telecoms, gaz), espaces verts et mobilier urbain. Integration de noues paysageres et bassins de retention pour gestion alternative des eaux pluviales.',
    '["ISO 9001:2015", "ISO 14001:2015", "Qualibat 1311", "RGE"]'::jsonb,
    '{"lineaire_voirie_ml": 3200, "lineaire_reseaux_ml": 8500, "surface_espaces_verts_m2": 15000, "duree_mois": 18, "effectif_moyen": 25, "volume_terrassement_m3": 45000}'::jsonb,
    true
),

-- REF-2023-006: Genie civil — Tunnel
(
    gen_random_uuid(),
    'REF-2023-006',
    'Prolongement du tunnel de la ligne B du metro - Lot GC2',
    'SNCF Reseau',
    'Genie civil - Tunnel et ouvrages souterrains',
    38000000.00,
    '2020-01-15',
    '2023-08-31',
    'Ile-de-France',
    'Realisation du lot Genie Civil n°2 pour le prolongement de la ligne B du metro vers le nord. Creusement de 1 200 ml de tunnel en methode conventionnelle (NATM) dans les marnes et calcaires du Lutetien. Realisation de 2 stations souterraines en parois moulees avec radier ancre et voute en beton projete fibre.',
    '["ISO 9001:2015", "ISO 14001:2015", "MASE", "Qualibat 2112"]'::jsonb,
    '{"longueur_tunnel_ml": 1200, "nombre_stations": 2, "profondeur_max_m": 28, "volume_beton_m3": 25000, "tonnage_acier_t": 3500, "duree_mois": 43, "effectif_moyen": 80, "taux_sinistralite": 0.0}'::jsonb,
    true
),

-- REF-2023-007: Batiment industriel — Entrepot logistique
(
    gen_random_uuid(),
    'REF-2023-007',
    'Construction plateforme logistique Amazon - Saint-Quentin-Fallavier',
    'Prologis France',
    'Batiment industriel - Entrepot logistique XXL',
    22000000.00,
    '2022-02-01',
    '2023-07-31',
    'Auvergne-Rhone-Alpes',
    'Construction d''une plateforme logistique de 65 000 m2 au sol avec mezzanine partielle, hauteur libre 12 m sous ferme. Structure charpente metallique sur fondations superficielles, dallage industriel fibre haute performance. Integration d''un systeme photovoltaique en toiture (2 MWc), certification BREEAM Very Good.',
    '["ISO 9001:2015", "ISO 14001:2015", "CSTB Avis Technique", "RGE"]'::jsonb,
    '{"surface_au_sol_m2": 65000, "hauteur_libre_m": 12, "surface_mezzanine_m2": 8000, "tonnage_charpente_t": 1800, "puissance_pv_kwc": 2000, "duree_mois": 17, "effectif_moyen": 55}'::jsonb,
    true
),

-- REF-2023-008: Gros oeuvre — Equipement public
(
    gen_random_uuid(),
    'REF-2023-008',
    'Construction du gymnase olympique intercommunal de Creteil',
    'Communaute d''Agglomeration du Val-de-Bievre',
    'Gros oeuvre - Equipement sportif',
    9800000.00,
    '2021-09-01',
    '2023-04-30',
    'Ile-de-France',
    'Construction d''un gymnase multisports aux normes olympiques avec tribune de 2 500 places. Structure en beton arme et charpente bois lamelle-colle pour la couverture du hall principal (portee libre 45 m). Equipements techniques specifiques : plancher sportif homologue FIBA, eclairage LED 1500 lux, acoustique maitrisee.',
    '["ISO 9001:2015", "NF Habitat", "Qualibat 2112", "CSTB Avis Technique"]'::jsonb,
    '{"surface_plancher_m2": 5200, "capacite_tribune": 2500, "portee_charpente_m": 45, "duree_mois": 19, "effectif_moyen": 40, "satisfaction_client": 4.6}'::jsonb,
    true
),

-- REF-2023-009: Voirie — Route departementale
(
    gen_random_uuid(),
    'REF-2023-009',
    'Deviation de la RD1075 - Contournement de Voiron',
    'Conseil Departemental de l''Isere',
    'Voirie - Route neuve et ouvrages d''art',
    15500000.00,
    '2021-04-01',
    '2023-11-15',
    'Auvergne-Rhone-Alpes',
    'Realisation de la deviation de la RD1075 sur 5,8 km en 2x2 voies avec echangeur denicele. Comprend 3 ouvrages d''art courants (PI et PS), un mur de soutenement en terre armee de 280 ml, et la mise en oeuvre de 120 000 m3 de terrassements en deblai/remblai avec traitement des sols en place a la chaux.',
    '["ISO 9001:2015", "ISO 14001:2015", "MASE", "Qualibat 1311"]'::jsonb,
    '{"lineaire_route_km": 5.8, "nombre_ouvrages_art": 3, "volume_terrassement_m3": 120000, "surface_chaussee_m2": 58000, "duree_mois": 31, "effectif_moyen": 50}'::jsonb,
    true
),

-- REF-2023-010: Batiment industriel — Usine
(
    gen_random_uuid(),
    'REF-2023-010',
    'Extension usine de production Sanofi - Site de Vitry-sur-Seine',
    'Sanofi-Aventis France',
    'Batiment industriel - Extension site pharmaceutique',
    28000000.00,
    '2020-11-01',
    '2023-05-31',
    'Ile-de-France',
    'Extension du site de production pharmaceutique Sanofi comprenant un batiment de production (3 200 m2) et un batiment utilites (1 800 m2). Construction en environnement ATEX avec salles blanches ISO 7 et ISO 8. Travaux realises en site occupe avec maintien de l''activite de production, protocole de securite renforce ICPE Seveso seuil haut.',
    '["ISO 9001:2015", "ISO 14001:2015", "MASE", "CSTB Avis Technique", "Qualibat 2112"]'::jsonb,
    '{"surface_production_m2": 3200, "surface_utilites_m2": 1800, "classe_salle_blanche": "ISO 7/8", "duree_mois": 30, "effectif_moyen": 60, "satisfaction_client": 4.9, "incidents_securite": 0}'::jsonb,
    true
);


-- ============================================================================
-- 2. HISTORICAL TENDERS — 15 past AOs (7 gagne, 5 perdu, 3 abandonne)
-- ============================================================================
INSERT INTO historical_tenders (
    id, ao_number, maitre_ouvrage, nature_travaux, montant_estime,
    montant_propose, resultat, raison_resultat, date_soumission,
    criteres_attribution, note_technique, note_prix, region, description,
    is_active
) VALUES

-- ===== GAGNES (7) =====

(
    gen_random_uuid(),
    'AO-HIS-2024-001',
    'Metropole du Grand Paris',
    'Gros oeuvre - Construction neuve logements collectifs',
    9500000.00,
    9150000.00,
    'gagne',
    'Meilleure offre economiquement avantageuse. Note technique excellente grace aux references similaires (REF-2023-001) et a la proposition d''une variante beton bas carbone CEM III/B ayant seduit le jury.',
    '2024-03-15',
    '{"prix": 40, "technique": 50, "delai": 10}'::jsonb,
    85.5,
    88.2,
    'Ile-de-France',
    'Construction de 65 logements collectifs en accession sociale dans le cadre du programme ANRU de renouvellement urbain du quartier des Hautes-Noues a Villiers-sur-Marne. Batiments R+5 en beton arme avec facade a ossature bois et isolation biosourcee.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-002',
    'SNCF Reseau',
    'Genie civil - Ouvrage d''art ferroviaire',
    14200000.00,
    13800000.00,
    'gagne',
    'Selection sur la base de l''experience en ouvrages ferroviaires (REF-2023-002) et de la methodologie de travail sous circulation proposee, jugee la plus securisante par le maitre d''oeuvre.',
    '2024-05-22',
    '{"prix": 35, "technique": 55, "delai": 10}'::jsonb,
    91.0,
    82.5,
    'Auvergne-Rhone-Alpes',
    'Remplacement du pont-rail de la LGV Paris-Lyon au PK 287+450. Ouvrage en beton precontraint a 2 travees de 35 m, realise en pousse avec interruptions de trafic programmees de nuit.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-003',
    'Ville de Nantes',
    'Voirie et Reseaux Divers - Amenagement urbain',
    5800000.00,
    5600000.00,
    'gagne',
    'Offre retenue pour la qualite de la demarche environnementale (reemploi des materiaux de demolition, noues vegetalisees) et le planning optimise permettant de limiter la gene aux riverains.',
    '2024-07-10',
    '{"prix": 45, "technique": 40, "delai": 15}'::jsonb,
    78.0,
    90.5,
    'Pays de la Loire',
    'Reamenagement complet de l''avenue de la Gare sur 1 200 ml : creation de pistes cyclables, reprise des reseaux d''assainissement, plantation de 80 arbres et installation de mobilier urbain intelligent.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-004',
    'Bouygues Immobilier',
    'Gros oeuvre - Construction neuve tertiaire',
    32000000.00,
    30500000.00,
    'gagne',
    'Marche attribue sur la base de notre experience en IGH (REF-2023-003) et de la proposition d''un planning en flux tendu avec prefabrication partielle des voiles et predulles beton.',
    '2024-02-28',
    '{"prix": 50, "technique": 40, "delai": 10}'::jsonb,
    82.0,
    92.0,
    'Ile-de-France',
    'Construction d''un ensemble immobilier de bureaux "Green Park" a Issy-les-Moulineaux, comprenant 2 batiments R+12 et R+8, parking souterrain R-3, surface totale 22 000 m2 SHON. Certification HQE Exceptionnel et BREEAM Outstanding visees.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-005',
    'CHU de Bordeaux',
    'Rehabilitation - Renovation batiment hospitalier',
    7400000.00,
    7100000.00,
    'gagne',
    'Attribution grace a l''expertise en travaux en site occupe hospitalier et a la proposition d''un phasage permettant le maintien de l''activite medicale sans interruption de service.',
    '2024-09-05',
    '{"prix": 35, "technique": 55, "delai": 10}'::jsonb,
    89.0,
    84.0,
    'Nouvelle-Aquitaine',
    'Rehabilitation du batiment A du CHU Pellegrin : renforcement parasismique, mise aux normes incendie et accessibilite, remplacement des reseaux CVC et plomberie, travaux en site occupe.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-006',
    'Conseil Regional Auvergne-Rhone-Alpes',
    'Gros oeuvre - Construction neuve equipement scolaire',
    11000000.00,
    10600000.00,
    'gagne',
    'Meilleur rapport qualite-prix. La note technique a ete renforcee par la proposition d''utiliser du beton bas carbone et une charpente mixte bois-beton pour la halle sportive.',
    '2024-11-20',
    '{"prix": 40, "technique": 45, "delai": 15}'::jsonb,
    86.5,
    87.0,
    'Auvergne-Rhone-Alpes',
    'Construction d''un lycee professionnel de 900 eleves a Annecy comprenant batiment d''enseignement, ateliers techniques, demi-pension 600 places, gymnase type C et espaces exterieurs amenages.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-007',
    'Societe du Grand Paris',
    'Genie civil - Tunnel et gares souterraines',
    48000000.00,
    46500000.00,
    'gagne',
    'Selection pour l''expertise tunnel (REF-2023-006) et la proposition technique de traitement des venues d''eau par injection de resine polyurethane, superieure aux solutions concurrentes.',
    '2024-04-18',
    '{"prix": 30, "technique": 60, "delai": 10}'::jsonb,
    93.5,
    79.0,
    'Ile-de-France',
    'Lot T2C du Grand Paris Express - Ligne 15 Sud : realisation de 2,8 km de tunnel au tunnelier et d''une gare souterraine de 250 m de long a 35 m de profondeur dans les sables de Fontainebleau.',
    true
),

-- ===== PERDUS (5) =====

(
    gen_random_uuid(),
    'AO-HIS-2024-008',
    'Departement des Bouches-du-Rhone',
    'Voirie - Route departementale neuve',
    8900000.00,
    8700000.00,
    'perdu',
    'Offre classee 2eme. Le concurrent (Eiffage) a propose un prix inferieur de 8% grace a une carriere locale permettant de reduire les couts de transport des granulats. Notre note technique etait superieure mais le critere prix ponderait a 60%.',
    '2024-06-12',
    '{"prix": 60, "technique": 30, "delai": 10}'::jsonb,
    82.0,
    71.5,
    'Provence-Alpes-Cote d''Azur',
    'Deviation de la RD9 entre Salon-de-Provence et Pelissanne sur 3,2 km en 2x1 voie, comprenant 1 ouvrage d''art de franchissement et 2 giratoires.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-009',
    'Mairie de Paris',
    'Rehabilitation - Renovation equipement culturel',
    15500000.00,
    16200000.00,
    'perdu',
    'Offre jugee trop elevee par rapport au budget previsionnel du maitre d''ouvrage. Notre estimation integrait une marge de risque de 12% liee a la decouverte potentielle d''amiante dans les faux plafonds, non confirmee par le diagnostic initial.',
    '2024-08-30',
    '{"prix": 45, "technique": 45, "delai": 10}'::jsonb,
    80.5,
    65.0,
    'Ile-de-France',
    'Rehabilitation du Theatre de la Ville - Sarah Bernhardt : restauration des facades, mise aux normes techniques (scene, eclairage, SSI), creation d''un espace d''accueil en sous-sol.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-010',
    'Port Autonome de Marseille',
    'Genie civil - Ouvrage portuaire',
    21000000.00,
    22500000.00,
    'perdu',
    'Offre non retenue en raison de l''absence de references recentes en travaux maritimes et portuaires. Le candidat retenu (Bouygues TP) disposait de 3 references directement comparables realisees au cours des 5 dernieres annees.',
    '2024-10-15',
    '{"prix": 35, "technique": 55, "delai": 10}'::jsonb,
    68.0,
    72.0,
    'Provence-Alpes-Cote d''Azur',
    'Construction d''un nouveau quai en eau profonde (tirant d''eau -14 m) au terminal conteneurs de Fos-sur-Mer. Realisation de 350 ml de quai sur pieux fores et paroi moulee en beton arme.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-011',
    'Region Occitanie',
    'Gros oeuvre - Construction neuve equipement sportif',
    6200000.00,
    6500000.00,
    'perdu',
    'Notre offre technique a ete penalisee par un planning de 20 mois juge trop long par le maitre d''ouvrage qui souhaitait une livraison en 16 mois maximum. Le concurrent retenu (NGE) a propose un planning de 15 mois avec travail en 2x8.',
    '2025-01-08',
    '{"prix": 40, "technique": 40, "delai": 20}'::jsonb,
    76.0,
    78.5,
    'Occitanie',
    'Construction d''un complexe aquatique intercommunal a Montpellier comprenant bassin olympique 50 m, bassin ludique, espace bien-etre et tribunes 500 places.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-012',
    'Nexity',
    'Gros oeuvre - Construction neuve logements collectifs',
    7800000.00,
    8100000.00,
    'perdu',
    'Classement en 3eme position. Le critere prix dominant (55%) a penalise notre offre. Les deux premiers candidats (Demathieu Bard et Legendre) ont propose des prix 6 et 9% inferieurs grace a des equipes de production implantees localement.',
    '2025-02-14',
    '{"prix": 55, "technique": 35, "delai": 10}'::jsonb,
    81.0,
    68.0,
    'Bretagne',
    'Construction de 88 logements collectifs en VEFA a Rennes, quartier EuroRennes. Deux batiments R+8 et R+6 sur un niveau de parking souterrain commun.',
    true
),

-- ===== ABANDONNES (3) =====

(
    gen_random_uuid(),
    'AO-HIS-2024-013',
    'Commune de Saint-Denis (974)',
    'Gros oeuvre - Construction neuve equipement public',
    4500000.00,
    NULL,
    'abandonne',
    'Decision de non-soumission (No-Go) en comite de direction. Le projet se situe a La Reunion et nous ne disposons pas de moyens de production sur place. Les couts de mobilisation et de transport du materiel auraient rendu l''offre non competitive.',
    '2024-04-01',
    '{"prix": 50, "technique": 40, "delai": 10}'::jsonb,
    NULL,
    NULL,
    'La Reunion',
    'Construction d''une maison de quartier et d''une creche municipale a Saint-Denis de La Reunion. Batiment parasismique et paracyclonique en beton arme R+2.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-014',
    'Ministere des Armees',
    'Genie civil - Infrastructure militaire',
    35000000.00,
    NULL,
    'abandonne',
    'Abandon de la procedure par le maitre d''ouvrage pour raisons budgetaires. Le ministere a reporte le projet a 2027 suite aux arbitrages de la loi de programmation militaire. Notre offre etait en cours de finalisation au moment de l''annulation.',
    '2024-07-20',
    '{"prix": 30, "technique": 60, "delai": 10}'::jsonb,
    NULL,
    NULL,
    'Ile-de-France',
    'Rehabilitation et extension de la base aerienne 107 de Villacoublay. Construction d''un nouveau hangar de maintenance aeronautique et renovation des infrastructures piste.',
    true
),

(
    gen_random_uuid(),
    'AO-HIS-2024-015',
    'Societe Fonciere Lyonnaise',
    'Rehabilitation - Renovation lourde tertiaire',
    18000000.00,
    NULL,
    'abandonne',
    'Decision de non-soumission (No-Go) en raison d''un plan de charge deja sature sur la region Ile-de-France au T1 2025. Les equipes de production et d''encadrement necessaires etaient mobilisees sur les chantiers REF-2023-003 et AO-HIS-2024-004.',
    '2024-12-05',
    '{"prix": 45, "technique": 45, "delai": 10}'::jsonb,
    NULL,
    NULL,
    'Ile-de-France',
    'Renovation lourde de l''immeuble Edouard VII (12 500 m2) dans le 9eme arrondissement de Paris. Curage complet, restructuration des plateaux, reprise des facades haussmanniennes, mise aux normes RT2020 et accessibilite.',
    true
);


-- ============================================================================
-- 3. COMPANY CAPABILITIES — 20 entries (8 certifications, 6 materiel, 6 personnel)
-- ============================================================================
INSERT INTO company_capabilities (
    id, category, name, description, valid_until, region, availability, details, is_active
) VALUES

-- ===== CERTIFICATIONS (8) =====

(
    gen_random_uuid(),
    'certification',
    'ISO 9001:2015 - Management de la qualite',
    'Certification ISO 9001 version 2015 couvrant l''ensemble des activites de construction, rehabilitation et genie civil de l''entreprise France. Auditee annuellement par Bureau Veritas.',
    '2026-12-31',
    'National',
    'disponible',
    '{"organisme_certificateur": "Bureau Veritas Certification", "numero_certificat": "FR065432", "date_emission": "2023-01-15", "perimetre": "Construction, rehabilitation et genie civil", "derniere_audit": "2025-06-20", "resultat_audit": "Conforme sans ecart"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'certification',
    'ISO 14001:2015 - Management environnemental',
    'Certification ISO 14001 version 2015 pour le management environnemental des chantiers. Couvre la gestion des dechets, la maitrise des nuisances et la preservation de la biodiversite.',
    '2026-12-31',
    'National',
    'disponible',
    '{"organisme_certificateur": "AFNOR Certification", "numero_certificat": "ENV-2023-8871", "date_emission": "2023-03-01", "perimetre": "Toutes activites de construction", "derniere_audit": "2025-03-15", "resultat_audit": "Conforme avec 1 ecart mineur"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'certification',
    'Qualibat 2112 - Beton arme - Technicite superieure',
    'Qualification Qualibat 2112 pour les travaux de beton arme de technicite superieure, couvrant les ouvrages complexes tels que IGH, ouvrages d''art et structures precontraintes.',
    '2026-06-30',
    'National',
    'disponible',
    '{"organisme_certificateur": "Qualibat", "numero_certificat": "Q-2112-VCF-2023", "date_emission": "2023-07-01", "classe": "Technicite superieure", "montant_max_qualifie": 50000000, "derniere_audit": "2025-07-10"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'certification',
    'Qualibat 1311 - Travaux de voirie et d''amenagement urbain',
    'Qualification Qualibat 1311 pour les travaux de voirie, reseaux divers et amenagement urbain. Inclut la realisation de chaussees, trottoirs, reseaux d''assainissement et espaces publics.',
    '2026-06-30',
    'National',
    'disponible',
    '{"organisme_certificateur": "Qualibat", "numero_certificat": "Q-1311-VCF-2023", "date_emission": "2023-07-01", "classe": "Technicite courante", "montant_max_qualifie": 15000000, "derniere_audit": "2025-07-10"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'certification',
    'MASE - Manuel d''Amelioration Securite des Entreprises',
    'Certification MASE pour le management de la securite, sante et environnement sur les chantiers. Indispensable pour les marches industriels (sites Seveso, nucleaire, chimie).',
    '2027-03-31',
    'National',
    'disponible',
    '{"organisme_certificateur": "MASE National", "numero_certificat": "MASE-IDF-2024-156", "date_emission": "2024-04-01", "niveau": "3 ans", "taux_frequence": 8.2, "taux_gravite": 0.35, "derniere_audit": "2024-03-15"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'certification',
    'NF Habitat - Certification logement neuf',
    'Certification NF Habitat delivree par Cerqual (groupe Qualitel) pour la construction de logements neufs. Garantit la qualite globale du logement : acoustique, thermique, accessibilite, qualite de l''air.',
    '2026-09-30',
    'National',
    'disponible',
    '{"organisme_certificateur": "Cerqual Qualitel", "numero_certificat": "NF-HAB-2023-4521", "date_emission": "2023-10-01", "perimetre": "Logements collectifs neufs", "option": "HQE", "derniere_audit": "2025-09-25"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'certification',
    'CSTB - Avis Techniques et DTA',
    'Entreprise habilitee a mettre en oeuvre des procedes sous Avis Technique CSTB. Couvre les systemes d''isolation thermique par l''exterieur, les planchers collaborants et les facades ventilees.',
    '2026-12-31',
    'National',
    'disponible',
    '{"organisme_certificateur": "CSTB", "numero_habilitation": "CSTB-HAB-2023-0892", "date_emission": "2023-01-01", "procedes_couverts": ["ITE sous enduit", "Plancher collaborant Cofradal", "Facade ventilee Trespa"], "derniere_verification": "2025-06-01"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'certification',
    'RGE - Reconnu Garant de l''Environnement',
    'Qualification RGE pour les travaux de renovation energetique : isolation thermique, menuiseries exterieures, systemes de chauffage et ventilation. Permet aux clients de beneficier des aides CEE et MaPrimeRenov.',
    '2026-11-30',
    'National',
    'disponible',
    '{"organisme_certificateur": "Qualibat", "numero_certificat": "RGE-2023-VCF-7744", "date_emission": "2023-12-01", "domaines": ["Isolation murs", "Isolation toiture", "Menuiseries", "Ventilation"], "derniere_audit": "2025-11-20"}'::jsonb,
    true
),

-- ===== MATERIEL (6) =====

(
    gen_random_uuid(),
    'materiel',
    'Grue a tour Liebherr 280 EC-H 12 - Parc IDF',
    'Grue a tour a montage par elements Liebherr 280 EC-H 12 Litronic, fleche 70 m, capacite en bout de fleche 3,2 tonnes, hauteur sous crochet max 65 m. Ideale pour les chantiers de grande hauteur en zone urbaine.',
    NULL,
    'Ile-de-France',
    'disponible',
    '{"marque": "Liebherr", "modele": "280 EC-H 12 Litronic", "annee_mise_service": 2021, "capacite_max_t": 12, "portee_max_m": 70, "hauteur_max_m": 65, "numero_parc": "GR-IDF-012", "derniere_vgp": "2025-09-15", "localisation_actuelle": "Depot Gennevilliers"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'materiel',
    'Grue a tour Potain MDT 219 - Parc ARA',
    'Grue a tour a montage automatise Potain MDT 219, fleche 65 m, capacite en bout de fleche 2,4 tonnes. Montage rapide en 1 journee, adaptee aux chantiers de logements collectifs.',
    NULL,
    'Auvergne-Rhone-Alpes',
    'occupe',
    '{"marque": "Potain", "modele": "MDT 219", "annee_mise_service": 2022, "capacite_max_t": 10, "portee_max_m": 65, "hauteur_max_m": 56, "numero_parc": "GR-ARA-008", "derniere_vgp": "2025-11-01", "localisation_actuelle": "Chantier Annecy - Lycee professionnel", "date_liberation_prevue": "2026-06-30"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'materiel',
    'Nacelles articulees Haulotte HA26 RTJ Pro (x4)',
    'Parc de 4 nacelles articulees diesel Haulotte HA26 RTJ Pro. Hauteur de travail 26 m, deport horizontal 14 m, capacite nacelle 350 kg. Homologuees pour travail sur voie publique.',
    NULL,
    'National',
    'partiel',
    '{"marque": "Haulotte", "modele": "HA26 RTJ Pro", "quantite": 4, "disponibles": 2, "hauteur_travail_m": 26, "deport_m": 14, "capacite_kg": 350, "motorisation": "diesel", "derniere_vgp": "2025-08-20", "nacelles_disponibles": ["NAC-017", "NAC-019"], "nacelles_occupees": ["NAC-016 - Chantier Bordeaux", "NAC-018 - Chantier Lyon"]}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'materiel',
    'Parc engins de terrassement - Region PACA',
    'Parc complet d''engins de terrassement base en PACA comprenant pelles hydrauliques (Cat 320 et 330), chargeuses (Cat 950M), tombereaux articules (Volvo A30G) et compacteurs vibrants (Hamm 3411).',
    NULL,
    'Provence-Alpes-Cote d''Azur',
    'disponible',
    '{"composition": [{"type": "Pelle hydraulique", "marque": "Caterpillar", "modele": "320 GC", "quantite": 3}, {"type": "Pelle hydraulique", "marque": "Caterpillar", "modele": "330 GC", "quantite": 2}, {"type": "Chargeuse", "marque": "Caterpillar", "modele": "950M", "quantite": 2}, {"type": "Tombereau articule", "marque": "Volvo", "modele": "A30G", "quantite": 4}, {"type": "Compacteur", "marque": "Hamm", "modele": "3411", "quantite": 2}], "base": "Depot Vitrolles (13)", "derniere_vgp_globale": "2025-10-05"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'materiel',
    'Centrale a beton mobile Liebherr Mobilmix 2.5',
    'Centrale a beton mobile Liebherr Mobilmix 2.5 d''une capacite de production de 100 m3/h. Montage en 3 jours, ideale pour les chantiers de genie civil isoles ou a fort volume de beton.',
    NULL,
    'National',
    'disponible',
    '{"marque": "Liebherr", "modele": "Mobilmix 2.5", "capacite_m3_h": 100, "volume_malaxeur_l": 2500, "annee_mise_service": 2020, "numero_parc": "CB-NAT-003", "derniere_vgp": "2025-07-12", "localisation_actuelle": "Depot Gennevilliers", "silos_ciment": 2, "capacite_silo_t": 60}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'materiel',
    'Coffrage grimpant Doka SKE 100 Plus (2 jeux)',
    'Systeme de coffrage grimpant automatique Doka SKE 100 Plus pour voiles beton de grande hauteur. Deux jeux complets permettant le coffrage simultane de noyaux et voiles. Cadence de levee : 1 etage tous les 4 jours.',
    NULL,
    'Ile-de-France',
    'occupe',
    '{"marque": "Doka", "modele": "SKE 100 Plus", "quantite_jeux": 2, "hauteur_levee_m": 3.0, "cadence_jours_par_etage": 4, "numero_parc": ["COF-IDF-021", "COF-IDF-022"], "localisation_actuelle": "Chantier Issy-les-Moulineaux - Green Park", "date_liberation_prevue": "2026-09-30"}'::jsonb,
    true
),

-- ===== PERSONNEL (6) =====

(
    gen_random_uuid(),
    'personnel',
    'Equipe gros oeuvre N°1 - Ile-de-France',
    'Equipe de production gros oeuvre composee de 25 compagnons qualifies : 1 chef d''equipe, 4 coffreurs-bancheurs N4, 6 coffreurs N3, 8 ferrailleurs N3, 4 macons N3 et 2 grutiers. Experience moyenne de 12 ans dans le BTP.',
    NULL,
    'Ile-de-France',
    'occupe',
    '{"effectif_total": 25, "chef_equipe": "Bernard Dupont", "qualifications": {"N4": 5, "N3": 18, "N2": 2}, "specialites": ["coffrage", "ferraillage", "maconnerie"], "habilitations": ["CACES R487", "AIPR", "SST"], "chantier_actuel": "Green Park - Issy-les-Moulineaux", "date_liberation_prevue": "2026-08-15"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'personnel',
    'Equipe VRD - Nouvelle-Aquitaine',
    'Equipe specialisee en voirie et reseaux divers composee de 18 compagnons : 1 chef d''equipe, 3 conducteurs d''engins (CACES R482 cat A a F), 5 canalisateurs, 4 ouvriers TP qualifies, 3 poseurs de bordures et 2 applicateurs d''enrobes.',
    NULL,
    'Nouvelle-Aquitaine',
    'disponible',
    '{"effectif_total": 18, "chef_equipe": "Philippe Moreau", "qualifications": {"N4": 2, "N3": 12, "N2": 4}, "specialites": ["voirie", "assainissement", "reseaux secs", "enrobes"], "habilitations": ["CACES R482", "AIPR", "H0B0", "SST"], "base": "Agence Bordeaux-Merignac"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'personnel',
    'Equipe electricite courants forts/faibles - PACA',
    'Equipe d''electriciens composee de 12 compagnons habilites : 1 chef d''equipe, 4 electriciens courants forts (habilitation B2V-BR-BC), 4 electriciens courants faibles (certification fibre optique), 2 techniciens CVC et 1 automaticien.',
    NULL,
    'Provence-Alpes-Cote d''Azur',
    'partiel',
    '{"effectif_total": 12, "disponibles": 6, "chef_equipe": "Karim Benali", "qualifications": {"N4": 3, "N3": 7, "N2": 2}, "specialites": ["courants forts", "courants faibles", "fibre optique", "CVC", "GTB/GTC"], "habilitations": ["B2V", "BR", "BC", "H2V", "AIPR", "CACES R486"], "partiel_raison": "6 compagnons mobilises sur chantier Marseille Hotel des Postes"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'personnel',
    'Conduite de travaux - Pool national',
    'Pool de 8 conducteurs de travaux et 4 directeurs de travaux disponibles pour affectation sur les grands projets. Profils experimentes (10 a 25 ans d''experience) couvrant toutes les specialites : gros oeuvre, genie civil, rehabilitation, batiment industriel.',
    NULL,
    'National',
    'partiel',
    '{"effectif_total": 12, "disponibles": 5, "directeurs_travaux": [{"nom": "Marc Lefevre", "experience_ans": 25, "specialite": "Genie civil", "disponible": true}, {"nom": "Isabelle Martin", "experience_ans": 20, "specialite": "Rehabilitation", "disponible": false}, {"nom": "Thierry Rousseau", "experience_ans": 22, "specialite": "Batiment industriel", "disponible": true}, {"nom": "Nathalie Chen", "experience_ans": 18, "specialite": "Gros oeuvre IGH", "disponible": false}], "conducteurs_disponibles": 3, "base": "Siege - Rueil-Malmaison"}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'personnel',
    'Bureau d''etudes structure - Ile-de-France',
    'Bureau d''etudes techniques interne specialise en calcul de structures beton arme et precontraint. Equipe de 10 ingenieurs et techniciens maitrisant les logiciels Robot Structural Analysis, SCIA Engineer et les codes Eurocodes (EC2, EC7, EC8).',
    NULL,
    'Ile-de-France',
    'partiel',
    '{"effectif_total": 10, "disponibles": 4, "responsable": "Dr. Jean-Pierre Nguyen", "competences_logiciels": ["Robot Structural Analysis", "SCIA Engineer", "Advance Design", "GRAITEC"], "normes_maitrisees": ["Eurocode 2", "Eurocode 7", "Eurocode 8", "NF EN 206", "NF P94-261"], "projets_en_cours": ["Green Park Issy", "Lycee Annecy"], "capacite_notes_calcul_par_mois": 15}'::jsonb,
    true
),

(
    gen_random_uuid(),
    'personnel',
    'Bureau d''etudes methodes et planification - National',
    'Equipe de 6 ingenieurs methodes et planificateurs specialises dans l''optimisation des modes constructifs, le choix des materiels et l''elaboration des plannings TCE. Maitrise de Primavera P6, MS Project et Tilos.',
    NULL,
    'National',
    'disponible',
    '{"effectif_total": 6, "responsable": "Sophie Garnier", "competences_logiciels": ["Primavera P6", "MS Project", "Tilos", "BIM 360", "Navisworks"], "specialites": ["Phasage et planning TCE", "Etudes de prix", "Methodes constructives", "BIM 4D/5D", "Installation de chantier"], "capacite_etudes_simultanees": 4}'::jsonb,
    true
);


-- ============================================================================
-- 4. PENDING TENDERS — 5 AOs for live demo
-- ============================================================================
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES

-- AO-2026-0042: Marche public, 80 logements Nanterre
(
    gen_random_uuid(),
    'ENT-IDF',
    'AO-2026-0042',
    'Marche public',
    'tenders/ao_2026_0042.pdf',
    'pending',
    '{
        "titre": "Construction de 80 logements collectifs - Programme ANRU Nanterre",
        "maitre_ouvrage": "Etablissement Public Territorial Paris Ouest La Defense",
        "maitre_oeuvre": "Atelier d''Architecture Chartier-Dalix",
        "nature_travaux": "Gros oeuvre - Construction neuve logements collectifs",
        "montant_estime": 8000000,
        "delai_execution_mois": 24,
        "date_limite_remise": "2026-03-15",
        "criteres_attribution": {"prix": 40, "technique": 50, "delai": 10},
        "lots": ["Lot 1 - Gros oeuvre", "Lot 2 - Charpente couverture", "Lot 3 - Facades"],
        "region": "Ile-de-France",
        "commune": "Nanterre",
        "description": "Construction de 80 logements collectifs dont 30% en logement social dans le cadre du programme ANRU du quartier du Parc Sud a Nanterre. Deux batiments R+6 et R+4 sur parking souterrain commun. Certification NF Habitat HQE et label E+C- niveau E3C1.",
        "exigences_specifiques": ["NF Habitat HQE", "Label E+C-", "Beton bas carbone CEM III", "Certification MASE non requise"],
        "source": "plateforme BOAMP"
    }'::jsonb,
    NOW() - INTERVAL '2 days'
),

-- AO-2026-0043: Marche prive, rehabilitation bureaux La Defense
(
    gen_random_uuid(),
    'ENT-IDF',
    'AO-2026-0043',
    'Marche prive',
    'tenders/ao_2026_0043.pdf',
    'pending',
    '{
        "titre": "Rehabilitation de l''immeuble de bureaux Tour Sequoia - La Defense",
        "maitre_ouvrage": "Gecina",
        "maitre_oeuvre": "Agence d''Architecture Jean-Paul Viguier",
        "nature_travaux": "Rehabilitation - Renovation lourde tertiaire",
        "montant_estime": 3500000,
        "delai_execution_mois": 10,
        "date_limite_remise": "2026-03-28",
        "criteres_attribution": {"prix": 45, "technique": 45, "delai": 10},
        "lots": ["Lot unique - TCE hors CVC"],
        "region": "Ile-de-France",
        "commune": "Courbevoie - La Defense",
        "description": "Rehabilitation des niveaux 3 a 8 de la Tour Sequoia (6 plateaux de 800 m2). Curage complet, reprise des faux planchers et faux plafonds, remplacement du reseau electrique courants forts/faibles, peintures et revetements de sol. Travaux en site partiellement occupe.",
        "exigences_specifiques": ["Travaux en site occupe", "Horaires decales 6h-22h", "Certification ISO 14001 exigee"],
        "source": "consultation directe"
    }'::jsonb,
    NOW() - INTERVAL '1 day'
),

-- AO-2026-0044: Conception-realisation, gymnase Villeurbanne
(
    gen_random_uuid(),
    'ENT-ARA',
    'AO-2026-0044',
    'Conception-realisation',
    'tenders/ao_2026_0044.pdf',
    'pending',
    '{
        "titre": "Conception-realisation du gymnase municipal Nelson Mandela - Villeurbanne",
        "maitre_ouvrage": "Ville de Villeurbanne",
        "maitre_oeuvre": "A definir (equipe de conception integree)",
        "nature_travaux": "Gros oeuvre - Equipement sportif",
        "montant_estime": 5000000,
        "delai_execution_mois": 18,
        "date_limite_remise": "2026-04-10",
        "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10},
        "lots": ["Lot unique - Conception-realisation"],
        "region": "Auvergne-Rhone-Alpes",
        "commune": "Villeurbanne",
        "description": "Conception et realisation d''un gymnase multisports de type B avec tribune 500 places, salle de danse, dojo et locaux associatifs. Structure mixte beton/bois lamelle-colle. Objectif RE2020 avec production photovoltaique en toiture et recuperation des eaux de pluie.",
        "exigences_specifiques": ["Equipe de conception integree obligatoire", "RE2020 anticipee", "Qualibat 2112 exigee", "NF Habitat non requis"],
        "source": "plateforme PLACE marches publics"
    }'::jsonb,
    NOW() - INTERVAL '3 days'
),

-- AO-2026-0045: Marche public, ouvrage d'art A86
(
    gen_random_uuid(),
    'ENT-IDF',
    'AO-2026-0045',
    'Marche public',
    'tenders/ao_2026_0045.pdf',
    'pending',
    '{
        "titre": "Remplacement de l''ouvrage d''art n47 - Echangeur A86/A4 Joinville-le-Pont",
        "maitre_ouvrage": "Direction Interdepartementale des Routes d''Ile-de-France (DiRIF)",
        "maitre_oeuvre": "Setec TPI",
        "nature_travaux": "Genie civil - Ouvrage d''art courant",
        "montant_estime": 12000000,
        "delai_execution_mois": 28,
        "date_limite_remise": "2026-04-25",
        "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10},
        "lots": ["Lot unique - Demolition et reconstruction OA"],
        "region": "Ile-de-France",
        "commune": "Joinville-le-Pont",
        "description": "Demolition et reconstruction de l''ouvrage d''art n47 (pont-dalle en beton precontraint, 3 travees, longueur 85 m) a l''echangeur A86/A4. Travaux sous circulation avec basculements de voies et coupures de nuit. Fondations profondes sur pieux fores de 18 m dans les alluvions de la Marne.",
        "exigences_specifiques": ["MASE obligatoire", "Qualibat 2112 exigee", "Plan de signalisation temporaire", "Travaux de nuit", "Proximite Marne - risque inondation"],
        "source": "plateforme PLACE marches publics"
    }'::jsonb,
    NOW() - INTERVAL '5 days'
),

-- AO-2026-0046: Marche public, amenagement ZAC Bordeaux Euratlantique
(
    gen_random_uuid(),
    'ENT-NAQ',
    'AO-2026-0046',
    'Marche public',
    'tenders/ao_2026_0046.pdf',
    'pending',
    '{
        "titre": "Amenagement de la ZAC Bordeaux Euratlantique - Secteur Armagnac Phase 3",
        "maitre_ouvrage": "EPA Bordeaux Euratlantique",
        "maitre_oeuvre": "Ingenierie Artelia / Paysagiste Michel Desvigne",
        "nature_travaux": "Voirie et Reseaux Divers - Amenagement urbain",
        "montant_estime": 7000000,
        "delai_execution_mois": 16,
        "date_limite_remise": "2026-05-05",
        "criteres_attribution": {"prix": 45, "technique": 40, "delai": 15},
        "lots": ["Lot 1 - Voirie et assainissement", "Lot 2 - Reseaux secs et eclairage public", "Lot 3 - Espaces verts et mobilier urbain"],
        "region": "Nouvelle-Aquitaine",
        "commune": "Bordeaux",
        "description": "Amenagement VRD de la phase 3 du secteur Armagnac (8,5 ha) : voiries structurantes et de desserte, reseaux d''assainissement separatifs avec gestion integree des eaux pluviales (noues, jardins de pluie), reseaux secs (electricite HTA/BT, telecoms FTTH, gaz), eclairage public LED intelligent, espaces verts et promenade paysagere le long de la Garonne.",
        "exigences_specifiques": ["ISO 14001 exigee", "Qualibat 1311 exigee", "Reemploi des materiaux de deconstruction > 50%", "Clause d''insertion sociale 10% des heures"],
        "source": "plateforme BOAMP"
    }'::jsonb,
    NOW()
);


-- Extra tenders: AO-2026-0047 to 0051 (from edge cases)
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES
(gen_random_uuid(), 'ENT-PACA', 'AO-2026-0047', 'Marche public', 'tenders/ao_2026_0047.pdf', 'pending', '{"titre": "Construction du quai de croisiere du Port de Toulon", "maitre_ouvrage": "Port Autonome de Toulon", "maitre_oeuvre": "Egis Ports", "nature_travaux": "Genie civil maritime - Ouvrage portuaire", "montant_estime": 25000000, "delai_execution_mois": 30, "date_limite_remise": "2026-04-15", "criteres_attribution": {"prix": 30, "technique": 60, "delai": 10}, "lots": ["Lot unique - Genie civil maritime"], "region": "Provence-Alpes-Cote d Azur", "commune": "Toulon", "description": "Construction d un nouveau quai de croisiere en eau profonde de 400 ml avec terre-plein sur pieux fores en milieu marin.", "exigences_specifiques": ["Experience travaux maritimes exigee", "Plongeurs certifies classe II-B", "MASE obligatoire"], "source": "plateforme PLACE marches publics"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-DROM', 'AO-2026-0048', 'Marche public', 'tenders/ao_2026_0048.pdf', 'pending', '{"titre": "Construction ecole primaire Paul Eluard - Saint-Pierre de la Reunion", "maitre_ouvrage": "Commune de Saint-Pierre (974)", "maitre_oeuvre": "Cabinet Bourbon Architectes", "nature_travaux": "Gros oeuvre - Construction neuve equipement scolaire", "montant_estime": 3200000, "delai_execution_mois": 14, "date_limite_remise": "2026-03-20", "criteres_attribution": {"prix": 55, "technique": 35, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre", "Lot 2 - Charpente metallique"], "region": "La Reunion", "commune": "Saint-Pierre", "description": "Construction d une ecole primaire de 12 classes avec cantine et preau. Structure paracyclonique et parasismique.", "exigences_specifiques": ["Normes paracycloniques NV65", "Normes parasismiques PS92 zone 5", "Implantation locale obligatoire"], "source": "plateforme BOAMP DOM-TOM"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-NAQ', 'AO-2026-0049', 'Marche public', 'tenders/ao_2026_0049.pdf', 'pending', '{"titre": "Confortement radier et enceinte de confinement - CNPE du Blayais", "maitre_ouvrage": "EDF - Division Production Nucleaire", "maitre_oeuvre": "Assystem Nuclear", "nature_travaux": "Genie civil nucleaire - Confortement structures", "montant_estime": 18000000, "delai_execution_mois": 36, "date_limite_remise": "2026-05-30", "criteres_attribution": {"prix": 25, "technique": 65, "delai": 10}, "lots": ["Lot unique - Genie civil confortement"], "region": "Nouvelle-Aquitaine", "commune": "Braud-et-Saint-Louis", "description": "Confortement du radier et de l enceinte de confinement du reacteur n2 du CNPE du Blayais dans le cadre du Grand Carenage.", "exigences_specifiques": ["Habilitation nucleaire PR1-CC", "Qualite nucleaire RCC-G", "MASE exige"], "source": "consultation EDF"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-ARA', 'AO-2026-0050', 'Marche public', 'tenders/ao_2026_0050.pdf', 'pending', '{"titre": "Construction de 95 logements collectifs - ZAC des Girondins Lyon 7eme", "maitre_ouvrage": "Lyon Metropole Habitat", "maitre_oeuvre": "Agence Tectoniques Architectes", "nature_travaux": "Gros oeuvre - Construction neuve logements collectifs", "montant_estime": 11500000, "delai_execution_mois": 22, "date_limite_remise": "2026-04-20", "criteres_attribution": {"prix": 40, "technique": 50, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre et VRD", "Lot 2 - Enveloppe"], "region": "Auvergne-Rhone-Alpes", "commune": "Lyon", "description": "Construction de 95 logements collectifs en 2 batiments R+7 et R+5 avec commerces en RDC et parking souterrain R-2.", "exigences_specifiques": ["NF Habitat HQE", "Qualibat 2112 exigee", "ISO 14001 souhaitee"], "source": "plateforme PLACE marches publics"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-IDF', 'AO-2026-0051', 'Marche prive', 'tenders/ao_2026_0051.pdf', 'pending', '{"titre": "Construction data center hyperscale - Campus digital de Lisses", "maitre_ouvrage": "Equinix France", "maitre_oeuvre": "ADP Ingenierie", "nature_travaux": "Batiment industriel - Data center haute densite", "montant_estime": 42000000, "delai_execution_mois": 20, "date_limite_remise": "2026-05-15", "criteres_attribution": {"prix": 50, "technique": 40, "delai": 10}, "lots": ["Lot unique - Gros oeuvre et enveloppe"], "region": "Ile-de-France", "commune": "Lisses", "description": "Construction d un data center hyperscale de 8 000 m2 IT avec puissance electrique de 32 MW.", "exigences_specifiques": ["Qualibat 2112", "ISO 9001 et 14001", "Planning agressif 20 mois"], "source": "consultation directe Equinix"}'::jsonb, NOW());

-- Additional 20 tenders: AO-2026-0052 to 0071
INSERT INTO tenders (
    id, entity_id, tender_number, tender_type, document_path, status,
    metadata, created_at
) VALUES
(gen_random_uuid(), 'ENT-HDF', 'AO-2026-0052', 'Marche public', 'tenders/ao_2026_0052.pdf', 'pending', '{"titre": "Construction college 600 eleves - Tourcoing", "maitre_ouvrage": "Departement du Nord", "nature_travaux": "Gros oeuvre - Equipement scolaire", "montant_estime": 9500000, "delai_execution_mois": 20, "date_limite_remise": "2026-04-30", "criteres_attribution": {"prix": 40, "technique": 50, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre", "Lot 2 - CVC"], "region": "Hauts-de-France", "commune": "Tourcoing", "description": "Construction d un college de 600 eleves avec demi-pension, gymnase et espaces exterieurs.", "exigences_specifiques": ["RE2020", "Qualibat 2112"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-OCC', 'AO-2026-0053', 'Marche public', 'tenders/ao_2026_0053.pdf', 'pending', '{"titre": "Amenagement place de la Comedie - Montpellier", "maitre_ouvrage": "Montpellier Mediterranee Metropole", "nature_travaux": "Voirie et Reseaux Divers - Amenagement urbain", "montant_estime": 4800000, "delai_execution_mois": 12, "date_limite_remise": "2026-05-10", "criteres_attribution": {"prix": 45, "technique": 40, "delai": 15}, "lots": ["Lot 1 - Voirie", "Lot 2 - Reseaux"], "region": "Occitanie", "commune": "Montpellier", "description": "Reamenagement de la place de la Comedie avec pietonisation et reprise des reseaux.", "exigences_specifiques": ["ISO 14001", "Qualibat 1311"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-BRE', 'AO-2026-0054', 'Marche prive', 'tenders/ao_2026_0054.pdf', 'pending', '{"titre": "Extension usine agroalimentaire Fleury Michon - Pouzauges", "maitre_ouvrage": "Fleury Michon SA", "nature_travaux": "Batiment industriel - Extension site agroalimentaire", "montant_estime": 15000000, "delai_execution_mois": 16, "date_limite_remise": "2026-04-25", "criteres_attribution": {"prix": 50, "technique": 40, "delai": 10}, "lots": ["Lot unique - Gros oeuvre et enveloppe"], "region": "Pays de la Loire", "commune": "Pouzauges", "description": "Extension de 5000 m2 avec chambres froides et zone de production.", "exigences_specifiques": ["MASE exige", "ISO 22000 souhaitee"], "source": "consultation directe"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-GE', 'AO-2026-0055', 'Marche public', 'tenders/ao_2026_0055.pdf', 'pending', '{"titre": "Construction passerelle pietonne sur l Ill - Strasbourg", "maitre_ouvrage": "Eurometropole de Strasbourg", "nature_travaux": "Genie civil - Ouvrage d art", "montant_estime": 6500000, "delai_execution_mois": 14, "date_limite_remise": "2026-05-20", "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10}, "lots": ["Lot unique - Ouvrage d art"], "region": "Grand Est", "commune": "Strasbourg", "description": "Passerelle pietonne et cyclable de 120 m en structure mixte acier-beton.", "exigences_specifiques": ["Qualibat 2112", "Travaux en site aquatique"], "source": "plateforme PLACE marches publics"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-IDF', 'AO-2026-0056', 'Accord-cadre', 'tenders/ao_2026_0056.pdf', 'pending', '{"titre": "Accord-cadre maintenance ouvrages d art - DIRIF", "maitre_ouvrage": "Direction Interdepartementale des Routes IDF", "nature_travaux": "Genie civil - Maintenance ouvrages d art", "montant_estime": 8000000, "delai_execution_mois": 48, "date_limite_remise": "2026-06-01", "criteres_attribution": {"prix": 40, "technique": 50, "delai": 10}, "lots": ["Lot 1 - Nord IDF", "Lot 2 - Sud IDF"], "region": "Ile-de-France", "commune": "Paris", "description": "Accord-cadre 4 ans pour la maintenance et reparation des ouvrages d art du reseau routier national en IDF.", "exigences_specifiques": ["MASE obligatoire", "Qualibat 2112", "Astreinte 24h"], "source": "plateforme PLACE marches publics"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-PACA', 'AO-2026-0057', 'Marche public', 'tenders/ao_2026_0057.pdf', 'pending', '{"titre": "Construction EHPAD 120 lits - Aix-en-Provence", "maitre_ouvrage": "Centre Hospitalier du Pays d Aix", "nature_travaux": "Gros oeuvre - Equipement de sante", "montant_estime": 12000000, "delai_execution_mois": 22, "date_limite_remise": "2026-05-25", "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre", "Lot 2 - Menuiseries", "Lot 3 - CVC"], "region": "Provence-Alpes-Cote d Azur", "commune": "Aix-en-Provence", "description": "Construction d un EHPAD de 120 lits en R+3 avec jardins therapeutiques.", "exigences_specifiques": ["NF Habitat HQE", "Certification sante"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-ARA', 'AO-2026-0058', 'Conception-realisation', 'tenders/ao_2026_0058.pdf', 'pending', '{"titre": "Piscine olympique intercommunale - Chambery", "maitre_ouvrage": "Grand Chambery Agglomeration", "nature_travaux": "Gros oeuvre - Equipement sportif aquatique", "montant_estime": 18500000, "delai_execution_mois": 26, "date_limite_remise": "2026-06-10", "criteres_attribution": {"prix": 30, "technique": 60, "delai": 10}, "lots": ["Lot unique - Conception-realisation"], "region": "Auvergne-Rhone-Alpes", "commune": "Chambery", "description": "Piscine olympique avec bassin 50m, bassin ludique et espace bien-etre.", "exigences_specifiques": ["Conception integree", "RE2020", "Qualibat 2112"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-NAQ', 'AO-2026-0059', 'Marche public', 'tenders/ao_2026_0059.pdf', 'pending', '{"titre": "Tramway ligne D - Section Bordeaux Lac", "maitre_ouvrage": "Bordeaux Metropole Transports", "nature_travaux": "Genie civil - Infrastructure tramway", "montant_estime": 35000000, "delai_execution_mois": 30, "date_limite_remise": "2026-06-30", "criteres_attribution": {"prix": 30, "technique": 60, "delai": 10}, "lots": ["Lot 1 - Plateforme et voirie", "Lot 2 - Ouvrages d art"], "region": "Nouvelle-Aquitaine", "commune": "Bordeaux", "description": "Construction de 3.5 km de plateforme tramway avec 4 stations et 2 ouvrages d art.", "exigences_specifiques": ["MASE obligatoire", "ISO 14001", "Experience tramway exigee"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-HDF', 'AO-2026-0060', 'Marche public', 'tenders/ao_2026_0060.pdf', 'pending', '{"titre": "Rehabilitation caserne Vauban - Lille", "maitre_ouvrage": "Ville de Lille", "nature_travaux": "Rehabilitation - Batiment patrimonial", "montant_estime": 7200000, "delai_execution_mois": 18, "date_limite_remise": "2026-05-15", "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre et structure", "Lot 2 - Menuiseries et facades"], "region": "Hauts-de-France", "commune": "Lille", "description": "Rehabilitation de la caserne Vauban pour creer un espace culturel et associatif.", "exigences_specifiques": ["ABF - Architecte des Batiments de France", "Qualibat 2112"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-IDF', 'AO-2026-0061', 'Marche prive', 'tenders/ao_2026_0061.pdf', 'pending', '{"titre": "Tour de logements R+25 - Ivry-sur-Seine", "maitre_ouvrage": "Altarea Cogedim", "nature_travaux": "Gros oeuvre - IGH logements", "montant_estime": 28000000, "delai_execution_mois": 30, "date_limite_remise": "2026-06-15", "criteres_attribution": {"prix": 45, "technique": 45, "delai": 10}, "lots": ["Lot unique - Gros oeuvre et structure"], "region": "Ile-de-France", "commune": "Ivry-sur-Seine", "description": "Tour de 180 logements R+25 avec parking R-3. Structure beton arme avec noyaux de contreventement.", "exigences_specifiques": ["Experience IGH exigee", "Qualibat 2112", "ISO 14001"], "source": "consultation directe"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-OCC', 'AO-2026-0062', 'Marche public', 'tenders/ao_2026_0062.pdf', 'pending', '{"titre": "Station d epuration 80 000 EH - Perpignan", "maitre_ouvrage": "Communaute Urbaine Perpignan Mediterranee", "nature_travaux": "Genie civil - Station d epuration", "montant_estime": 22000000, "delai_execution_mois": 24, "date_limite_remise": "2026-07-01", "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10}, "lots": ["Lot 1 - Genie civil", "Lot 2 - Equipements process"], "region": "Occitanie", "commune": "Perpignan", "description": "Construction d une station d epuration de 80 000 EH avec traitement biologique et desodorisation.", "exigences_specifiques": ["MASE exige", "ISO 14001", "Experience assainissement"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-BRE', 'AO-2026-0063', 'Marche public', 'tenders/ao_2026_0063.pdf', 'pending', '{"titre": "Construction residence etudiante 250 logements - Rennes", "maitre_ouvrage": "CROUS de Rennes", "nature_travaux": "Gros oeuvre - Construction neuve logements", "montant_estime": 8500000, "delai_execution_mois": 18, "date_limite_remise": "2026-05-30", "criteres_attribution": {"prix": 45, "technique": 45, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre", "Lot 2 - Enveloppe et menuiseries"], "region": "Bretagne", "commune": "Rennes", "description": "Residence etudiante de 250 studios et T2 en R+6 avec espaces communs et local velos.", "exigences_specifiques": ["RE2020", "NF Habitat", "Beton bas carbone"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-GE', 'AO-2026-0064', 'Marche public', 'tenders/ao_2026_0064.pdf', 'pending', '{"titre": "Contournement routier RD83 - Colmar", "maitre_ouvrage": "Collectivite europeenne d Alsace", "nature_travaux": "Voirie - Route neuve", "montant_estime": 14000000, "delai_execution_mois": 24, "date_limite_remise": "2026-06-20", "criteres_attribution": {"prix": 40, "technique": 45, "delai": 15}, "lots": ["Lot 1 - Terrassements et chaussees", "Lot 2 - Ouvrages d art"], "region": "Grand Est", "commune": "Colmar", "description": "Deviation de 4.2 km en 2x1 voie avec giratoire et passage inferieur.", "exigences_specifiques": ["MASE", "ISO 14001", "Qualibat 1311"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-PACA', 'AO-2026-0065', 'Marche prive', 'tenders/ao_2026_0065.pdf', 'pending', '{"titre": "Hotel 5 etoiles 200 chambres - Cannes Croisette", "maitre_ouvrage": "LVMH Hospitality", "nature_travaux": "Gros oeuvre - Hotellerie de luxe", "montant_estime": 38000000, "delai_execution_mois": 28, "date_limite_remise": "2026-07-15", "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10}, "lots": ["Lot unique - Gros oeuvre et structure"], "region": "Provence-Alpes-Cote d Azur", "commune": "Cannes", "description": "Construction d un hotel de luxe 200 chambres en R+8 avec spa et restaurant panoramique.", "exigences_specifiques": ["Qualibat 2112", "ISO 9001", "Experience hotellerie souhaitee"], "source": "consultation directe LVMH"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-ARA', 'AO-2026-0066', 'Marche public', 'tenders/ao_2026_0066.pdf', 'pending', '{"titre": "Parking silo 800 places - Gare Part-Dieu Lyon", "maitre_ouvrage": "SYTRAL Mobilites", "nature_travaux": "Gros oeuvre - Parking multi-niveaux", "montant_estime": 10000000, "delai_execution_mois": 16, "date_limite_remise": "2026-05-05", "criteres_attribution": {"prix": 50, "technique": 40, "delai": 10}, "lots": ["Lot unique - Gros oeuvre et VRD"], "region": "Auvergne-Rhone-Alpes", "commune": "Lyon", "description": "Parking silo de 800 places en R+6 en structure beton precontraint avec facade vegetalisee.", "exigences_specifiques": ["Qualibat 2112", "ISO 14001", "Facade vegetalisee"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-IDF', 'AO-2026-0067', 'Marche public', 'tenders/ao_2026_0067.pdf', 'pending', '{"titre": "Groupe scolaire 15 classes - Saclay", "maitre_ouvrage": "Etablissement Public Paris-Saclay", "nature_travaux": "Gros oeuvre - Equipement scolaire", "montant_estime": 7800000, "delai_execution_mois": 16, "date_limite_remise": "2026-04-28", "criteres_attribution": {"prix": 40, "technique": 50, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre", "Lot 2 - CVC Plomberie"], "region": "Ile-de-France", "commune": "Saclay", "description": "Groupe scolaire de 15 classes avec restaurant scolaire et gymnase de type C.", "exigences_specifiques": ["RE2020", "NF Habitat HQE", "Beton bas carbone"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-NAQ', 'AO-2026-0068', 'Marche public', 'tenders/ao_2026_0068.pdf', 'pending', '{"titre": "Centre aquatique intercommunal - Anglet", "maitre_ouvrage": "Communaute Pays Basque", "nature_travaux": "Gros oeuvre - Equipement sportif aquatique", "montant_estime": 16000000, "delai_execution_mois": 24, "date_limite_remise": "2026-06-05", "criteres_attribution": {"prix": 35, "technique": 55, "delai": 10}, "lots": ["Lot 1 - Gros oeuvre et bassins", "Lot 2 - CVC et traitement eau"], "region": "Nouvelle-Aquitaine", "commune": "Anglet", "description": "Centre aquatique avec bassin sportif 25m, bassin ludique et espace bien-etre.", "exigences_specifiques": ["Qualibat 2112", "Experience aquatique souhaitee"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-HDF', 'AO-2026-0069', 'Accord-cadre', 'tenders/ao_2026_0069.pdf', 'pending', '{"titre": "Accord-cadre renovation energetique lycees - Region HDF", "maitre_ouvrage": "Region Hauts-de-France", "nature_travaux": "Rehabilitation - Renovation energetique", "montant_estime": 20000000, "delai_execution_mois": 48, "date_limite_remise": "2026-07-10", "criteres_attribution": {"prix": 40, "technique": 45, "delai": 15}, "lots": ["Lot 1 - Somme Oise", "Lot 2 - Nord Pas-de-Calais"], "region": "Hauts-de-France", "commune": "Lille", "description": "Accord-cadre 4 ans pour la renovation energetique de 25 lycees.", "exigences_specifiques": ["RGE obligatoire", "ISO 14001", "Travaux en site occupe"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-OCC', 'AO-2026-0070', 'Marche public', 'tenders/ao_2026_0070.pdf', 'pending', '{"titre": "Pont hauban sur le Tarn - Millau", "maitre_ouvrage": "Departement de l Aveyron", "nature_travaux": "Genie civil - Ouvrage d art exceptionnel", "montant_estime": 25000000, "delai_execution_mois": 36, "date_limite_remise": "2026-08-01", "criteres_attribution": {"prix": 25, "technique": 65, "delai": 10}, "lots": ["Lot unique - Ouvrage d art"], "region": "Occitanie", "commune": "Millau", "description": "Pont hauban de 250 m de portee principale avec pylone de 80 m de hauteur.", "exigences_specifiques": ["Qualibat 2112", "Experience ouvrages exceptionnels", "MASE"], "source": "plateforme BOAMP"}'::jsonb, NOW()),
(gen_random_uuid(), 'ENT-GE', 'AO-2026-0071', 'Marche prive', 'tenders/ao_2026_0071.pdf', 'pending', '{"titre": "Centre logistique Amazon - Metz Actipole", "maitre_ouvrage": "Prologis France", "nature_travaux": "Batiment industriel - Entrepot logistique", "montant_estime": 19000000, "delai_execution_mois": 14, "date_limite_remise": "2026-05-28", "criteres_attribution": {"prix": 55, "technique": 35, "delai": 10}, "lots": ["Lot unique - Gros oeuvre et enveloppe"], "region": "Grand Est", "commune": "Metz", "description": "Centre logistique de 45 000 m2 avec mezzanine et quais de chargement.", "exigences_specifiques": ["Qualibat 2112", "ISO 14001", "Planning serre 14 mois"], "source": "consultation directe Prologis"}'::jsonb, NOW());

-- ============================================================================
-- CROSS-DOMAIN: Harmonized AO -> Claim Scenario
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

-- ============================================================================
-- BILINGUAL METADATA FOR TENDERS
-- ============================================================================
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of 80 collective housing units including 30% social housing as part of the ANRU program in the Parc Sud district of Nanterre.", "document_path_en": "tenders/ao_2026_0042_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0042';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Rehabilitation of floors 3 to 8 of the Sequoia Tower (6 floor plates of 800 sqm each). Complete stripping, replacement of raised floors and suspended ceilings.", "document_path_en": "tenders/ao_2026_0043_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0043';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Design and build of a type B multi-sport gymnasium with 500-seat grandstand, dance hall, dojo and community rooms.", "document_path_en": "tenders/ao_2026_0044_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0044';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Demolition and reconstruction of structure no. 47 (prestressed concrete slab bridge, 3 spans, 85 m length) at the A86/A4 interchange.", "document_path_en": "tenders/ao_2026_0045_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0045';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Roads and utilities development for phase 3 of the Armagnac sector (8.5 ha): main and service roads, separate stormwater drainage.", "document_path_en": "tenders/ao_2026_0046_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0046';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of a new deep-water cruise ship berth of 400 linear meters with fill platform on bored piles.", "document_path_en": "tenders/ao_2026_0047_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0047';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of a 12-classroom primary school with cafeteria and covered playground. Cyclone-resistant and earthquake-resistant structure.", "document_path_en": "tenders/ao_2026_0048_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0048';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Reinforcement of the base slab and containment vessel of reactor no. 2 at the Blayais nuclear power plant.", "document_path_en": "tenders/ao_2026_0049_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0049';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of 95 collective housing units in 2 buildings R+7 and R+5 with ground-floor retail and R-2 underground parking.", "document_path_en": "tenders/ao_2026_0050_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0050';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of an 8,000 sqm IT hyperscale data center with 32 MW electrical capacity.", "document_path_en": "tenders/ao_2026_0051_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0051';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of a 600-student secondary school with canteen, gymnasium and outdoor areas.", "document_path_en": "tenders/ao_2026_0052_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0052';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Redevelopment of the Place de la Comedie with pedestrianization and utility network overhaul.", "document_path_en": "tenders/ao_2026_0053_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0053';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "5,000 sqm extension with cold rooms and production area.", "document_path_en": "tenders/ao_2026_0054_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0054';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "120 m pedestrian and cycling bridge in mixed steel-concrete structure.", "document_path_en": "tenders/ao_2026_0055_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0055';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "4-year framework agreement for the maintenance and repair of civil engineering structures in Ile-de-France.", "document_path_en": "tenders/ao_2026_0056_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0056';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of a 120-bed nursing home (EHPAD) in R+3 with therapeutic gardens.", "document_path_en": "tenders/ao_2026_0057_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0057';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Olympic swimming pool with 50 m competition pool, leisure pool and wellness area.", "document_path_en": "tenders/ao_2026_0058_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0058';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of 3.5 km of tramway platform with 4 stations and 2 civil engineering structures.", "document_path_en": "tenders/ao_2026_0059_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0059';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Rehabilitation of the Vauban barracks to create a cultural and community center.", "document_path_en": "tenders/ao_2026_0060_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0060';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "180-unit residential tower R+25 with R-3 underground parking. Reinforced concrete structure.", "document_path_en": "tenders/ao_2026_0061_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0061';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of an 80,000 population-equivalent wastewater treatment plant with biological treatment.", "document_path_en": "tenders/ao_2026_0062_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0062';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "250-unit student residence of studios and one-bedroom apartments in R+6 with communal spaces.", "document_path_en": "tenders/ao_2026_0063_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0063';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "4.2 km bypass road in 2x1 lane configuration with roundabout and underpass.", "document_path_en": "tenders/ao_2026_0064_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0064';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of a 200-room luxury 5-star hotel in R+8 with spa and panoramic restaurant.", "document_path_en": "tenders/ao_2026_0065_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0065';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "800-space multi-storey car park in R+6 with prestressed concrete structure and green facade.", "document_path_en": "tenders/ao_2026_0066_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0066';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "15-classroom school complex with school cafeteria and type C gymnasium.", "document_path_en": "tenders/ao_2026_0067_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0067';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Aquatic center with 25 m competition pool, leisure pool and wellness area.", "document_path_en": "tenders/ao_2026_0068_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0068';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "4-year framework agreement for the energy renovation of 25 high schools.", "document_path_en": "tenders/ao_2026_0069_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0069';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Cable-stayed bridge with 250 m main span and 80 m high pylon.", "document_path_en": "tenders/ao_2026_0070_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0070';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "45,000 sqm logistics center with mezzanine and loading docks.", "document_path_en": "tenders/ao_2026_0071_en.pdf"}'::jsonb WHERE tender_number = 'AO-2026-0071';
UPDATE tenders SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"description_en": "Construction of a municipal sports complex.", "document_path_en": "tenders/ao-2025-idf-003-dce_en.pdf"}'::jsonb WHERE tender_number = 'AO-2025-IDF-003';

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

-- Bilingual metadata for tender decision
UPDATE tender_decisions SET metadata = '{"reasoning_en": "GO recommendation for the Cergy-Pontoise municipal sports complex tender. Entreprise Construction IDF has strong references in sports facilities (3 similar projects over 5 years), all required certifications (Qualibat 2111, ISO 14001), and internal resources are available. The 4.2M EUR amount is within our usual range. The historical success rate on this type of public contract in Ile-de-France is 42%. Points of attention: tight 18-month deadline and strong competition expected (Bouygues, Eiffage)."}'::jsonb
WHERE tender_id = (SELECT id FROM tenders WHERE tender_number = 'AO-2025-IDF-003');

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

-- Bilingual metadata for claim decision
UPDATE claim_decisions SET metadata = '{"reasoning_en": "MANUAL_REVIEW recommendation for claim CLM-ENT-001 (slab collapse, Cergy-Pontoise construction site). The estimated amount of 850,000 EUR is high and exceeds the automatic validation threshold. Contract CTR-ENT-RC-2024 covers material damage and collapses (TRC coverage). However, liability is complex: need to determine if the collapse was due to a design defect (engineering firm liability), an execution defect (contractor liability), or a material defect (supplier liability). Bureau Veritas inspection is ongoing. Favorable points: appropriate safety measures, no injuries, timely declaration."}'::jsonb
WHERE claim_id = (SELECT id FROM claims WHERE claim_number = 'CLM-ENT-001');

-- PII guardrails detections for the claim
INSERT INTO guardrails_detections (id, claim_id, detection_type, severity, action_taken, detected_at, metadata) VALUES
    (uuid_generate_v4(), 'f6a7b8c9-d0e1-2345-fabc-456789012345', 'EMAIL', 'medium', 'redacted', '2025-07-22 14:32:00+00',
     '{"field_name": "ocr_text", "source": "regex", "entity_type": "claim", "entity_id": "f6a7b8c9-d0e1-2345-fabc-456789012345"}'),
    (uuid_generate_v4(), 'f6a7b8c9-d0e1-2345-fabc-456789012345', 'PHONE_FR', 'medium', 'redacted', '2025-07-22 14:32:00+00',
     '{"field_name": "ocr_text", "source": "regex", "entity_type": "claim", "entity_id": "f6a7b8c9-d0e1-2345-fabc-456789012345"}'),
    (uuid_generate_v4(), 'f6a7b8c9-d0e1-2345-fabc-456789012345', 'DATE_FR', 'low', 'redacted', '2025-07-22 14:32:00+00',
     '{"field_name": "ocr_text", "source": "regex", "entity_type": "claim", "entity_id": "f6a7b8c9-d0e1-2345-fabc-456789012345"}');

-- ============================================================================
-- COURRIER & COLIS DOMAIN
-- ============================================================================
DELETE FROM reclamation_processing_logs;
DELETE FROM reclamation_decisions;
DELETE FROM reclamation_documents;
DELETE FROM reclamations;
DELETE FROM tracking_events;
DELETE FROM courrier_knowledge_base;

-- ============================================================================
-- RECLAMATIONS (30 entries)
-- ============================================================================

-- 1-10: status = 'completed' (with processed_at set)
INSERT INTO reclamations (id, numero_suivi, reclamation_number, reclamation_type, client_nom, client_email, client_telephone, description, valeur_declaree, document_path, status, submitted_at, processed_at, total_processing_time_ms, metadata, created_at, updated_at) VALUES
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e01', '6C198745632FR', 'RECL-2025-0001', 'colis_endommage', 'Jean-Pierre Dupont', 'jp.dupont@gmail.com', '06 12 34 56 78', 'Colis recu avec le carton completement ecrase. Le contenu (service a the en porcelaine) est brise en plusieurs morceaux.', 89.90, 'reclamations/reclamation_colis_endommage_001.pdf', 'completed', '2025-06-10 09:15:00', '2025-06-10 09:18:42', 222000, '{"source": "web", "browser": "Chrome", "description_en": "Package received with the box completely crushed. The contents (porcelain tea set) are broken into multiple pieces.", "document_path_en": "reclamations/reclamation_colis_endommage_001_en.pdf"}', '2025-06-10 09:15:00', '2025-06-10 09:18:42'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e02', '6C234567891FR', 'RECL-2025-0002', 'colis_perdu', 'Marie-Claire Lefebvre', 'mc.lefebvre@orange.fr', '07 23 45 67 89', 'Colis expedie le 2 juin, toujours pas recu. Le suivi indique un dernier scan au centre de tri de Roissy le 4 juin.', 245.00, 'reclamations/reclamation_colis_perdu_001.pdf', 'completed', '2025-06-12 14:30:00', '2025-06-12 14:35:12', 312000, '{"source": "phone", "operator_id": "OP-042", "description_en": "Package shipped on June 2nd, still not received. Tracking shows a last scan at Roissy sorting center on June 4th.", "document_path_en": "reclamations/reclamation_colis_perdu_001_en.pdf"}', '2025-06-12 14:30:00', '2025-06-12 14:35:12'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e03', '6C345678912FR', 'RECL-2025-0003', 'non_livre', 'Francois Martin', 'f.martin@free.fr', '06 34 56 78 90', 'Le livreur a laisse un avis de passage alors que j''etais present a mon domicile toute la journee. Aucune tentative de sonnette.', 32.50, 'reclamations/reclamation_non_livre_001.pdf', 'completed', '2025-06-15 10:45:00', '2025-06-15 10:48:30', 210000, '{"source": "web", "description_en": "The delivery person left a notice of passage while I was home all day. No doorbell attempt was made.", "document_path_en": "reclamations/reclamation_non_livre_001_en.pdf"}', '2025-06-15 10:45:00', '2025-06-15 10:48:30'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e04', '6C456789123FR', 'RECL-2025-0004', 'retard_livraison', 'Sophie Bernard', 'sophie.bernard@laposte.net', '06 45 67 89 01', 'Colis commande en Colissimo J+2 le 8 juin, toujours pas livre au 18 juin. Delai largement depasse pour un anniversaire.', 67.00, 'reclamations/reclamation_retard_livraison_001.pdf', 'completed', '2025-06-18 16:20:00', '2025-06-18 16:24:55', 295000, '{"source": "web", "priority": "high", "description_en": "Package ordered via Colissimo J+2 on June 8th, still not delivered by June 18th. Deadline far exceeded for a birthday.", "document_path_en": "reclamations/reclamation_retard_livraison_001_en.pdf"}', '2025-06-18 16:20:00', '2025-06-18 16:24:55'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e05', '6C567891234FR', 'RECL-2025-0005', 'vol_point_relais', 'Ahmed Benali', 'a.benali@hotmail.fr', '07 56 78 90 12', 'Mon colis a ete marque comme livre au point relais Tabac Presse du Marais, mais le commercant affirme ne jamais l''avoir recu.', 189.99, 'reclamations/reclamation_vol_point_relais_001.pdf', 'completed', '2025-06-20 11:00:00', '2025-06-20 11:05:20', 320000, '{"source": "web", "point_relais_id": "PR-75004-12", "description_en": "My package was marked as delivered to Tabac Presse du Marais pickup point, but the shopkeeper claims to have never received it.", "document_path_en": "reclamations/reclamation_vol_point_relais_001_en.pdf"}', '2025-06-20 11:00:00', '2025-06-20 11:05:20'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e06', '6C678912345FR', 'RECL-2025-0006', 'colis_endommage', 'Isabelle Moreau', 'i.moreau@sfr.fr', '06 67 89 01 23', 'Emballage exterieur intact mais l''interieur du colis sentait fortement l''humidite. Livres completement gondoles et inutilisables.', 54.80, 'reclamations/reclamation_colis_endommage_002.pdf', 'completed', '2025-06-22 08:30:00', '2025-06-22 08:33:15', 195000, '{"source": "app_mobile", "description_en": "Outer packaging intact but the inside of the package had a strong moisture smell. Books completely warped and unusable.", "document_path_en": "reclamations/reclamation_colis_endommage_002_en.pdf"}', '2025-06-22 08:30:00', '2025-06-22 08:33:15'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e07', '6C789123456FR', 'RECL-2025-0007', 'mauvaise_adresse', 'Pierre Dubois', 'p.dubois@gmail.com', '06 78 90 12 34', 'Colis livre au 12 rue des Lilas au lieu du 12 rue des Tilleuls. Le voisin qui l''a recu refuse de me le remettre.', 125.00, 'reclamations/reclamation_mauvaise_adresse_001.pdf', 'completed', '2025-06-25 13:45:00', '2025-06-25 13:49:10', 250000, '{"source": "web", "description_en": "Package delivered to 12 rue des Lilas instead of 12 rue des Tilleuls. The neighbor who received it refuses to give it to me.", "document_path_en": "reclamations/reclamation_mauvaise_adresse_001_en.pdf"}', '2025-06-25 13:45:00', '2025-06-25 13:49:10'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e08', '6C891234567FR', 'RECL-2025-0008', 'colis_perdu', 'Nathalie Girard', 'n.girard@yahoo.fr', '07 89 01 23 45', 'Colis expedie depuis la Belgique. Le suivi s''arrete a la douane de Lille depuis 3 semaines. Aucune information disponible.', 340.00, 'reclamations/reclamation_colis_perdu_002.pdf', 'completed', '2025-06-28 15:10:00', '2025-06-28 15:15:45', 345000, '{"source": "phone", "international": true, "description_en": "Package shipped from Belgium. Tracking stops at Lille customs for 3 weeks. No information available.", "document_path_en": "reclamations/reclamation_colis_perdu_002_en.pdf"}', '2025-06-28 15:10:00', '2025-06-28 15:15:45'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e09', '6C912345678FR', 'RECL-2025-0009', 'non_livre', 'Laurent Petit', 'l.petit@outlook.fr', '06 90 12 34 56', 'Troisieme tentative de livraison echouee. Je suis en teletravail et personne ne sonne. La camera de surveillance ne montre aucun passage.', 78.50, 'reclamations/reclamation_non_livre_002.pdf', 'completed', '2025-07-01 09:00:00', '2025-07-01 09:04:20', 260000, '{"source": "web", "attempts": 3, "description_en": "Third failed delivery attempt. I work from home and nobody rings. Security camera shows no postal carrier visit.", "document_path_en": "reclamations/reclamation_non_livre_002_en.pdf"}', '2025-07-01 09:00:00', '2025-07-01 09:04:20'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e10', '6C123456789FR', 'RECL-2025-0010', 'retard_livraison', 'Camille Roux', 'c.roux@gmail.com', '07 01 23 45 67', 'Colissimo express 24h envoye le lundi, toujours en attente le vendredi. Contenu perissable (chocolats artisanaux), probablement fichu.', 95.00, 'reclamations/reclamation_retard_livraison_002.pdf', 'completed', '2025-07-03 17:30:00', '2025-07-03 17:34:50', 320000, '{"source": "web", "perishable": true, "description_en": "Colissimo express 24h shipped Monday, still pending Friday. Perishable content (artisanal chocolates), likely ruined.", "document_path_en": "reclamations/reclamation_retard_livraison_002_en.pdf"}', '2025-07-03 17:30:00', '2025-07-03 17:34:50')
ON CONFLICT (reclamation_number) DO NOTHING;

-- 11-15: status = 'rejected'
INSERT INTO reclamations (id, numero_suivi, reclamation_number, reclamation_type, client_nom, client_email, client_telephone, description, valeur_declaree, document_path, status, submitted_at, processed_at, total_processing_time_ms, metadata, created_at, updated_at) VALUES
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e11', '6C111222333FR', 'RECL-2025-0011', 'colis_endommage', 'Gerard Fontaine', 'g.fontaine@wanadoo.fr', '06 11 22 33 44', 'Legere eraflure sur le carton d''emballage exterieur. Le contenu (vetements) est intact et en parfait etat.', 29.90, 'reclamations/reclamation_colis_endommage_003.pdf', 'rejected', '2025-07-05 10:00:00', '2025-07-05 10:03:10', 190000, '{"source": "web", "description_en": "Slight scuff on the outer packaging box. The contents (clothing) are intact and in perfect condition.", "document_path_en": "reclamations/reclamation_colis_endommage_003_en.pdf"}', '2025-07-05 10:00:00', '2025-07-05 10:03:10'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e12', '6C222333444FR', 'RECL-2025-0012', 'retard_livraison', 'Monique Duval', 'm.duval@free.fr', '07 22 33 44 55', 'Colis livre avec 1 jour de retard sur la date estimee. Pas de prejudice particulier, mais c''est le principe.', 15.00, 'reclamations/reclamation_retard_livraison_003.pdf', 'rejected', '2025-07-06 14:15:00', '2025-07-06 14:17:30', 150000, '{"source": "web", "description_en": "Package delivered 1 day late compared to the estimated date. No particular harm done, but it is the principle.", "document_path_en": "reclamations/reclamation_retard_livraison_003_en.pdf"}', '2025-07-06 14:15:00', '2025-07-06 14:17:30'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e13', '6C333444555FR', 'RECL-2025-0013', 'colis_perdu', 'Eric Leroy', 'e.leroy@gmail.com', '06 33 44 55 66', 'Je n''ai pas recu mon colis. EDIT: en fait il etait chez le gardien, je ne l''avais pas vu. Desole.', 45.00, 'reclamations/reclamation_colis_perdu_003.pdf', 'rejected', '2025-07-07 11:30:00', '2025-07-07 11:32:50', 170000, '{"source": "web", "self_resolved": true, "description_en": "I did not receive my package. EDIT: actually it was with the building concierge, I had not noticed. Sorry.", "document_path_en": "reclamations/reclamation_colis_perdu_003_en.pdf"}', '2025-07-07 11:30:00', '2025-07-07 11:32:50'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e14', '6C444555666FR', 'RECL-2025-0014', 'non_livre', 'Valerie Simon', 'v.simon@orange.fr', '07 44 55 66 77', 'Colis non livre. En verifiant, je me suis rendu compte que j''avais donne une mauvaise adresse lors de la commande.', 22.00, 'reclamations/reclamation_non_livre_003.pdf', 'rejected', '2025-07-08 16:45:00', '2025-07-08 16:47:20', 155000, '{"source": "phone", "description_en": "Package not delivered. Upon checking, I realized I had given the wrong address when placing the order.", "document_path_en": "reclamations/reclamation_non_livre_003_en.pdf"}', '2025-07-08 16:45:00', '2025-07-08 16:47:20'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e15', '6C555666777FR', 'RECL-2025-0015', 'colis_endommage', 'Thierry Lambert', 't.lambert@laposte.net', '06 55 66 77 88', 'Reclamation pour colis endommage datant de 14 mois. Je viens seulement de m''en apercevoir en ouvrant le carton.', 180.00, 'reclamations/reclamation_colis_endommage_004.pdf', 'rejected', '2025-07-09 09:20:00', '2025-07-09 09:23:40', 220000, '{"source": "web", "claim_age_months": 14, "description_en": "Claim for damaged package dating back 14 months. I only just noticed when opening the box.", "document_path_en": "reclamations/reclamation_colis_endommage_004_en.pdf"}', '2025-07-09 09:20:00', '2025-07-09 09:23:40')
ON CONFLICT (reclamation_number) DO NOTHING;

-- 16-20: status = 'pending'
INSERT INTO reclamations (id, numero_suivi, reclamation_number, reclamation_type, client_nom, client_email, client_telephone, description, valeur_declaree, document_path, status, submitted_at, metadata, created_at, updated_at) VALUES
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e16', '6C666777888FR', 'RECL-2025-0016', 'colis_endommage', 'Claire Rousseau', 'c.rousseau@gmail.com', '06 66 77 88 99', 'Recu un colis dont le contenu (appareil photo) est casse. L''objectif est fele et le boitier raye profondement.', 499.00, 'reclamations/reclamation_colis_endommage_005.pdf', 'pending', '2025-07-10 08:00:00', '{"source": "web", "description_en": "Received a package with broken contents (camera). The lens is cracked and the body deeply scratched.", "document_path_en": "reclamations/reclamation_colis_endommage_005_en.pdf"}', '2025-07-10 08:00:00', '2025-07-10 08:00:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e17', '6C777888999FR', 'RECL-2025-0017', 'colis_perdu', 'David Mercier', 'd.mercier@hotmail.fr', '07 77 88 99 00', 'Envoi recommande avec AR contenant des documents administratifs importants. Perdu depuis le 5 juillet.', 50.00, 'reclamations/reclamation_colis_perdu_004.pdf', 'pending', '2025-07-10 10:30:00', '{"source": "bureau_poste", "recommande": true, "description_en": "Registered letter with AR containing important administrative documents. Lost since July 5th.", "document_path_en": "reclamations/reclamation_colis_perdu_004_en.pdf"}', '2025-07-10 10:30:00', '2025-07-10 10:30:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e18', '6C888999000FR', 'RECL-2025-0018', 'vol_point_relais', 'Emilie Fournier', 'e.fournier@sfr.fr', '06 88 99 00 11', 'Colis depose en point relais (Relais Colis Boulangerie Martin). Quand je suis allee le chercher, on m''a dit qu''il avait deja ete retire par quelqu''un d''autre.', 156.50, 'reclamations/reclamation_vol_point_relais_002.pdf', 'pending', '2025-07-11 12:00:00', '{"source": "web", "point_relais_id": "PR-69003-08", "description_en": "Package deposited at pickup point. When I went to collect it, I was told it had already been picked up by someone else.", "document_path_en": "reclamations/reclamation_vol_point_relais_002_en.pdf"}', '2025-07-11 12:00:00', '2025-07-11 12:00:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e19', '6C999000111FR', 'RECL-2025-0019', 'mauvaise_adresse', 'Nicolas Bonnet', 'n.bonnet@outlook.fr', '07 99 00 11 22', 'Mon colis a ete livre a mon ancienne adresse malgre un changement d''adresse effectue il y a 2 mois aupres de La Poste.', 88.00, 'reclamations/reclamation_mauvaise_adresse_002.pdf', 'pending', '2025-07-11 14:45:00', '{"source": "app_mobile", "address_change_date": "2025-05-11", "description_en": "My package was delivered to my old address despite an address change made 2 months ago with La Poste.", "document_path_en": "reclamations/reclamation_mauvaise_adresse_002_en.pdf"}', '2025-07-11 14:45:00', '2025-07-11 14:45:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e20', '6C000111222FR', 'RECL-2025-0020', 'retard_livraison', 'Audrey Blanc', 'a.blanc@gmail.com', '06 00 11 22 33', 'Commande passee il y a 10 jours en Colissimo 48h. Le suivi est bloque sur "en cours de traitement" depuis le depart.', 42.00, 'reclamations/reclamation_retard_livraison_004.pdf', 'pending', '2025-07-12 09:15:00', '{"source": "web", "description_en": "Order placed 10 days ago via Colissimo 48h. Tracking is stuck on processing since departure.", "document_path_en": "reclamations/reclamation_retard_livraison_004_en.pdf"}', '2025-07-12 09:15:00', '2025-07-12 09:15:00')
ON CONFLICT (reclamation_number) DO NOTHING;

-- 21-25: status = 'processing'
INSERT INTO reclamations (id, numero_suivi, reclamation_number, reclamation_type, client_nom, client_email, client_telephone, description, valeur_declaree, document_path, status, submitted_at, metadata, created_at, updated_at) VALUES
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e21', '6C101112131FR', 'RECL-2025-0021', 'colis_endommage', 'Philippe Garnier', 'p.garnier@free.fr', '06 10 11 12 13', 'Colis contenant une guitare classique. Le manche est casse net. Emballage visiblement maltraite (traces de choc).', 350.00, 'reclamations/reclamation_colis_endommage_006.pdf', 'processing', '2025-07-12 11:00:00', '{"source": "web", "fragile_sticker": true, "description_en": "Package containing a classical guitar. The neck is cleanly broken. Packaging visibly mishandled (impact marks).", "document_path_en": "reclamations/reclamation_colis_endommage_006_en.pdf"}', '2025-07-12 11:00:00', '2025-07-12 11:00:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e22', '6C121314151FR', 'RECL-2025-0022', 'non_livre', 'Sandrine Chevalier', 's.chevalier@yahoo.fr', '07 12 13 14 15', 'Colis marque comme livre le 9 juillet, mais je n''ai rien recu. Pas d''avis de passage, rien dans la boite aux lettres.', 76.00, 'reclamations/reclamation_non_livre_004.pdf', 'processing', '2025-07-12 13:30:00', '{"source": "web", "description_en": "Package marked as delivered on July 9th, but I received nothing. No delivery notice, nothing in the mailbox.", "document_path_en": "reclamations/reclamation_non_livre_004_en.pdf"}', '2025-07-12 13:30:00', '2025-07-12 13:30:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e23', '6C131415161FR', 'RECL-2025-0023', 'colis_perdu', 'Julien Morel', 'j.morel@laposte.net', '06 13 14 15 16', 'Colis international (Japon -> France) bloque en douane depuis plus d''un mois. Aucune mise a jour du suivi.', 420.00, 'reclamations/reclamation_colis_perdu_005.pdf', 'processing', '2025-07-12 15:00:00', '{"source": "phone", "international": true, "origin": "JP", "description_en": "International package (Japan to France) stuck in customs for over a month. No tracking update.", "document_path_en": "reclamations/reclamation_colis_perdu_005_en.pdf"}', '2025-07-12 15:00:00', '2025-07-12 15:00:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e24', '6C141516171FR', 'RECL-2025-0024', 'retard_livraison', 'Veronique Blanc', 've.blanc@orange.fr', '07 14 15 16 17', 'Colis Chronopost (sous-traite par La Poste) en retard de 5 jours. Contenu: medicaments veterinaires urgents pour mon chien.', 210.00, 'reclamations/reclamation_retard_livraison_005.pdf', 'processing', '2025-07-12 16:30:00', '{"source": "phone", "urgent_medical": true, "description_en": "Chronopost package (subcontracted by La Poste) 5 days late. Contents: urgent veterinary medication for my sick dog.", "document_path_en": "reclamations/reclamation_retard_livraison_005_en.pdf"}', '2025-07-12 16:30:00', '2025-07-12 16:30:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e25', '6C151617181FR', 'RECL-2025-0025', 'vol_point_relais', 'Remi Faure', 'r.faure@gmail.com', '06 15 16 17 18', 'Colis recupere par une personne non autorisee au point relais. Le commercant dit avoir verifie la piece d''identite mais le nom ne correspond pas.', 299.00, 'reclamations/reclamation_vol_point_relais_003.pdf', 'processing', '2025-07-13 08:00:00', '{"source": "web", "point_relais_id": "PR-31000-05", "identity_check_claimed": true, "description_en": "Package collected by an unauthorized person at the pickup point. The shopkeeper claims to have checked the ID but the name does not match.", "document_path_en": "reclamations/reclamation_vol_point_relais_003_en.pdf"}', '2025-07-13 08:00:00', '2025-07-13 08:00:00')
ON CONFLICT (reclamation_number) DO NOTHING;

-- 26-28: status = 'manual_review'
INSERT INTO reclamations (id, numero_suivi, reclamation_number, reclamation_type, client_nom, client_email, client_telephone, description, valeur_declaree, document_path, status, submitted_at, metadata, created_at, updated_at) VALUES
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e26', '6C161718191FR', 'RECL-2025-0026', 'colis_endommage', 'Helene Picard', 'h.picard@sfr.fr', '07 16 17 18 19', 'Colis contenant du materiel informatique (carte graphique RTX 4090). Le produit ne fonctionne plus apres livraison. Emballage d''origine insuffisant ou colis maltraite?', 500.00, 'reclamations/reclamation_colis_endommage_007.pdf', 'manual_review', '2025-07-13 09:30:00', '{"source": "web", "high_value": true, "ambiguous_cause": true, "description_en": "Package containing computer hardware (RTX 4090 graphics card). Product no longer works after delivery. Original packaging insufficient or package mishandled?", "document_path_en": "reclamations/reclamation_colis_endommage_007_en.pdf"}', '2025-07-13 09:30:00', '2025-07-13 09:30:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e27', '6C171819202FR', 'RECL-2025-0027', 'colis_perdu', 'Yannick Lemaire', 'y.lemaire@hotmail.fr', '06 17 18 19 20', 'Envoi de bijoux de valeur (bague en or). Le suivi montre une livraison mais je n''ai rien recu. Troisieme reclamation similaire en 6 mois.', 480.00, 'reclamations/reclamation_colis_perdu_006.pdf', 'manual_review', '2025-07-13 11:00:00', '{"source": "web", "repeat_claimant": true, "previous_claims": 2, "description_en": "Shipment of valuable jewelry (gold ring). Tracking shows delivery but I received nothing. Third similar claim in 6 months.", "document_path_en": "reclamations/reclamation_colis_perdu_006_en.pdf"}', '2025-07-13 11:00:00', '2025-07-13 11:00:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e28', '6C181920213FR', 'RECL-2025-0028', 'mauvaise_adresse', 'Stephanie Vincent', 's.vincent@gmail.com', '07 18 19 20 21', 'Le colis a ete livre a un homonyme habitant dans la meme rue. Le destinataire refuse de restituer le colis. Situation complexe.', 175.00, 'reclamations/reclamation_mauvaise_adresse_003.pdf', 'manual_review', '2025-07-13 14:00:00', '{"source": "bureau_poste", "homonyme_confirmed": true, "description_en": "The package was delivered to a person with the same name living on the same street. The recipient refuses to return the package. Complex situation.", "document_path_en": "reclamations/reclamation_mauvaise_adresse_003_en.pdf"}', '2025-07-13 14:00:00', '2025-07-13 14:00:00')
ON CONFLICT (reclamation_number) DO NOTHING;

-- 29-30: status = 'escalated'
INSERT INTO reclamations (id, numero_suivi, reclamation_number, reclamation_type, client_nom, client_email, client_telephone, description, valeur_declaree, document_path, status, submitted_at, metadata, created_at, updated_at) VALUES
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e29', '6C192021224FR', 'RECL-2025-0029', 'vol_point_relais', 'Marc-Antoine Dupuis', 'ma.dupuis@orange.fr', '06 19 20 21 22', 'Vol organise au point relais: 3 colis de clients differents disparus le meme jour. Le commercant est soupconne. Plainte deposee.', 450.00, 'reclamations/reclamation_vol_point_relais_004.pdf', 'escalated', '2025-07-13 16:00:00', '{"source": "phone", "police_report": "PV-2025-07890", "multiple_victims": true, "description_en": "Organized theft at pickup point: 3 packages from different customers disappeared on the same day. Shopkeeper suspected. Police report filed.", "document_path_en": "reclamations/reclamation_vol_point_relais_004_en.pdf"}', '2025-07-13 16:00:00', '2025-07-13 16:00:00'),
    ('d1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e30', '6C202122235FR', 'RECL-2025-0030', 'colis_perdu', 'Christine Delorme', 'c.delorme@free.fr', '07 20 21 22 23', 'Colis contenant un tableau de valeur (oeuvre d''art originale). Disparu depuis 3 semaines. Assurance ad valorem souscrite. Litige avec l''assureur sur le montant.', 500.00, 'reclamations/reclamation_colis_perdu_007.pdf', 'escalated', '2025-07-14 08:00:00', '{"source": "courrier_recommande", "insured": true, "insurance_dispute": true, "art_piece": true, "description_en": "Package containing a valuable painting (original artwork). Missing for 3 weeks. Ad valorem insurance taken out. Dispute with insurer over the amount.", "document_path_en": "reclamations/reclamation_colis_perdu_007_en.pdf"}', '2025-07-14 08:00:00', '2025-07-14 08:00:00')
ON CONFLICT (reclamation_number) DO NOTHING;

-- ============================================================================
-- TRACKING EVENTS (for reclamations 1-15)
-- ============================================================================

-- Tracking for RECL-2025-0001 (colis_endommage, completed) — delivered but damaged
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C198745632FR', 'prise_en_charge', '2025-06-06 14:00:00', 'Bureau de Poste Lyon Part-Dieu', 'Prise en charge du colis', '69003', false, '{}'),
    (uuid_generate_v4(), '6C198745632FR', 'tri', '2025-06-06 22:30:00', 'Centre de tri Lyon Vénissieux', 'Tri effectué', '69200', false, '{}'),
    (uuid_generate_v4(), '6C198745632FR', 'en_cours_acheminement', '2025-06-07 03:15:00', 'Plateforme Colis Lyon', 'En cours d''acheminement vers le site de distribution', '69008', false, '{}'),
    (uuid_generate_v4(), '6C198745632FR', 'arrive_centre', '2025-06-08 06:00:00', 'Centre courrier Marseille Capelette', 'Arrivé au centre de distribution', '13010', false, '{}'),
    (uuid_generate_v4(), '6C198745632FR', 'en_livraison', '2025-06-08 08:45:00', 'Marseille 6e', 'En cours de livraison', '13006', false, '{}'),
    (uuid_generate_v4(), '6C198745632FR', 'incident', '2025-06-08 09:10:00', 'Marseille 6e', 'Colis présentant des dommages visibles constatés à la livraison', '13006', false, '{"damage_noted": true}'),
    (uuid_generate_v4(), '6C198745632FR', 'livre', '2025-06-08 09:15:00', 'Marseille 6e', 'Distribué — signé avec réserves pour dommages', '13006', true, '{"signed_with_reserve": true}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0002 (colis_perdu, completed) — trail stops at sorting center
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C234567891FR', 'prise_en_charge', '2025-06-02 10:00:00', 'Bureau de Poste Bordeaux Mériadeck', 'Prise en charge du colis', '33000', false, '{}'),
    (uuid_generate_v4(), '6C234567891FR', 'tri', '2025-06-02 20:00:00', 'Centre de tri Bordeaux Bègles', 'Tri effectué', '33130', false, '{}'),
    (uuid_generate_v4(), '6C234567891FR', 'en_cours_acheminement', '2025-06-03 02:00:00', 'Plateforme Colis Bordeaux', 'En cours d''acheminement', '33300', false, '{}'),
    (uuid_generate_v4(), '6C234567891FR', 'arrive_centre', '2025-06-04 05:30:00', 'Centre de tri Roissy Hub', 'Arrivé au centre de tri', '95700', false, '{}'),
    (uuid_generate_v4(), '6C234567891FR', 'tri', '2025-06-04 08:00:00', 'Centre de tri Roissy Hub', 'En cours de traitement', '95700', false, '{"last_known_scan": true}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0003 (non_livre, completed) — ends with avis_passage
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C345678912FR', 'prise_en_charge', '2025-06-12 09:00:00', 'Bureau de Poste Nantes Centre', 'Prise en charge du colis', '44000', false, '{}'),
    (uuid_generate_v4(), '6C345678912FR', 'tri', '2025-06-12 19:00:00', 'Centre de tri Nantes Rezé', 'Tri effectué', '44400', false, '{}'),
    (uuid_generate_v4(), '6C345678912FR', 'en_cours_acheminement', '2025-06-13 01:30:00', 'Plateforme Colis Nantes', 'En cours d''acheminement', '44300', false, '{}'),
    (uuid_generate_v4(), '6C345678912FR', 'arrive_centre', '2025-06-13 22:00:00', 'Centre courrier Paris 11e', 'Arrivé au centre de distribution', '75011', false, '{}'),
    (uuid_generate_v4(), '6C345678912FR', 'en_livraison', '2025-06-14 07:30:00', 'Paris 11e', 'Pris en charge par le facteur', '75011', false, '{}'),
    (uuid_generate_v4(), '6C345678912FR', 'avis_passage', '2025-06-14 10:45:00', 'Paris 11e', 'Avis de passage déposé — destinataire absent', '75011', false, '{"attempt_number": 1}'),
    (uuid_generate_v4(), '6C345678912FR', 'en_livraison', '2025-06-15 07:30:00', 'Paris 11e', 'Nouvelle tentative de livraison', '75011', false, '{}'),
    (uuid_generate_v4(), '6C345678912FR', 'avis_passage', '2025-06-15 10:30:00', 'Paris 11e', 'Deuxième avis de passage — destinataire absent', '75011', false, '{"attempt_number": 2}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0004 (retard_livraison, completed) — shows delay
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C456789123FR', 'prise_en_charge', '2025-06-08 16:00:00', 'Bureau de Poste Toulouse Capitole', 'Prise en charge du colis — Colissimo J+2', '31000', false, '{}'),
    (uuid_generate_v4(), '6C456789123FR', 'tri', '2025-06-08 23:00:00', 'Centre de tri Toulouse Colomiers', 'Tri effectué', '31770', false, '{}'),
    (uuid_generate_v4(), '6C456789123FR', 'en_cours_acheminement', '2025-06-09 04:00:00', 'Plateforme Colis Toulouse', 'En cours d''acheminement', '31100', false, '{}'),
    (uuid_generate_v4(), '6C456789123FR', 'incident', '2025-06-10 12:00:00', 'Centre de tri Limoges', 'Erreur d''acheminement — colis mal orienté', '87000', false, '{"routing_error": true}'),
    (uuid_generate_v4(), '6C456789123FR', 'en_cours_acheminement', '2025-06-11 06:00:00', 'Centre de tri Limoges', 'Réacheminement vers la bonne destination', '87000', false, '{}'),
    (uuid_generate_v4(), '6C456789123FR', 'arrive_centre', '2025-06-14 07:00:00', 'Centre courrier Strasbourg Neudorf', 'Arrivé au centre de distribution', '67100', false, '{}'),
    (uuid_generate_v4(), '6C456789123FR', 'en_livraison', '2025-06-15 08:00:00', 'Strasbourg Centre', 'En cours de livraison', '67000', false, '{}'),
    (uuid_generate_v4(), '6C456789123FR', 'livre', '2025-06-15 11:30:00', 'Strasbourg Centre', 'Distribué — livré avec 5 jours de retard', '67000', true, '{"days_late": 5}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0005 (vol_point_relais, completed) — delivered to point relais
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C567891234FR', 'prise_en_charge', '2025-06-16 11:00:00', 'Bureau de Poste Nice Jean Médecin', 'Prise en charge du colis', '06000', false, '{}'),
    (uuid_generate_v4(), '6C567891234FR', 'tri', '2025-06-16 21:00:00', 'Centre de tri Nice Saint-Augustin', 'Tri effectué', '06200', false, '{}'),
    (uuid_generate_v4(), '6C567891234FR', 'en_cours_acheminement', '2025-06-17 03:00:00', 'Plateforme Colis Nice', 'En cours d''acheminement vers Paris', '06300', false, '{}'),
    (uuid_generate_v4(), '6C567891234FR', 'arrive_centre', '2025-06-18 05:00:00', 'Centre courrier Paris 4e', 'Arrivé au centre de distribution', '75004', false, '{}'),
    (uuid_generate_v4(), '6C567891234FR', 'en_livraison', '2025-06-18 08:00:00', 'Paris 4e', 'En cours de livraison', '75004', false, '{}'),
    (uuid_generate_v4(), '6C567891234FR', 'avis_passage', '2025-06-18 11:00:00', 'Paris 4e', 'Absent — colis déposé en point relais', '75004', false, '{}'),
    (uuid_generate_v4(), '6C567891234FR', 'point_relais', '2025-06-18 14:00:00', 'Tabac Presse du Marais, Paris 4e', 'Colis disponible en point relais', '75004', true, '{"point_relais_id": "PR-75004-12", "available_until": "2025-07-02"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0006 (colis_endommage, completed) — delivered, damaged by moisture
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C678912345FR', 'prise_en_charge', '2025-06-18 15:00:00', 'Bureau de Poste Lille Flandres', 'Prise en charge du colis', '59000', false, '{}'),
    (uuid_generate_v4(), '6C678912345FR', 'tri', '2025-06-19 00:00:00', 'Centre de tri Lille Lesquin', 'Tri effectué', '59810', false, '{}'),
    (uuid_generate_v4(), '6C678912345FR', 'en_cours_acheminement', '2025-06-19 05:00:00', 'Plateforme Colis Lille', 'En cours d''acheminement', '59800', false, '{}'),
    (uuid_generate_v4(), '6C678912345FR', 'arrive_centre', '2025-06-20 06:00:00', 'Centre courrier Montpellier Antigone', 'Arrivé au centre de distribution', '34000', false, '{}'),
    (uuid_generate_v4(), '6C678912345FR', 'en_livraison', '2025-06-20 08:30:00', 'Montpellier Centre', 'En cours de livraison', '34000', false, '{}'),
    (uuid_generate_v4(), '6C678912345FR', 'livre', '2025-06-20 10:45:00', 'Montpellier Centre', 'Distribué', '34000', true, '{}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0007 (mauvaise_adresse, completed) — delivered to wrong address
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C789123456FR', 'prise_en_charge', '2025-06-22 09:30:00', 'Bureau de Poste Rennes République', 'Prise en charge du colis', '35000', false, '{}'),
    (uuid_generate_v4(), '6C789123456FR', 'tri', '2025-06-22 20:00:00', 'Centre de tri Rennes Saint-Jacques', 'Tri effectué', '35136', false, '{}'),
    (uuid_generate_v4(), '6C789123456FR', 'en_cours_acheminement', '2025-06-23 03:00:00', 'Plateforme Colis Rennes', 'En cours d''acheminement', '35200', false, '{}'),
    (uuid_generate_v4(), '6C789123456FR', 'arrive_centre', '2025-06-24 06:30:00', 'Centre courrier Grenoble Europole', 'Arrivé au centre de distribution', '38000', false, '{}'),
    (uuid_generate_v4(), '6C789123456FR', 'en_livraison', '2025-06-24 08:00:00', 'Grenoble Centre', 'En cours de livraison', '38000', false, '{}'),
    (uuid_generate_v4(), '6C789123456FR', 'livre', '2025-06-24 10:20:00', 'Grenoble Centre', 'Distribué au 12 rue des Lilas', '38000', true, '{"delivered_to": "12 rue des Lilas", "intended_address": "12 rue des Tilleuls"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0008 (colis_perdu, completed) — stuck at customs
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C891234567FR', 'prise_en_charge', '2025-06-05 12:00:00', 'Bureau de Poste Bruxelles Centre', 'Prise en charge du colis — envoi international', '1000', false, '{"country": "BE"}'),
    (uuid_generate_v4(), '6C891234567FR', 'en_cours_acheminement', '2025-06-06 08:00:00', 'Centre international Bruxelles', 'En cours d''acheminement vers la France', '1000', false, '{"country": "BE"}'),
    (uuid_generate_v4(), '6C891234567FR', 'arrive_centre', '2025-06-07 04:00:00', 'Centre de tri international Lille', 'Arrivé au centre de tri international', '59810', false, '{}'),
    (uuid_generate_v4(), '6C891234567FR', 'tri', '2025-06-07 10:00:00', 'Douane Lille', 'Dédouanement en cours', '59810', false, '{"customs_status": "in_progress"}'),
    (uuid_generate_v4(), '6C891234567FR', 'incident', '2025-06-08 14:00:00', 'Douane Lille', 'Retenu en douane — documents complémentaires requis', '59810', false, '{"customs_hold": true}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0009 (non_livre, completed) — multiple failed delivery attempts
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C912345678FR', 'prise_en_charge', '2025-06-26 10:00:00', 'Bureau de Poste Dijon Centre', 'Prise en charge du colis', '21000', false, '{}'),
    (uuid_generate_v4(), '6C912345678FR', 'tri', '2025-06-26 21:00:00', 'Centre de tri Dijon Longvic', 'Tri effectué', '21600', false, '{}'),
    (uuid_generate_v4(), '6C912345678FR', 'en_cours_acheminement', '2025-06-27 02:30:00', 'Plateforme Colis Dijon', 'En cours d''acheminement', '21000', false, '{}'),
    (uuid_generate_v4(), '6C912345678FR', 'arrive_centre', '2025-06-27 18:00:00', 'Centre courrier Annecy', 'Arrivé au centre de distribution', '74000', false, '{}'),
    (uuid_generate_v4(), '6C912345678FR', 'en_livraison', '2025-06-28 07:30:00', 'Annecy Centre', 'Tentative de livraison n 1', '74000', false, '{}'),
    (uuid_generate_v4(), '6C912345678FR', 'avis_passage', '2025-06-28 10:00:00', 'Annecy Centre', 'Destinataire absent', '74000', false, '{"attempt_number": 1}'),
    (uuid_generate_v4(), '6C912345678FR', 'en_livraison', '2025-06-29 07:30:00', 'Annecy Centre', 'Tentative de livraison n 2', '74000', false, '{}'),
    (uuid_generate_v4(), '6C912345678FR', 'avis_passage', '2025-06-29 09:45:00', 'Annecy Centre', 'Destinataire absent', '74000', false, '{"attempt_number": 2}'),
    (uuid_generate_v4(), '6C912345678FR', 'en_livraison', '2025-06-30 07:30:00', 'Annecy Centre', 'Tentative de livraison n 3', '74000', false, '{}'),
    (uuid_generate_v4(), '6C912345678FR', 'avis_passage', '2025-06-30 10:15:00', 'Annecy Centre', 'Troisième avis de passage — colis mis en instance', '74000', false, '{"attempt_number": 3, "mise_en_instance": true}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0010 (retard_livraison, completed) — express with major delay
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C123456789FR', 'prise_en_charge', '2025-06-30 09:00:00', 'Bureau de Poste Aix-en-Provence', 'Prise en charge — Colissimo Express 24h', '13100', false, '{"service": "express_24h"}'),
    (uuid_generate_v4(), '6C123456789FR', 'tri', '2025-06-30 20:00:00', 'Centre de tri Aix-en-Provence', 'Tri effectué', '13100', false, '{}'),
    (uuid_generate_v4(), '6C123456789FR', 'en_cours_acheminement', '2025-07-01 02:00:00', 'Plateforme Colis Marseille', 'En cours d''acheminement', '13000', false, '{}'),
    (uuid_generate_v4(), '6C123456789FR', 'incident', '2025-07-01 14:00:00', 'Centre de tri Paris Gennevilliers', 'Retard de traitement — surcharge plateforme', '92230', false, '{"delay_reason": "platform_overload"}'),
    (uuid_generate_v4(), '6C123456789FR', 'en_cours_acheminement', '2025-07-02 06:00:00', 'Centre de tri Paris Gennevilliers', 'Reprise d''acheminement', '92230', false, '{}'),
    (uuid_generate_v4(), '6C123456789FR', 'arrive_centre', '2025-07-03 07:00:00', 'Centre courrier Tours Centre', 'Arrivé au centre de distribution', '37000', false, '{}'),
    (uuid_generate_v4(), '6C123456789FR', 'en_livraison', '2025-07-03 08:30:00', 'Tours Centre', 'En cours de livraison', '37000', false, '{}'),
    (uuid_generate_v4(), '6C123456789FR', 'livre', '2025-07-03 11:00:00', 'Tours Centre', 'Distribué — livré avec 3 jours de retard', '37000', true, '{"days_late": 3, "service": "express_24h"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0011 (colis_endommage, rejected) — minor scuff, delivered OK
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C111222333FR', 'prise_en_charge', '2025-07-01 14:00:00', 'Bureau de Poste Clermont-Ferrand', 'Prise en charge du colis', '63000', false, '{}'),
    (uuid_generate_v4(), '6C111222333FR', 'tri', '2025-07-01 22:00:00', 'Centre de tri Clermont-Ferrand', 'Tri effectué', '63100', false, '{}'),
    (uuid_generate_v4(), '6C111222333FR', 'en_cours_acheminement', '2025-07-02 03:00:00', 'Plateforme Colis Clermont', 'En cours d''acheminement', '63000', false, '{}'),
    (uuid_generate_v4(), '6C111222333FR', 'arrive_centre', '2025-07-03 06:00:00', 'Centre courrier Perpignan', 'Arrivé au centre de distribution', '66000', false, '{}'),
    (uuid_generate_v4(), '6C111222333FR', 'en_livraison', '2025-07-03 08:00:00', 'Perpignan Centre', 'En cours de livraison', '66000', false, '{}'),
    (uuid_generate_v4(), '6C111222333FR', 'livre', '2025-07-03 10:30:00', 'Perpignan Centre', 'Distribué', '66000', true, '{}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0012 (retard_livraison, rejected) — 1 day late
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C222333444FR', 'prise_en_charge', '2025-07-02 10:00:00', 'Bureau de Poste Rouen Centre', 'Prise en charge du colis', '76000', false, '{}'),
    (uuid_generate_v4(), '6C222333444FR', 'tri', '2025-07-02 20:00:00', 'Centre de tri Rouen Sotteville', 'Tri effectué', '76300', false, '{}'),
    (uuid_generate_v4(), '6C222333444FR', 'en_cours_acheminement', '2025-07-03 04:00:00', 'Plateforme Colis Rouen', 'En cours d''acheminement', '76000', false, '{}'),
    (uuid_generate_v4(), '6C222333444FR', 'arrive_centre', '2025-07-04 07:00:00', 'Centre courrier Caen', 'Arrivé au centre de distribution', '14000', false, '{}'),
    (uuid_generate_v4(), '6C222333444FR', 'en_livraison', '2025-07-05 08:00:00', 'Caen Centre', 'En cours de livraison', '14000', false, '{}'),
    (uuid_generate_v4(), '6C222333444FR', 'livre', '2025-07-05 10:00:00', 'Caen Centre', 'Distribué — 1 jour de retard sur estimation', '14000', true, '{"days_late": 1}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0013 (colis_perdu, rejected — self-resolved) — actually delivered
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C333444555FR', 'prise_en_charge', '2025-07-03 09:00:00', 'Bureau de Poste Metz Centre', 'Prise en charge du colis', '57000', false, '{}'),
    (uuid_generate_v4(), '6C333444555FR', 'tri', '2025-07-03 19:00:00', 'Centre de tri Metz Woippy', 'Tri effectué', '57140', false, '{}'),
    (uuid_generate_v4(), '6C333444555FR', 'en_cours_acheminement', '2025-07-04 02:00:00', 'Plateforme Colis Metz', 'En cours d''acheminement', '57000', false, '{}'),
    (uuid_generate_v4(), '6C333444555FR', 'arrive_centre', '2025-07-05 06:00:00', 'Centre courrier Nancy', 'Arrivé au centre de distribution', '54000', false, '{}'),
    (uuid_generate_v4(), '6C333444555FR', 'en_livraison', '2025-07-05 08:00:00', 'Nancy Centre', 'En cours de livraison', '54000', false, '{}'),
    (uuid_generate_v4(), '6C333444555FR', 'livre', '2025-07-05 09:30:00', 'Nancy Centre', 'Distribué — remis au gardien', '54000', true, '{"delivered_to": "gardien"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0014 (non_livre, rejected — client error) — returned to sender
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C444555666FR', 'prise_en_charge', '2025-07-04 11:00:00', 'Bureau de Poste Orléans Centre', 'Prise en charge du colis', '45000', false, '{}'),
    (uuid_generate_v4(), '6C444555666FR', 'tri', '2025-07-04 21:00:00', 'Centre de tri Orléans Saran', 'Tri effectué', '45770', false, '{}'),
    (uuid_generate_v4(), '6C444555666FR', 'en_cours_acheminement', '2025-07-05 03:00:00', 'Plateforme Colis Orléans', 'En cours d''acheminement', '45000', false, '{}'),
    (uuid_generate_v4(), '6C444555666FR', 'arrive_centre', '2025-07-06 06:30:00', 'Centre courrier Poitiers', 'Arrivé au centre de distribution', '86000', false, '{}'),
    (uuid_generate_v4(), '6C444555666FR', 'en_livraison', '2025-07-06 08:00:00', 'Poitiers Centre', 'En cours de livraison', '86000', false, '{}'),
    (uuid_generate_v4(), '6C444555666FR', 'incident', '2025-07-06 10:00:00', 'Poitiers Centre', 'Adresse incorrecte — destinataire inconnu à cette adresse', '86000', false, '{"reason": "wrong_address"}'),
    (uuid_generate_v4(), '6C444555666FR', 'retour_expediteur', '2025-07-07 09:00:00', 'Poitiers Centre', 'Retour à l''expéditeur — adresse erronée', '86000', true, '{"return_reason": "incorrect_address"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0015 (colis_endommage, rejected — too old) — delivered long ago
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C555666777FR', 'prise_en_charge', '2024-05-10 10:00:00', 'Bureau de Poste Avignon Centre', 'Prise en charge du colis', '84000', false, '{}'),
    (uuid_generate_v4(), '6C555666777FR', 'tri', '2024-05-10 20:00:00', 'Centre de tri Avignon', 'Tri effectué', '84000', false, '{}'),
    (uuid_generate_v4(), '6C555666777FR', 'en_cours_acheminement', '2024-05-11 03:00:00', 'Plateforme Colis Avignon', 'En cours d''acheminement', '84000', false, '{}'),
    (uuid_generate_v4(), '6C555666777FR', 'arrive_centre', '2024-05-12 06:00:00', 'Centre courrier Toulon', 'Arrivé au centre de distribution', '83000', false, '{}'),
    (uuid_generate_v4(), '6C555666777FR', 'en_livraison', '2024-05-12 08:00:00', 'Toulon Centre', 'En cours de livraison', '83000', false, '{}'),
    (uuid_generate_v4(), '6C555666777FR', 'livre', '2024-05-12 10:00:00', 'Toulon Centre', 'Distribué', '83000', true, '{}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0016 (colis_endommage, pending) — camera shows drop marks
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C666777888FR', 'prise_en_charge', '2025-07-05 14:00:00', 'Bureau de Poste Bordeaux Centre', 'Prise en charge du colis', '33000', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C666777888FR', 'tri', '2025-07-05 22:00:00', 'Centre de tri Bordeaux Begles', 'Tri effectue', '33130', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C666777888FR', 'en_cours_acheminement', '2025-07-06 04:00:00', 'Plateforme Colis Bordeaux', 'En cours d''acheminement', '33000', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C666777888FR', 'arrive_centre', '2025-07-07 06:00:00', 'Centre courrier Bordeaux Bastide', 'Arrive au centre de distribution', '33100', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C666777888FR', 'en_livraison', '2025-07-08 08:00:00', 'Bordeaux Centre', 'En cours de livraison', '33000', false, '{"detail_en": "Out for delivery"}'),
    (uuid_generate_v4(), '6C666777888FR', 'livre', '2025-07-08 10:30:00', 'Bordeaux Centre', 'Distribue', '33000', true, '{"detail_en": "Delivered"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0017 (colis_perdu, pending) — last scan at sorting center
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C777888999FR', 'prise_en_charge', '2025-07-05 09:00:00', 'Bureau de Poste Paris 20e', 'Prise en charge de l''envoi recommande', '75020', false, '{"detail_en": "Registered mail accepted"}'),
    (uuid_generate_v4(), '6C777888999FR', 'tri', '2025-07-05 20:00:00', 'Centre de tri Paris Nord', 'Tri effectue', '93200', false, '{"detail_en": "Sorted"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0018 (vol_point_relais, pending) — delivered to pickup point
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C888999000FR', 'prise_en_charge', '2025-07-06 11:00:00', 'Bureau de Poste Lyon 6e', 'Prise en charge du colis', '69006', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C888999000FR', 'tri', '2025-07-06 20:00:00', 'Centre de tri Lyon Venissieux', 'Tri effectue', '69200', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C888999000FR', 'arrive_centre', '2025-07-07 06:00:00', 'Centre courrier Lyon 3e', 'Arrive au centre de distribution', '69003', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C888999000FR', 'point_relais', '2025-07-07 14:00:00', 'Relais Colis Boulangerie Martin, Lyon 3e', 'Colis depose en point relais', '69003', true, '{"point_relais_id": "PR-69003-08", "detail_en": "Package deposited at pickup point"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0019 (mauvaise_adresse, pending) — delivered to old address
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C999000111FR', 'prise_en_charge', '2025-07-07 10:00:00', 'Bureau de Poste Nantes Centre', 'Prise en charge du colis', '44000', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C999000111FR', 'tri', '2025-07-07 20:00:00', 'Centre de tri Nantes Chantenay', 'Tri effectue', '44100', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C999000111FR', 'en_cours_acheminement', '2025-07-08 03:00:00', 'Plateforme Colis Nantes', 'En cours d''acheminement', '44000', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C999000111FR', 'arrive_centre', '2025-07-08 06:00:00', 'Centre courrier Nantes Erdre', 'Arrive au centre de distribution', '44300', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C999000111FR', 'en_livraison', '2025-07-09 08:00:00', 'Nantes Centre', 'En cours de livraison', '44000', false, '{"detail_en": "Out for delivery"}'),
    (uuid_generate_v4(), '6C999000111FR', 'livre', '2025-07-09 10:00:00', 'Nantes Centre', 'Distribue a l''ancienne adresse', '44000', true, '{"delivered_to_old_address": true, "detail_en": "Delivered to old address"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0020 (retard_livraison, pending) — stuck in processing
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C000111222FR', 'prise_en_charge', '2025-07-02 15:00:00', 'Bureau de Poste Toulouse Capitole', 'Prise en charge du colis', '31000', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C000111222FR', 'tri', '2025-07-02 22:00:00', 'Centre de tri Toulouse Colomiers', 'Tri effectue', '31770', false, '{"detail_en": "Sorted"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0021 (colis_endommage, processing) — guitar damage
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C101112131FR', 'prise_en_charge', '2025-07-08 10:00:00', 'Bureau de Poste Paris 12e', 'Prise en charge du colis', '75012', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C101112131FR', 'tri', '2025-07-08 21:00:00', 'Centre de tri Paris Sud', 'Tri effectue', '94500', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C101112131FR', 'en_cours_acheminement', '2025-07-09 03:00:00', 'Plateforme Colis Paris', 'En cours d''acheminement', '94500', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C101112131FR', 'arrive_centre', '2025-07-10 05:00:00', 'Centre courrier Marseille 8e', 'Arrive au centre de distribution', '13008', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C101112131FR', 'en_livraison', '2025-07-10 08:00:00', 'Marseille 8e', 'En cours de livraison', '13008', false, '{"detail_en": "Out for delivery"}'),
    (uuid_generate_v4(), '6C101112131FR', 'livre', '2025-07-10 11:00:00', 'Marseille 8e', 'Distribue', '13008', true, '{"detail_en": "Delivered"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0022 (non_livre, processing) — marked delivered, nothing received
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C121314151FR', 'prise_en_charge', '2025-07-05 13:00:00', 'Bureau de Poste Lyon Part-Dieu', 'Prise en charge du colis', '69003', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C121314151FR', 'tri', '2025-07-05 21:00:00', 'Centre de tri Lyon Venissieux', 'Tri effectue', '69200', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C121314151FR', 'en_cours_acheminement', '2025-07-06 03:00:00', 'Plateforme Colis Lyon', 'En cours d''acheminement', '69200', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C121314151FR', 'arrive_centre', '2025-07-08 05:00:00', 'Centre courrier Nice Centre', 'Arrive au centre de distribution', '06000', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C121314151FR', 'en_livraison', '2025-07-09 07:30:00', 'Nice Centre', 'En cours de livraison', '06000', false, '{"detail_en": "Out for delivery"}'),
    (uuid_generate_v4(), '6C121314151FR', 'livre', '2025-07-09 10:00:00', 'Nice Centre', 'Distribue', '06000', true, '{"detail_en": "Delivered"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0023 (colis_perdu, processing) — stuck in customs (Japan)
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C131415161FR', 'prise_en_charge', '2025-06-01 09:00:00', 'Japan Post Tokyo', 'Prise en charge de l''envoi international', '100-8798', false, '{"country": "JP", "detail_en": "International shipment accepted"}'),
    (uuid_generate_v4(), '6C131415161FR', 'en_cours_acheminement', '2025-06-03 12:00:00', 'Japan Post International', 'Depart du pays d''origine', '100-8798', false, '{"country": "JP", "detail_en": "Departed country of origin"}'),
    (uuid_generate_v4(), '6C131415161FR', 'arrive_centre', '2025-06-06 08:00:00', 'Centre de tri international Roissy CDG', 'Arrive en France', '95700', false, '{"detail_en": "Arrived in France"}'),
    (uuid_generate_v4(), '6C131415161FR', 'tri', '2025-06-06 14:00:00', 'Douane Roissy CDG', 'Dedouanement en cours', '95700', false, '{"customs_status": "in_progress", "detail_en": "Customs clearance in progress"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0024 (retard_livraison, processing) — Chronopost delay
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C141516171FR', 'prise_en_charge', '2025-07-07 10:00:00', 'Bureau de Poste Strasbourg Centre', 'Prise en charge du colis Chronopost', '67000', false, '{"service": "chronopost", "detail_en": "Chronopost package accepted"}'),
    (uuid_generate_v4(), '6C141516171FR', 'tri', '2025-07-07 18:00:00', 'Centre de tri Strasbourg Entzheim', 'Tri effectue', '67960', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C141516171FR', 'en_cours_acheminement', '2025-07-08 02:00:00', 'Plateforme Chronopost Strasbourg', 'En cours d''acheminement', '67000', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C141516171FR', 'incident', '2025-07-09 10:00:00', 'Centre de tri Paris Gennevilliers', 'Retard de traitement -- surcharge plateforme', '92230', false, '{"delay_reason": "platform_overload", "detail_en": "Processing delay -- platform overload"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0025 (vol_point_relais, processing) — unauthorized pickup
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C151617181FR', 'prise_en_charge', '2025-07-08 11:00:00', 'Bureau de Poste Toulouse Wilson', 'Prise en charge du colis', '31000', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C151617181FR', 'tri', '2025-07-08 20:00:00', 'Centre de tri Toulouse Colomiers', 'Tri effectue', '31770', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C151617181FR', 'en_cours_acheminement', '2025-07-09 04:00:00', 'Plateforme Colis Toulouse', 'En cours d''acheminement', '31100', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C151617181FR', 'arrive_centre', '2025-07-09 06:00:00', 'Centre courrier Toulouse Centre', 'Arrive au centre de distribution', '31000', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C151617181FR', 'point_relais', '2025-07-09 14:00:00', 'Presse Loto Tabac, Toulouse', 'Colis depose en point relais', '31000', true, '{"point_relais_id": "PR-31000-05", "detail_en": "Package deposited at pickup point"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0026 (colis_endommage, manual_review) — RTX 4090
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C161718191FR', 'prise_en_charge', '2025-07-09 15:00:00', 'Bureau de Poste Lyon 7e', 'Prise en charge du colis', '69007', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C161718191FR', 'tri', '2025-07-09 23:00:00', 'Centre de tri Lyon Venissieux', 'Tri effectue', '69200', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C161718191FR', 'en_cours_acheminement', '2025-07-10 04:00:00', 'Plateforme Colis Lyon', 'En cours d''acheminement', '69200', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C161718191FR', 'arrive_centre', '2025-07-11 06:00:00', 'Centre courrier Strasbourg Neudorf', 'Arrive au centre de distribution', '67100', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C161718191FR', 'en_livraison', '2025-07-11 08:00:00', 'Strasbourg Centre', 'En cours de livraison', '67000', false, '{"detail_en": "Out for delivery"}'),
    (uuid_generate_v4(), '6C161718191FR', 'livre', '2025-07-11 10:30:00', 'Strasbourg Centre', 'Distribue', '67000', true, '{"detail_en": "Delivered"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0027 (colis_perdu, manual_review) — jewelry
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C171819202FR', 'prise_en_charge', '2025-07-10 10:00:00', 'Bureau de Poste Paris 16e', 'Prise en charge du colis', '75016', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C171819202FR', 'tri', '2025-07-10 20:00:00', 'Centre de tri Paris Ouest', 'Tri effectue', '92000', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C171819202FR', 'en_cours_acheminement', '2025-07-11 03:00:00', 'Plateforme Colis Paris', 'En cours d''acheminement', '92000', false, '{"detail_en": "In transit"}'),
    (uuid_generate_v4(), '6C171819202FR', 'arrive_centre', '2025-07-11 06:00:00', 'Centre courrier Paris 16e', 'Arrive au centre de distribution', '75016', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C171819202FR', 'en_livraison', '2025-07-11 08:00:00', 'Paris 16e', 'En cours de livraison', '75016', false, '{"detail_en": "Out for delivery"}'),
    (uuid_generate_v4(), '6C171819202FR', 'livre', '2025-07-11 10:00:00', 'Paris 16e', 'Distribue', '75016', true, '{"detail_en": "Delivered"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0028 (mauvaise_adresse, manual_review) — homonym
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C181920213FR', 'prise_en_charge', '2025-07-10 12:00:00', 'Bureau de Poste Montpellier Comedie', 'Prise en charge du colis', '34000', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C181920213FR', 'tri', '2025-07-10 21:00:00', 'Centre de tri Montpellier', 'Tri effectue', '34070', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C181920213FR', 'arrive_centre', '2025-07-11 06:00:00', 'Centre courrier Montpellier Antigone', 'Arrive au centre de distribution', '34000', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C181920213FR', 'en_livraison', '2025-07-11 08:00:00', 'Montpellier Centre', 'En cours de livraison', '34000', false, '{"detail_en": "Out for delivery"}'),
    (uuid_generate_v4(), '6C181920213FR', 'livre', '2025-07-11 10:00:00', 'Montpellier Centre', 'Distribue au 14 rue des Oliviers', '34000', true, '{"delivered_to": "14 rue des Oliviers", "intended_address": "14 bis rue des Oliviers", "detail_en": "Delivered to 14 rue des Oliviers (intended: 14 bis)"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0029 (vol_point_relais, escalated) — organized theft
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C192021224FR', 'prise_en_charge', '2025-07-09 10:00:00', 'Bureau de Poste Lyon 2e', 'Prise en charge du colis', '69002', false, '{"detail_en": "Package accepted"}'),
    (uuid_generate_v4(), '6C192021224FR', 'tri', '2025-07-09 20:00:00', 'Centre de tri Lyon Venissieux', 'Tri effectue', '69200', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C192021224FR', 'arrive_centre', '2025-07-10 06:00:00', 'Centre courrier Lyon 7e', 'Arrive au centre de distribution', '69007', false, '{"detail_en": "Arrived at distribution center"}'),
    (uuid_generate_v4(), '6C192021224FR', 'point_relais', '2025-07-10 14:00:00', 'Tabac Presse du Pont, Lyon 7e', 'Colis depose en point relais', '69007', true, '{"point_relais_id": "PR-69007-03", "detail_en": "Package deposited at pickup point"}')
ON CONFLICT DO NOTHING;

-- Tracking for RECL-2025-0030 (colis_perdu, escalated) — art piece
INSERT INTO tracking_events (id, numero_suivi, event_type, event_date, location, detail, code_postal, is_final, metadata) VALUES
    (uuid_generate_v4(), '6C202122235FR', 'prise_en_charge', '2025-07-01 14:00:00', 'Bureau de Poste Paris 6e', 'Prise en charge du colis assure', '75006', false, '{"insured": true, "detail_en": "Insured package accepted"}'),
    (uuid_generate_v4(), '6C202122235FR', 'tri', '2025-07-01 22:00:00', 'Centre de tri Paris Sud', 'Tri effectue', '94500', false, '{"detail_en": "Sorted"}'),
    (uuid_generate_v4(), '6C202122235FR', 'en_cours_acheminement', '2025-07-02 04:00:00', 'Plateforme Colis Paris', 'En cours d''acheminement', '94500', false, '{"detail_en": "In transit"}')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- RECLAMATION PROCESSING LOGS (for completed and rejected: 1-15)
-- ============================================================================

INSERT INTO reclamation_processing_logs (id, reclamation_id, step, status, started_at, completed_at, duration_ms, output_data, error_message) VALUES
    -- RECL-2025-0001 (completed)
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e01', 'tracking_analysis', 'completed', '2025-06-10 09:15:05', '2025-06-10 09:15:15', 10000, '{"events_count": 6, "final_status": "livre"}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e01', 'document_analysis', 'completed', '2025-06-10 09:15:15', '2025-06-10 09:16:00', 45000, '{"photos_analyzed": 3, "damage_confirmed": true}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e01', 'rag_retrieval', 'completed', '2025-06-10 09:16:00', '2025-06-10 09:16:30', 30000, '{"policies_found": 2, "relevance": 0.89}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e01', 'llm_decision', 'completed', '2025-06-10 09:16:30', '2025-06-10 09:18:00', 90000, '{"decision": "rembourser", "confidence": 0.92}', NULL),
    -- RECL-2025-0002 (completed)
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e02', 'tracking_analysis', 'completed', '2025-06-12 14:30:05', '2025-06-12 14:30:20', 15000, '{"events_count": 3, "last_scan_days_ago": 10}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e02', 'rag_retrieval', 'completed', '2025-06-12 14:30:20', '2025-06-12 14:30:50', 30000, '{"policies_found": 1, "relevance": 0.91}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e02', 'llm_decision', 'completed', '2025-06-12 14:30:50', '2025-06-12 14:35:00', 250000, '{"decision": "rembourser", "confidence": 0.88}', NULL),
    -- RECL-2025-0003 (completed)
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e03', 'tracking_analysis', 'completed', '2025-06-15 10:45:05', '2025-06-15 10:45:20', 15000, '{"events_count": 5, "delivery_attempts": 2}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e03', 'rag_retrieval', 'completed', '2025-06-15 10:45:20', '2025-06-15 10:45:50', 30000, '{"policies_found": 1}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e03', 'llm_decision', 'completed', '2025-06-15 10:45:50', '2025-06-15 10:48:00', 130000, '{"decision": "reexpedier", "confidence": 0.85}', NULL),
    -- RECL-2025-0004 (completed)
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e04', 'tracking_analysis', 'completed', '2025-06-18 16:20:05', '2025-06-18 16:20:25', 20000, '{"events_count": 8, "days_late": 5}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e04', 'rag_retrieval', 'completed', '2025-06-18 16:20:25', '2025-06-18 16:21:00', 35000, '{"policies_found": 2}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e04', 'llm_decision', 'completed', '2025-06-18 16:21:00', '2025-06-18 16:24:00', 180000, '{"decision": "rembourser", "confidence": 0.90}', NULL),
    -- RECL-2025-0005 (completed)
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e05', 'tracking_analysis', 'completed', '2025-06-20 11:00:05', '2025-06-20 11:00:20', 15000, '{"events_count": 7, "point_relais_delivery": true}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e05', 'rag_retrieval', 'completed', '2025-06-20 11:00:20', '2025-06-20 11:01:00', 40000, '{"policies_found": 2}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e05', 'llm_decision', 'completed', '2025-06-20 11:01:00', '2025-06-20 11:05:00', 240000, '{"decision": "rembourser", "confidence": 0.87}', NULL),
    -- RECL-2025-0006 to 0010 (completed - abbreviated)
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e06', 'tracking_analysis', 'completed', '2025-06-22 08:30:05', '2025-06-22 08:30:15', 10000, '{"events_count": 6}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e06', 'llm_decision', 'completed', '2025-06-22 08:30:30', '2025-06-22 08:33:00', 150000, '{"decision": "rembourser", "confidence": 0.82}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e07', 'tracking_analysis', 'completed', '2025-06-25 13:45:05', '2025-06-25 13:45:15', 10000, '{"events_count": 6}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e07', 'llm_decision', 'completed', '2025-06-25 13:45:30', '2025-06-25 13:49:00', 210000, '{"decision": "reexpedier", "confidence": 0.91}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e08', 'tracking_analysis', 'completed', '2025-06-28 15:10:05', '2025-06-28 15:10:20', 15000, '{"events_count": 5, "customs_hold": true}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e08', 'llm_decision', 'completed', '2025-06-28 15:10:35', '2025-06-28 15:15:00', 265000, '{"decision": "rembourser", "confidence": 0.86}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e09', 'tracking_analysis', 'completed', '2025-07-01 09:00:05', '2025-07-01 09:00:20', 15000, '{"events_count": 10, "failed_attempts": 3}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e09', 'llm_decision', 'completed', '2025-07-01 09:00:35', '2025-07-01 09:04:00', 205000, '{"decision": "reexpedier", "confidence": 0.89}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e10', 'tracking_analysis', 'completed', '2025-07-03 17:30:05', '2025-07-03 17:30:25', 20000, '{"events_count": 8, "days_late": 3}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e10', 'llm_decision', 'completed', '2025-07-03 17:30:40', '2025-07-03 17:34:00', 200000, '{"decision": "rembourser", "confidence": 0.93}', NULL),
    -- RECL-2025-0011 to 0015 (rejected)
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e11', 'tracking_analysis', 'completed', '2025-07-05 10:00:05', '2025-07-05 10:00:15', 10000, '{"events_count": 6}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e11', 'llm_decision', 'completed', '2025-07-05 10:00:30', '2025-07-05 10:03:00', 150000, '{"decision": "rejeter", "confidence": 0.95}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e12', 'tracking_analysis', 'completed', '2025-07-06 14:15:05', '2025-07-06 14:15:15', 10000, '{"events_count": 6, "days_late": 1}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e12', 'llm_decision', 'completed', '2025-07-06 14:15:25', '2025-07-06 14:17:00', 95000, '{"decision": "rejeter", "confidence": 0.94}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e13', 'tracking_analysis', 'completed', '2025-07-07 11:30:05', '2025-07-07 11:30:15', 10000, '{"events_count": 6, "delivered": true}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e13', 'llm_decision', 'completed', '2025-07-07 11:30:25', '2025-07-07 11:32:00', 95000, '{"decision": "rejeter", "confidence": 0.97}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e14', 'tracking_analysis', 'completed', '2025-07-08 16:45:05', '2025-07-08 16:45:15', 10000, '{"events_count": 7, "returned": true}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e14', 'llm_decision', 'completed', '2025-07-08 16:45:25', '2025-07-08 16:47:00', 95000, '{"decision": "rejeter", "confidence": 0.93}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e15', 'tracking_analysis', 'completed', '2025-07-09 09:20:05', '2025-07-09 09:20:15', 10000, '{"events_count": 6, "claim_age_months": 14}', NULL),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e15', 'llm_decision', 'completed', '2025-07-09 09:20:25', '2025-07-09 09:23:00', 155000, '{"decision": "rejeter", "confidence": 0.96}', NULL)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- RECLAMATION DECISIONS (for completed and rejected reclamations)
-- ============================================================================

-- Decisions for completed reclamations (1-10)
INSERT INTO reclamation_decisions (id, reclamation_id, initial_decision, initial_confidence, initial_reasoning, initial_decided_at, decision, confidence, reasoning, llm_model, requires_manual_review, decided_at, metadata) VALUES
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e01', 'rembourser', 0.92, 'Colis endommage avec preuves photographiques. Dommages visibles sur le contenu (porcelaine brisee). Valeur declaree raisonnable.', '2025-06-10 09:18:00', 'rembourser', 0.92, 'Remboursement approuve -- dommages confirmes par photos et reserves a la livraison.', 'mistral-large-latest', false, '2025-06-10 09:18:00', '{"reasoning_en": "Reimbursement approved -- damage confirmed by photos and reservations noted at delivery. Declared value reasonable."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e02', 'rembourser', 0.88, 'Colis perdu confirme -- dernier scan au centre de tri il y a plus de 10 jours. Aucune mise a jour du suivi.', '2025-06-12 14:34:00', 'rembourser', 0.88, 'Remboursement approuve -- colis considere comme perdu apres 10 jours sans mouvement.', 'mistral-large-latest', false, '2025-06-12 14:34:00', '{"reasoning_en": "Reimbursement approved -- package considered lost after 10 days without movement in tracking."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e03', 'reexpedier', 0.85, 'Non-livraison malgre presence du destinataire. Avis de passage sans tentative reelle. Reexpedition recommandee.', '2025-06-15 10:47:00', 'reexpedier', 0.85, 'Reexpedition ordonnee -- defaut de livraison imputable au facteur.', 'mistral-large-latest', false, '2025-06-15 10:47:00', '{"reasoning_en": "Re-shipment ordered -- delivery failure attributable to the postal carrier."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e04', 'rembourser', 0.90, 'Retard majeur (5 jours pour un J+2). Erreur d''acheminement documentee. Indemnisation conforme aux CGV.', '2025-06-18 16:24:00', 'rembourser', 0.90, 'Remboursement des frais de port + indemnite forfaitaire pour retard excessif.', 'mistral-large-latest', false, '2025-06-18 16:24:00', '{"reasoning_en": "Reimbursement of shipping costs + flat-rate compensation for excessive delay (5 days for a J+2 service)."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e05', 'rembourser', 0.87, 'Vol en point relais suspecte. Le colis est marque comme arrive mais le commercant nie l''avoir recu.', '2025-06-20 11:04:00', 'rembourser', 0.87, 'Remboursement approuve -- responsabilite du point relais engagee.', 'mistral-large-latest', false, '2025-06-20 11:04:00', '{"reasoning_en": "Reimbursement approved -- pickup point liability engaged. Package marked as arrived but shopkeeper denies receipt."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e06', 'rembourser', 0.82, 'Dommages causes par l''humidite durant le transport. Contenu (livres) inutilisable.', '2025-06-22 08:32:00', 'rembourser', 0.82, 'Remboursement partiel -- dommages lies aux conditions de transport.', 'mistral-large-latest', false, '2025-06-22 08:32:00', '{"reasoning_en": "Partial reimbursement -- damage linked to transport conditions. Books rendered unusable by moisture."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e07', 'reexpedier', 0.91, 'Erreur d''adresse imputable au service de livraison. Colis livre a la mauvaise rue.', '2025-06-25 13:48:00', 'reexpedier', 0.91, 'Reexpedition a la bonne adresse -- erreur du facteur confirmee.', 'mistral-large-latest', false, '2025-06-25 13:48:00', '{"reasoning_en": "Re-shipment to the correct address -- postal carrier error confirmed. Delivered to wrong street."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e08', 'rembourser', 0.86, 'Colis bloque en douane depuis 3 semaines sans evolution. Considere comme perdu.', '2025-06-28 15:14:00', 'rembourser', 0.86, 'Remboursement approuve -- colis bloque en douane sans perspective de deblocage.', 'mistral-large-latest', false, '2025-06-28 15:14:00', '{"reasoning_en": "Reimbursement approved -- package stuck in customs for 3 weeks with no prospect of clearance. Considered lost."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e09', 'reexpedier', 0.89, 'Trois tentatives de livraison echouees sans preuve de passage reel. Camera du client confirme l''absence du facteur.', '2025-07-01 09:03:00', 'reexpedier', 0.89, 'Reexpedition avec instruction de livraison specifique au facteur.', 'mistral-large-latest', false, '2025-07-01 09:03:00', '{"reasoning_en": "Re-shipment with specific delivery instructions for the carrier. Customer camera confirms no actual delivery attempts were made."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e10', 'rembourser', 0.93, 'Express 24h livre avec 3 jours de retard. Contenu perissable deteriore. Faute manifeste du service.', '2025-07-03 17:34:00', 'rembourser', 0.93, 'Remboursement total -- retard excessif ayant entraine la perte du contenu perissable.', 'mistral-large-latest', false, '2025-07-03 17:34:00', '{"reasoning_en": "Full reimbursement -- excessive delay caused loss of perishable content. Express 24h delivered 3 days late."}')
ON CONFLICT DO NOTHING;

-- Decisions for rejected reclamations (11-15)
INSERT INTO reclamation_decisions (id, reclamation_id, initial_decision, initial_confidence, initial_reasoning, initial_decided_at, decision, confidence, reasoning, llm_model, requires_manual_review, decided_at, metadata) VALUES
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e11', 'rejeter', 0.95, 'Dommages superficiels sur l''emballage uniquement. Contenu intact et fonctionnel. Pas de prejudice.', '2025-07-05 10:02:00', 'rejeter', 0.95, 'Reclamation rejetee -- aucun dommage sur le contenu du colis.', 'mistral-large-latest', false, '2025-07-05 10:02:00', '{"reasoning_en": "Claim rejected -- no damage to package contents. Only superficial marks on outer packaging."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e12', 'rejeter', 0.94, 'Retard de 1 jour seulement par rapport a l''estimation. Les dates estimees ne sont pas contractuelles.', '2025-07-06 14:17:00', 'rejeter', 0.94, 'Reclamation rejetee -- retard mineur dans les tolerances du service.', 'mistral-large-latest', false, '2025-07-06 14:17:00', '{"reasoning_en": "Claim rejected -- minor delay within service tolerances. Estimated dates are not contractual."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e13', 'rejeter', 0.97, 'Le client a retrouve son colis chez le gardien. Reclamation sans objet.', '2025-07-07 11:32:00', 'rejeter', 0.97, 'Reclamation rejetee -- colis retrouve par le client.', 'mistral-large-latest', false, '2025-07-07 11:32:00', '{"reasoning_en": "Claim rejected -- package found by the customer at the building concierge. Claim is moot."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e14', 'rejeter', 0.93, 'Adresse erronee fournie par le client. La non-livraison n''est pas imputable au service postal.', '2025-07-08 16:47:00', 'rejeter', 0.93, 'Reclamation rejetee -- erreur d''adresse de la part de l''expediteur.', 'mistral-large-latest', false, '2025-07-08 16:47:00', '{"reasoning_en": "Claim rejected -- incorrect address provided by the customer. Non-delivery is not attributable to the postal service."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e15', 'rejeter', 0.96, 'Reclamation deposee 14 mois apres la livraison. Delai de reclamation depasse (1 an maximum).', '2025-07-09 09:23:00', 'rejeter', 0.96, 'Reclamation rejetee -- delai de prescription depasse (14 mois).', 'mistral-large-latest', false, '2025-07-09 09:23:00', '{"reasoning_en": "Claim rejected -- statute of limitations exceeded (14 months). Maximum claim period is 1 year."}')
ON CONFLICT DO NOTHING;

-- Decisions for manual_review reclamations (26-28) — requires_manual_review = true
INSERT INTO reclamation_decisions (id, reclamation_id, initial_decision, initial_confidence, initial_reasoning, initial_decided_at, decision, confidence, reasoning, llm_model, requires_manual_review, decided_at, metadata) VALUES
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e26', 'rembourser', 0.52, 'Impossible de determiner si le dommage est du au transport ou a un defaut d''emballage. Expertise technique necessaire.', '2025-07-13 09:35:00', 'rembourser', 0.52, 'Expertise technique requise -- la cause du dommage (transport vs emballage d''origine) ne peut etre determinee automatiquement.', 'mistral-large-latest', true, '2025-07-13 09:35:00', '{"reasoning_en": "Technical expertise required -- the cause of damage (transport vs original packaging) cannot be determined automatically. High-value item (RTX 4090)."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e27', 'rembourser', 0.45, 'Pattern suspect: 3eme reclamation en 6 mois pour des colis de valeur. Verification du profil client necessaire avant decision.', '2025-07-13 11:05:00', 'rembourser', 0.45, 'Verification du profil client necessaire -- pattern de reclamations repetitives pour des objets de valeur detecte.', 'mistral-large-latest', true, '2025-07-13 11:05:00', '{"reasoning_en": "Client profile verification required -- pattern of repeated claims for valuable items detected. Third similar claim in 6 months."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e28', 'reexpedier', 0.55, 'Situation d''homonymie complexe. Intervention du bureau de poste necessaire pour recuperer le colis et confirmer l''identite du destinataire.', '2025-07-13 14:05:00', 'reexpedier', 0.55, 'Mediation necessaire -- homonymie confirmee entre deux residents de la meme rue. Le bureau de poste doit intervenir.', 'mistral-large-latest', true, '2025-07-13 14:05:00', '{"reasoning_en": "Mediation required -- confirmed case of same-name residents on the same street. Post office must intervene to recover package and verify recipient identity."}')
ON CONFLICT DO NOTHING;

-- Decisions for escalated reclamations (29-30) — requires_manual_review = true
INSERT INTO reclamation_decisions (id, reclamation_id, initial_decision, initial_confidence, initial_reasoning, initial_decided_at, decision, confidence, reasoning, llm_model, requires_manual_review, decided_at, metadata) VALUES
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e29', 'escalader', 0.40, 'Vol organise au point relais impliquant plusieurs victimes. Enquete de police en cours (PV-2025-07890). Escalade vers le service juridique necessaire.', '2025-07-13 16:05:00', 'escalader', 0.40, 'Escalade vers service juridique -- vol organise avec plainte de police. Plusieurs victimes. Point relais desactive.', 'mistral-large-latest', true, '2025-07-13 16:05:00', '{"reasoning_en": "Escalation to legal department -- organized theft with police report. Multiple victims. Pickup point deactivated. Requires coordination with law enforcement."}'),
    (uuid_generate_v4(), 'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e30', 'escalader', 0.48, 'Litige assureur complexe. Valeur declaree (500 EUR) vs estimation expert (2500 EUR). Expertise independante en cours. Montant depasse le seuil de decision autonome.', '2025-07-14 08:05:00', 'escalader', 0.48, 'Escalade vers le service contentieux -- litige assureur sur le montant d''indemnisation. Expertise independante en attente.', 'mistral-large-latest', true, '2025-07-14 08:05:00', '{"reasoning_en": "Escalation to litigation department -- insurer dispute over compensation amount. Declared value (500 EUR) vs expert valuation (2500 EUR). Independent appraisal pending."}')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- RECLAMATION DOCUMENTS (OCR for processed reclamations 1-15, 26-30)
-- ============================================================================

-- Documents for completed reclamations (1-10)
INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e01',
    'reclamation_colis',
    'reclamations/reclamation_colis_endommage_001.pdf',
    85000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C198745632FR
Date de depot: 10/06/2025

INFORMATIONS CLIENT:
Nom: Jean-Pierre Dupont
Email: jp.dupont@gmail.com
Telephone: 06 12 34 56 78

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Colis recu avec le carton completement ecrase. Le contenu (service a the en porcelaine) est brise en plusieurs morceaux. Des reserves ont ete emises a la signature.

Valeur declaree: 89,90 EUR

PIECES JOINTES:
- Photos du colis endommage (3 photos)
- Bon de livraison avec reserves
- Facture d''achat du contenu',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C198745632FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: J***-P*** D***
Email: j***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Colis recu avec le carton completement ecrase. Le contenu (service a the en porcelaine) est brise en plusieurs morceaux. Des reserves ont ete emises a la signature.

Valeur declaree: 89,90 EUR

PIECES JOINTES:
- Photos du colis endommage (3 photos)
- Bon de livraison avec reserves
- Facture d''achat du contenu',
    '{"numero_suivi": "6C198745632FR", "type_reclamation": "colis_endommage", "client_nom": "Jean-Pierre Dupont", "valeur_declaree": 89.90, "date_depot": "2025-06-10", "pieces_jointes": 3}',
    0.94,
    '2025-06-10 09:16:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e02',
    'reclamation_colis',
    'reclamations/reclamation_colis_perdu_001.pdf',
    72000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C234567891FR
Date de depot: 12/06/2025

INFORMATIONS CLIENT:
Nom: Marie-Claire Lefebvre
Email: mc.lefebvre@orange.fr
Telephone: 07 23 45 67 89

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Colis expedie le 2 juin 2025, toujours pas recu. Le suivi indique un dernier scan au centre de tri de Roissy le 4 juin. Aucune mise a jour depuis.

Valeur declaree: 245,00 EUR

PIECES JOINTES:
- Capture d''ecran du suivi Colissimo
- Confirmation d''expedition du vendeur
- Facture d''achat',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C234567891FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: M***-C*** L***
Email: m***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Colis expedie le ** juin ****, toujours pas recu. Le suivi indique un dernier scan au centre de tri de Roissy le ** juin. Aucune mise a jour depuis.

Valeur declaree: 245,00 EUR

PIECES JOINTES:
- Capture d''ecran du suivi Colissimo
- Confirmation d''expedition du vendeur
- Facture d''achat',
    '{"numero_suivi": "6C234567891FR", "type_reclamation": "colis_perdu", "client_nom": "Marie-Claire Lefebvre", "valeur_declaree": 245.00, "date_depot": "2025-06-12", "dernier_scan": "Roissy", "jours_sans_mouvement": 10}',
    0.93,
    '2025-06-12 14:31:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e03',
    'reclamation_colis',
    'reclamations/reclamation_non_livre_001.pdf',
    68000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C345678912FR
Date de depot: 15/06/2025

INFORMATIONS CLIENT:
Nom: Francois Martin
Email: f.martin@free.fr
Telephone: 06 34 56 78 90

TYPE DE RECLAMATION: Non livre

DESCRIPTION DES FAITS:
Le livreur a laisse un avis de passage alors que j''etais present a mon domicile toute la journee. Aucune tentative de sonnette. Le colis a ete renvoye au bureau de poste sans raison.

Valeur declaree: 32,50 EUR

PIECES JOINTES:
- Avis de passage (photo)
- Attestation de presence a domicile',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C345678912FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: F*** M***
Email: f***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Non livre

DESCRIPTION DES FAITS:
Le livreur a laisse un avis de passage alors que j''etais present a mon domicile toute la journee. Aucune tentative de sonnette. Le colis a ete renvoye au bureau de poste sans raison.

Valeur declaree: 32,50 EUR

PIECES JOINTES:
- Avis de passage (photo)
- Attestation de presence a domicile',
    '{"numero_suivi": "6C345678912FR", "type_reclamation": "non_livre", "client_nom": "Francois Martin", "valeur_declaree": 32.50, "date_depot": "2025-06-15", "avis_passage": true}',
    0.95,
    '2025-06-15 10:46:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e04',
    'reclamation_colis',
    'reclamations/reclamation_retard_livraison_001.pdf',
    71000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C456789123FR
Date de depot: 18/06/2025

INFORMATIONS CLIENT:
Nom: Sophie Bernard
Email: sophie.bernard@laposte.net
Telephone: 06 45 67 89 01

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis commande en Colissimo J+2 le 8 juin 2025, toujours pas livre au 18 juin. Delai largement depasse. Il s''agissait d''un cadeau d''anniversaire qui n''est jamais arrive a temps.

Service souscrit: Colissimo J+2
Date d''expedition: 08/06/2025
Delai attendu: 10/06/2025
Retard constate: 8 jours et plus

Valeur declaree: 67,00 EUR

PIECES JOINTES:
- Confirmation de commande
- Capture du suivi Colissimo',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C456789123FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: S*** B***
Email: s***@***.net
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis commande en Colissimo J+2 le ** juin ****, toujours pas livre au ** juin. Delai largement depasse. Il s''agissait d''un cadeau d''anniversaire qui n''est jamais arrive a temps.

Service souscrit: Colissimo J+2
Date d''expedition: **/**/****
Delai attendu: **/**/****
Retard constate: 8 jours et plus

Valeur declaree: 67,00 EUR

PIECES JOINTES:
- Confirmation de commande
- Capture du suivi Colissimo',
    '{"numero_suivi": "6C456789123FR", "type_reclamation": "retard_livraison", "client_nom": "Sophie Bernard", "valeur_declaree": 67.00, "date_depot": "2025-06-18", "service": "Colissimo J+2", "retard_jours": 8}',
    0.93,
    '2025-06-18 16:21:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e05',
    'reclamation_colis',
    'reclamations/reclamation_vol_point_relais_001.pdf',
    78000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C567891234FR
Date de depot: 20/06/2025

INFORMATIONS CLIENT:
Nom: Ahmed Benali
Email: a.benali@hotmail.fr
Telephone: 07 56 78 90 12

TYPE DE RECLAMATION: Vol en point relais

POINT RELAIS:
Nom: Tabac Presse du Marais
Identifiant: PR-75004-12
Adresse: 15 rue des Francs-Bourgeois, 75004 Paris

DESCRIPTION DES FAITS:
Mon colis a ete marque comme livre au point relais Tabac Presse du Marais, mais le commercant affirme ne jamais l''avoir recu. Le suivi indique une livraison au point relais le 18 juin 2025. Je me suis presente le 19 juin et le commercant a nie toute reception.

Valeur declaree: 189,99 EUR

PIECES JOINTES:
- Attestation du commercant
- Capture du suivi indiquant "livre"',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C567891234FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: A*** B***
Email: a***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Vol en point relais

POINT RELAIS:
Nom: Tabac Presse du Marais
Identifiant: PR-75004-12
Adresse: 15 rue des Francs-Bourgeois, 75004 Paris

DESCRIPTION DES FAITS:
Mon colis a ete marque comme livre au point relais Tabac Presse du Marais, mais le commercant affirme ne jamais l''avoir recu. Le suivi indique une livraison au point relais le ** juin ****. Je me suis presente le ** juin et le commercant a nie toute reception.

Valeur declaree: 189,99 EUR

PIECES JOINTES:
- Attestation du commercant
- Capture du suivi indiquant "livre"',
    '{"numero_suivi": "6C567891234FR", "type_reclamation": "vol_point_relais", "client_nom": "Ahmed Benali", "valeur_declaree": 189.99, "date_depot": "2025-06-20", "point_relais_id": "PR-75004-12", "point_relais_nom": "Tabac Presse du Marais"}',
    0.92,
    '2025-06-20 11:01:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e06',
    'reclamation_colis',
    'reclamations/reclamation_colis_endommage_002.pdf',
    65000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C678912345FR
Date de depot: 22/06/2025

INFORMATIONS CLIENT:
Nom: Isabelle Moreau
Email: i.moreau@sfr.fr
Telephone: 06 67 89 01 23

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Emballage exterieur intact mais l''interieur du colis sentait fortement l''humidite. Les livres commandes sont completement gondoles et inutilisables. Le colis a vraisemblablement ete stocke dans un environnement humide durant le transport.

Valeur declaree: 54,80 EUR

PIECES JOINTES:
- Photos des livres endommages (2 photos)
- Facture de la librairie en ligne',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C678912345FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: I*** M***
Email: i***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Emballage exterieur intact mais l''interieur du colis sentait fortement l''humidite. Les livres commandes sont completement gondoles et inutilisables. Le colis a vraisemblablement ete stocke dans un environnement humide durant le transport.

Valeur declaree: 54,80 EUR

PIECES JOINTES:
- Photos des livres endommages (2 photos)
- Facture de la librairie en ligne',
    '{"numero_suivi": "6C678912345FR", "type_reclamation": "colis_endommage", "client_nom": "Isabelle Moreau", "valeur_declaree": 54.80, "date_depot": "2025-06-22", "cause_dommage": "humidite"}',
    0.95,
    '2025-06-22 08:31:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e07',
    'reclamation_colis',
    'reclamations/reclamation_mauvaise_adresse_001.pdf',
    70000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C789123456FR
Date de depot: 25/06/2025

INFORMATIONS CLIENT:
Nom: Pierre Dubois
Email: p.dubois@gmail.com
Telephone: 06 78 90 12 34

TYPE DE RECLAMATION: Mauvaise adresse de livraison

ADRESSE PREVUE: 12 rue des Tilleuls, 75012 Paris
ADRESSE DE LIVRAISON EFFECTIVE: 12 rue des Lilas, 75012 Paris

DESCRIPTION DES FAITS:
Colis livre au 12 rue des Lilas au lieu du 12 rue des Tilleuls. Le voisin qui l''a recu refuse de me le remettre. L''adresse sur le colis est correcte (rue des Tilleuls), l''erreur est imputable au facteur.

Valeur declaree: 125,00 EUR

PIECES JOINTES:
- Photo de l''etiquette d''expedition
- Confirmation de commande avec adresse correcte',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C789123456FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: P*** D***
Email: p***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Mauvaise adresse de livraison

ADRESSE PREVUE: 12 rue des Tilleuls, 75012 Paris
ADRESSE DE LIVRAISON EFFECTIVE: 12 rue des Lilas, 75012 Paris

DESCRIPTION DES FAITS:
Colis livre au 12 rue des Lilas au lieu du 12 rue des Tilleuls. Le voisin qui l''a recu refuse de me le remettre. L''adresse sur le colis est correcte (rue des Tilleuls), l''erreur est imputable au facteur.

Valeur declaree: 125,00 EUR

PIECES JOINTES:
- Photo de l''etiquette d''expedition
- Confirmation de commande avec adresse correcte',
    '{"numero_suivi": "6C789123456FR", "type_reclamation": "mauvaise_adresse", "client_nom": "Pierre Dubois", "valeur_declaree": 125.00, "date_depot": "2025-06-25", "adresse_prevue": "12 rue des Tilleuls, 75012", "adresse_effective": "12 rue des Lilas, 75012"}',
    0.94,
    '2025-06-25 13:46:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e08',
    'reclamation_colis',
    'reclamations/reclamation_colis_perdu_002.pdf',
    75000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C891234567FR
Date de depot: 28/06/2025

INFORMATIONS CLIENT:
Nom: Nathalie Girard
Email: n.girard@yahoo.fr
Telephone: 07 89 01 23 45

TYPE DE RECLAMATION: Colis perdu (international)

DESCRIPTION DES FAITS:
Colis expedie depuis la Belgique le 5 juin 2025. Le suivi s''arrete a la douane de Lille depuis 3 semaines. Aucune information disponible aupres du service client. Le contenu est un lot de vetements de marque.

Pays d''origine: Belgique
Douane bloquante: Lille
Duree de blocage: 3 semaines

Valeur declaree: 340,00 EUR

PIECES JOINTES:
- Preuve d''expedition (BPost Belgique)
- Facture des articles
- Capture du suivi arrete a Lille',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C891234567FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: N*** G***
Email: n***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis perdu (international)

DESCRIPTION DES FAITS:
Colis expedie depuis la Belgique le ** juin ****. Le suivi s''arrete a la douane de Lille depuis 3 semaines. Aucune information disponible aupres du service client. Le contenu est un lot de vetements de marque.

Pays d''origine: Belgique
Douane bloquante: Lille
Duree de blocage: 3 semaines

Valeur declaree: 340,00 EUR

PIECES JOINTES:
- Preuve d''expedition (BPost Belgique)
- Facture des articles
- Capture du suivi arrete a Lille',
    '{"numero_suivi": "6C891234567FR", "type_reclamation": "colis_perdu", "client_nom": "Nathalie Girard", "valeur_declaree": 340.00, "date_depot": "2025-06-28", "international": true, "pays_origine": "Belgique", "douane": "Lille"}',
    0.91,
    '2025-06-28 15:11:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e09',
    'reclamation_colis',
    'reclamations/reclamation_non_livre_002.pdf',
    69000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C912345678FR
Date de depot: 01/07/2025

INFORMATIONS CLIENT:
Nom: Laurent Petit
Email: l.petit@outlook.fr
Telephone: 06 90 12 34 56

TYPE DE RECLAMATION: Non livre

DESCRIPTION DES FAITS:
Troisieme tentative de livraison echouee. Je suis en teletravail a domicile tous les jours et personne ne sonne a la porte. La camera de surveillance installee a l''entree ne montre aucun passage de facteur aux heures indiquees sur les avis.

Nombre de tentatives: 3
Presence confirmee: Oui (teletravail)
Camera de surveillance: Oui

Valeur declaree: 78,50 EUR

PIECES JOINTES:
- Extraits video de la camera (3 fichiers)
- Avis de passage (3 avis)',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C912345678FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: L*** P***
Email: l***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Non livre

DESCRIPTION DES FAITS:
Troisieme tentative de livraison echouee. Je suis en teletravail a domicile tous les jours et personne ne sonne a la porte. La camera de surveillance installee a l''entree ne montre aucun passage de facteur aux heures indiquees sur les avis.

Nombre de tentatives: 3
Presence confirmee: Oui (teletravail)
Camera de surveillance: Oui

Valeur declaree: 78,50 EUR

PIECES JOINTES:
- Extraits video de la camera (3 fichiers)
- Avis de passage (3 avis)',
    '{"numero_suivi": "6C912345678FR", "type_reclamation": "non_livre", "client_nom": "Laurent Petit", "valeur_declaree": 78.50, "date_depot": "2025-07-01", "tentatives_livraison": 3, "camera_surveillance": true}',
    0.94,
    '2025-07-01 09:01:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e10',
    'reclamation_colis',
    'reclamations/reclamation_retard_livraison_002.pdf',
    67000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C123456789FR
Date de depot: 03/07/2025

INFORMATIONS CLIENT:
Nom: Camille Roux
Email: c.roux@gmail.com
Telephone: 07 01 23 45 67

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colissimo express 24h envoye le lundi 30 juin, toujours en attente le vendredi 4 juillet. Contenu perissable (chocolats artisanaux) probablement deteriore par la chaleur et le delai.

Service souscrit: Colissimo Express 24h
Date d''expedition: 30/06/2025
Delai attendu: 01/07/2025
Retard constate: 4 jours
Contenu perissable: Oui

Valeur declaree: 95,00 EUR

PIECES JOINTES:
- Bon d''expedition Express 24h
- Facture chocolatier',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C123456789FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: C*** R***
Email: c***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colissimo express 24h envoye le lundi ** juin, toujours en attente le vendredi ** juillet. Contenu perissable (chocolats artisanaux) probablement deteriore par la chaleur et le delai.

Service souscrit: Colissimo Express 24h
Date d''expedition: **/**/****
Delai attendu: **/**/****
Retard constate: 4 jours
Contenu perissable: Oui

Valeur declaree: 95,00 EUR

PIECES JOINTES:
- Bon d''expedition Express 24h
- Facture chocolatier',
    '{"numero_suivi": "6C123456789FR", "type_reclamation": "retard_livraison", "client_nom": "Camille Roux", "valeur_declaree": 95.00, "date_depot": "2025-07-03", "service": "Colissimo Express 24h", "retard_jours": 4, "contenu_perissable": true}',
    0.93,
    '2025-07-03 17:31:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

-- Documents for rejected reclamations (11-15)
INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e11',
    'reclamation_colis',
    'reclamations/reclamation_colis_endommage_003.pdf',
    55000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C111222333FR
Date de depot: 05/07/2025

INFORMATIONS CLIENT:
Nom: Gerard Fontaine
Email: g.fontaine@wanadoo.fr
Telephone: 06 11 22 33 44

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Legere eraflure sur le carton d''emballage exterieur. Le contenu (vetements) est intact et en parfait etat. Je demande tout de meme un geste commercial.

Valeur declaree: 29,90 EUR

PIECES JOINTES:
- Photo de l''eraflure sur le carton',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C111222333FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: G*** F***
Email: g***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Legere eraflure sur le carton d''emballage exterieur. Le contenu (vetements) est intact et en parfait etat. Je demande tout de meme un geste commercial.

Valeur declaree: 29,90 EUR

PIECES JOINTES:
- Photo de l''eraflure sur le carton',
    '{"numero_suivi": "6C111222333FR", "type_reclamation": "colis_endommage", "client_nom": "Gerard Fontaine", "valeur_declaree": 29.90, "date_depot": "2025-07-05", "contenu_intact": true, "dommage_superficiel": true}',
    0.96,
    '2025-07-05 10:01:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e12',
    'reclamation_colis',
    'reclamations/reclamation_retard_livraison_003.pdf',
    52000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C222333444FR
Date de depot: 06/07/2025

INFORMATIONS CLIENT:
Nom: Monique Duval
Email: m.duval@free.fr
Telephone: 07 22 33 44 55

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis livre avec 1 jour de retard sur la date estimee. Pas de prejudice particulier, mais c''est le principe. Les dates estimees devraient etre respectees.

Service souscrit: Colissimo domicile
Retard constate: 1 jour

Valeur declaree: 15,00 EUR',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C222333444FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: M*** D***
Email: m***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis livre avec 1 jour de retard sur la date estimee. Pas de prejudice particulier, mais c''est le principe. Les dates estimees devraient etre respectees.

Service souscrit: Colissimo domicile
Retard constate: 1 jour

Valeur declaree: 15,00 EUR',
    '{"numero_suivi": "6C222333444FR", "type_reclamation": "retard_livraison", "client_nom": "Monique Duval", "valeur_declaree": 15.00, "date_depot": "2025-07-06", "retard_jours": 1, "prejudice": false}',
    0.96,
    '2025-07-06 14:16:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e13',
    'reclamation_colis',
    'reclamations/reclamation_colis_perdu_003.pdf',
    50000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C333444555FR
Date de depot: 07/07/2025

INFORMATIONS CLIENT:
Nom: Eric Leroy
Email: e.leroy@gmail.com
Telephone: 06 33 44 55 66

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Je n''ai pas recu mon colis.

MISE A JOUR: En fait il etait chez le gardien de l''immeuble, je ne l''avais pas vu. Desole pour le derangement.

Valeur declaree: 45,00 EUR',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C333444555FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: E*** L***
Email: e***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Je n''ai pas recu mon colis.

MISE A JOUR: En fait il etait chez le gardien de l''immeuble, je ne l''avais pas vu. Desole pour le derangement.

Valeur declaree: 45,00 EUR',
    '{"numero_suivi": "6C333444555FR", "type_reclamation": "colis_perdu", "client_nom": "Eric Leroy", "valeur_declaree": 45.00, "date_depot": "2025-07-07", "auto_resolu": true}',
    0.96,
    '2025-07-07 11:31:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e14',
    'reclamation_colis',
    'reclamations/reclamation_non_livre_003.pdf',
    54000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C444555666FR
Date de depot: 08/07/2025

INFORMATIONS CLIENT:
Nom: Valerie Simon
Email: v.simon@orange.fr
Telephone: 07 44 55 66 77

TYPE DE RECLAMATION: Non livre

DESCRIPTION DES FAITS:
Colis non livre a mon adresse. En verifiant ma commande, je me suis rendu compte que j''avais donne une mauvaise adresse lors de la commande (ancien code postal). L''erreur est de mon fait.

Valeur declaree: 22,00 EUR',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C444555666FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: V*** S***
Email: v***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Non livre

DESCRIPTION DES FAITS:
Colis non livre a mon adresse. En verifiant ma commande, je me suis rendu compte que j''avais donne une mauvaise adresse lors de la commande (ancien code postal). L''erreur est de mon fait.

Valeur declaree: 22,00 EUR',
    '{"numero_suivi": "6C444555666FR", "type_reclamation": "non_livre", "client_nom": "Valerie Simon", "valeur_declaree": 22.00, "date_depot": "2025-07-08", "erreur_client": true}',
    0.96,
    '2025-07-08 16:46:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e15',
    'reclamation_colis',
    'reclamations/reclamation_colis_endommage_004.pdf',
    58000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C555666777FR
Date de depot: 09/07/2025

INFORMATIONS CLIENT:
Nom: Thierry Lambert
Email: t.lambert@laposte.net
Telephone: 06 55 66 77 88

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Reclamation pour colis endommage recu il y a 14 mois. Je viens seulement de m''en apercevoir en ouvrant le carton que j''avais stocke dans mon garage. Le contenu (casque audio) est casse.

Date de reception du colis: Mai 2024
Delai avant ouverture: 14 mois

Valeur declaree: 180,00 EUR

PIECES JOINTES:
- Photo du casque casse',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C555666777FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: T*** L***
Email: t***@***.net
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Reclamation pour colis endommage recu il y a 14 mois. Je viens seulement de m''en apercevoir en ouvrant le carton que j''avais stocke dans mon garage. Le contenu (casque audio) est casse.

Date de reception du colis: Mai ****
Delai avant ouverture: 14 mois

Valeur declaree: 180,00 EUR

PIECES JOINTES:
- Photo du casque casse',
    '{"numero_suivi": "6C555666777FR", "type_reclamation": "colis_endommage", "client_nom": "Thierry Lambert", "valeur_declaree": 180.00, "date_depot": "2025-07-09", "delai_reclamation_mois": 14, "prescription_depassee": true}',
    0.95,
    '2025-07-09 09:21:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

-- Documents for manual_review reclamations (26-28)
INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e26',
    'reclamation_colis',
    'reclamations/reclamation_colis_endommage_007.pdf',
    92000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C161718191FR
Date de depot: 13/07/2025

INFORMATIONS CLIENT:
Nom: Helene Picard
Email: h.picard@sfr.fr
Telephone: 07 16 17 18 19

TYPE DE RECLAMATION: Colis endommage (materiel informatique haute valeur)

DESCRIPTION DES FAITS:
Colis contenant du materiel informatique (carte graphique NVIDIA RTX 4090, valeur 500 EUR). Le produit ne fonctionne plus apres livraison. Aucun dommage visible sur l''emballage exterieur. La question est de savoir si le dommage est du au transport (choc interne) ou a un emballage d''origine insuffisant de la part du vendeur.

Le vendeur affirme avoir emballe correctement le produit. La Poste indique que le colis n''a pas subi de choc anormal.

Valeur declaree: 500,00 EUR

PIECES JOINTES:
- Photos de l''emballage exterieur intact
- Photos de l''emballage interieur
- Facture d''achat
- Attestation du vendeur sur l''emballage',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C161718191FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: H*** P***
Email: h***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis endommage (materiel informatique haute valeur)

DESCRIPTION DES FAITS:
Colis contenant du materiel informatique (carte graphique NVIDIA RTX 4090, valeur 500 EUR). Le produit ne fonctionne plus apres livraison. Aucun dommage visible sur l''emballage exterieur. La question est de savoir si le dommage est du au transport (choc interne) ou a un emballage d''origine insuffisant de la part du vendeur.

Le vendeur affirme avoir emballe correctement le produit. La Poste indique que le colis n''a pas subi de choc anormal.

Valeur declaree: 500,00 EUR

PIECES JOINTES:
- Photos de l''emballage exterieur intact
- Photos de l''emballage interieur
- Facture d''achat
- Attestation du vendeur sur l''emballage',
    '{"numero_suivi": "6C161718191FR", "type_reclamation": "colis_endommage", "client_nom": "Helene Picard", "valeur_declaree": 500.00, "date_depot": "2025-07-13", "haute_valeur": true, "cause_ambigue": true, "produit": "RTX 4090"}',
    0.93,
    '2025-07-13 09:31:00',
    3,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e27',
    'reclamation_colis',
    'reclamations/reclamation_colis_perdu_006.pdf',
    88000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C171819202FR
Date de depot: 13/07/2025

INFORMATIONS CLIENT:
Nom: Yannick Lemaire
Email: y.lemaire@hotmail.fr
Telephone: 06 17 18 19 20

TYPE DE RECLAMATION: Colis perdu (bijoux de valeur)

DESCRIPTION DES FAITS:
Envoi de bijoux de valeur (bague en or). Le suivi montre une livraison effectuee le 10 juillet mais je n''ai rien recu. Pas d''avis de passage, pas de signature sur le bon de livraison.

NOTE INTERNE: Il s''agit de la troisieme reclamation similaire de ce client en 6 mois pour des colis de valeur. Les deux precedentes ont ete indemnisees.

Reclamation precedente 1: RECL-2025-XXX (boucles d''oreilles, 220 EUR, indemnise)
Reclamation precedente 2: RECL-2025-YYY (bracelet, 350 EUR, indemnise)

Valeur declaree: 480,00 EUR

PIECES JOINTES:
- Facture du bijoutier
- Capture du suivi',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C171819202FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: Y*** L***
Email: y***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis perdu (bijoux de valeur)

DESCRIPTION DES FAITS:
Envoi de bijoux de valeur (bague en or). Le suivi montre une livraison effectuee le ** juillet mais je n''ai rien recu. Pas d''avis de passage, pas de signature sur le bon de livraison.

NOTE INTERNE: Il s''agit de la troisieme reclamation similaire de ce client en 6 mois pour des colis de valeur. Les deux precedentes ont ete indemnisees.

Reclamation precedente 1: RECL-2025-XXX (boucles d''oreilles, *** EUR, indemnise)
Reclamation precedente 2: RECL-2025-YYY (bracelet, *** EUR, indemnise)

Valeur declaree: 480,00 EUR

PIECES JOINTES:
- Facture du bijoutier
- Capture du suivi',
    '{"numero_suivi": "6C171819202FR", "type_reclamation": "colis_perdu", "client_nom": "Yannick Lemaire", "valeur_declaree": 480.00, "date_depot": "2025-07-13", "reclamations_precedentes": 2, "pattern_suspect": true, "produit": "bague en or"}',
    0.91,
    '2025-07-13 11:01:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e28',
    'reclamation_colis',
    'reclamations/reclamation_mauvaise_adresse_003.pdf',
    82000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C181920213FR
Date de depot: 13/07/2025

INFORMATIONS CLIENT:
Nom: Stephanie Vincent
Email: s.vincent@gmail.com
Telephone: 07 18 19 20 21

TYPE DE RECLAMATION: Mauvaise adresse (homonymie)

ADRESSE DU DESTINATAIRE: 8 avenue Victor Hugo, 92100 Boulogne-Billancourt
ADRESSE DE LIVRAISON EFFECTIVE: 8 avenue Victor Hugo, 92100 Boulogne-Billancourt (meme adresse, personne differente)

DESCRIPTION DES FAITS:
Le colis a ete livre a un homonyme (S. Vincent) habitant dans le meme immeuble au 3eme etage, alors que je suis au 5eme. Le destinataire qui a recu le colis refuse de le restituer, pretendant qu''il lui etait destine. Le facteur n''a pas verifie le numero d''appartement.

Situation complexe: meme nom, meme adresse, meme immeuble. Intervention du bureau de poste necessaire.

Valeur declaree: 175,00 EUR

PIECES JOINTES:
- Avis de passage au nom de S. Vincent (sans precision d''etage)
- Confirmation de commande avec numero d''appartement',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C181920213FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: S*** V***
Email: s***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Mauvaise adresse (homonymie)

ADRESSE DU DESTINATAIRE: 8 avenue Victor Hugo, 92100 Boulogne-Billancourt
ADRESSE DE LIVRAISON EFFECTIVE: 8 avenue Victor Hugo, 92100 Boulogne-Billancourt (meme adresse, personne differente)

DESCRIPTION DES FAITS:
Le colis a ete livre a un homonyme (S*** V***) habitant dans le meme immeuble au 3eme etage, alors que je suis au 5eme. Le destinataire qui a recu le colis refuse de le restituer, pretendant qu''il lui etait destine. Le facteur n''a pas verifie le numero d''appartement.

Situation complexe: meme nom, meme adresse, meme immeuble. Intervention du bureau de poste necessaire.

Valeur declaree: 175,00 EUR

PIECES JOINTES:
- Avis de passage au nom de S*** V*** (sans precision d''etage)
- Confirmation de commande avec numero d''appartement',
    '{"numero_suivi": "6C181920213FR", "type_reclamation": "mauvaise_adresse", "client_nom": "Stephanie Vincent", "valeur_declaree": 175.00, "date_depot": "2025-07-13", "homonymie": true, "meme_immeuble": true}',
    0.92,
    '2025-07-13 14:01:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

-- Documents for escalated reclamations (29-30)
INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e29',
    'reclamation_colis',
    'reclamations/reclamation_vol_point_relais_004.pdf',
    105000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C192021224FR
Date de depot: 13/07/2025

INFORMATIONS CLIENT:
Nom: Marc-Antoine Dupuis
Email: ma.dupuis@orange.fr
Telephone: 06 19 20 21 22

TYPE DE RECLAMATION: Vol organise en point relais

POINT RELAIS:
Nom: Relais Colis Express Toulouse
Identifiant: PR-31000-05
Adresse: 42 rue Alsace-Lorraine, 31000 Toulouse

DESCRIPTION DES FAITS:
Vol organise au point relais: 3 colis de clients differents ont disparu le meme jour (11 juillet 2025). Le commercant est soupconne de complicite. Plainte deposee au commissariat de Toulouse (PV-2025-07890).

Mon colis contenait du materiel electronique (console de jeu + accessoires).

Autres victimes identifiees: 2 autres clients La Poste ont signale des disparitions le meme jour au meme point relais.

Valeur declaree: 450,00 EUR

PIECES JOINTES:
- Copie du depot de plainte (PV-2025-07890)
- Capture du suivi indiquant "livre au point relais"
- Facture d''achat du materiel
- Attestation sur l''honneur',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C192021224FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: M***-A*** D***
Email: m***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Vol organise en point relais

POINT RELAIS:
Nom: Relais Colis Express Toulouse
Identifiant: PR-31000-05
Adresse: 42 rue Alsace-Lorraine, 31000 Toulouse

DESCRIPTION DES FAITS:
Vol organise au point relais: 3 colis de clients differents ont disparu le meme jour (** juillet ****). Le commercant est soupconne de complicite. Plainte deposee au commissariat de Toulouse (PV-****-*****).

Mon colis contenait du materiel electronique (console de jeu + accessoires).

Autres victimes identifiees: 2 autres clients La Poste ont signale des disparitions le meme jour au meme point relais.

Valeur declaree: 450,00 EUR

PIECES JOINTES:
- Copie du depot de plainte (PV-****-*****)
- Capture du suivi indiquant "livre au point relais"
- Facture d''achat du materiel
- Attestation sur l''honneur',
    '{"numero_suivi": "6C192021224FR", "type_reclamation": "vol_point_relais", "client_nom": "Marc-Antoine Dupuis", "valeur_declaree": 450.00, "date_depot": "2025-07-13", "point_relais_id": "PR-31000-05", "plainte_police": "PV-2025-07890", "victimes_multiples": 3, "vol_organise": true}',
    0.90,
    '2025-07-13 16:01:00',
    3,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e30',
    'reclamation_colis',
    'reclamations/reclamation_colis_perdu_007.pdf',
    98000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C202122235FR
Date de depot: 14/07/2025

INFORMATIONS CLIENT:
Nom: Christine Delorme
Email: c.delorme@free.fr
Telephone: 07 20 21 22 23

TYPE DE RECLAMATION: Colis perdu (oeuvre d''art, assurance ad valorem)

DESCRIPTION DES FAITS:
Colis contenant un tableau de valeur (oeuvre d''art originale, huile sur toile, artiste contemporain reconnu). Le colis est disparu depuis 3 semaines, aucune mise a jour du suivi depuis le depart.

Une assurance ad valorem avait ete souscrite pour 500 EUR (valeur declaree a l''expedition). Cependant, une expertise independante a depuis estime la valeur reelle de l''oeuvre a 2 500 EUR. Litige en cours avec le service d''assurance sur le montant d''indemnisation.

Valeur declaree a l''expedition: 500,00 EUR
Estimation expert: 2 500,00 EUR
Ecart: L''assurance ne couvre que la valeur declaree, pas la valeur expertisee.

Valeur declaree: 500,00 EUR

PIECES JOINTES:
- Attestation d''assurance ad valorem
- Rapport d''expertise independante
- Certificat d''authenticite de l''oeuvre
- Photos de l''oeuvre avant expedition',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C202122235FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: C*** D***
Email: c***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis perdu (oeuvre d''art, assurance ad valorem)

DESCRIPTION DES FAITS:
Colis contenant un tableau de valeur (oeuvre d''art originale, huile sur toile, artiste contemporain reconnu). Le colis est disparu depuis 3 semaines, aucune mise a jour du suivi depuis le depart.

Une assurance ad valorem avait ete souscrite pour 500 EUR (valeur declaree a l''expedition). Cependant, une expertise independante a depuis estime la valeur reelle de l''oeuvre a 2 500 EUR. Litige en cours avec le service d''assurance sur le montant d''indemnisation.

Valeur declaree a l''expedition: 500,00 EUR
Estimation expert: 2 500,00 EUR
Ecart: L''assurance ne couvre que la valeur declaree, pas la valeur expertisee.

Valeur declaree: 500,00 EUR

PIECES JOINTES:
- Attestation d''assurance ad valorem
- Rapport d''expertise independante
- Certificat d''authenticite de l''oeuvre
- Photos de l''oeuvre avant expedition',
    '{"numero_suivi": "6C202122235FR", "type_reclamation": "colis_perdu", "client_nom": "Christine Delorme", "valeur_declaree": 500.00, "date_depot": "2025-07-14", "assurance_ad_valorem": true, "valeur_expertisee": 2500.00, "litige_assureur": true, "oeuvre_art": true}',
    0.89,
    '2025-07-14 08:01:00',
    3,
    'fra'
) ON CONFLICT DO NOTHING;

-- Documents for pending reclamations (16-20)
INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e16',
    'reclamation_colis',
    'reclamations/reclamation_colis_endommage_005.pdf',
    78000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C666777888FR
Date de depot: 10/07/2025

INFORMATIONS CLIENT:
Nom: Claire Rousseau
Email: c.rousseau@gmail.com
Telephone: 06 66 77 88 99

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Colis recu avec l''emballage defonce sur le dessus. Le contenu (camera numerique professionnelle) est casse : objectif fissure et boitier raye. Des reserves ont ete emises a la signature. La camera etait neuve et commandee pour un mariage le week-end suivant.

Valeur declaree: 499,00 EUR

PIECES JOINTES:
- Photos du colis endommage (4 photos)
- Facture d''achat de la camera
- Bon de livraison avec reserves',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C666777888FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: C*** R***
Email: c***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Colis recu avec l''emballage defonce sur le dessus. Le contenu (camera numerique professionnelle) est casse : objectif fissure et boitier raye. Des reserves ont ete emises a la signature. La camera etait neuve et commandee pour un mariage le week-end suivant.

Valeur declaree: 499,00 EUR

PIECES JOINTES:
- Photos du colis endommage (4 photos)
- Facture d''achat de la camera
- Bon de livraison avec reserves',
    '{"numero_suivi": "6C666777888FR", "type_reclamation": "colis_endommage", "client_nom": "Claire Rousseau", "valeur_declaree": 499.00, "date_depot": "2025-07-10"}',
    0.94,
    '2025-07-10 08:01:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e17',
    'reclamation_colis',
    'reclamations/reclamation_colis_perdu_004.pdf',
    62000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C777888999FR
Date de depot: 10/07/2025

INFORMATIONS CLIENT:
Nom: David Mercier
Email: d.mercier@hotmail.fr
Telephone: 07 77 88 99 00

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Lettre recommandee envoyee le 28 juin 2025 contenant des documents administratifs importants. Le suivi indique "pris en charge" depuis le 29 juin mais aucune mise a jour depuis. Le destinataire n''a rien recu. Il s''agissait de documents urgents pour une procedure juridique.

Valeur declaree: 50,00 EUR

PIECES JOINTES:
- Recu de depot en bureau de poste
- Capture du suivi en ligne',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C777888999FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: D*** M***
Email: d***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Lettre recommandee envoyee le ** juin **** contenant des documents administratifs importants. Le suivi indique "pris en charge" depuis le ** juin mais aucune mise a jour depuis. Le destinataire n''a rien recu. Il s''agissait de documents urgents pour une procedure juridique.

Valeur declaree: 50,00 EUR

PIECES JOINTES:
- Recu de depot en bureau de poste
- Capture du suivi en ligne',
    '{"numero_suivi": "6C777888999FR", "type_reclamation": "colis_perdu", "client_nom": "David Mercier", "valeur_declaree": 50.00, "date_depot": "2025-07-10"}',
    0.93,
    '2025-07-10 08:15:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e18',
    'reclamation_colis',
    'reclamations/reclamation_vol_point_relais_002.pdf',
    71000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C888999000FR
Date de depot: 11/07/2025

INFORMATIONS CLIENT:
Nom: Emilie Fournier
Email: e.fournier@sfr.fr
Telephone: 06 88 99 00 11

TYPE DE RECLAMATION: Vol en point relais

DESCRIPTION DES FAITS:
Je me suis presentee au point relais pour recuperer mon colis le 10 juillet. Le commercant m''a indique que le colis avait deja ete retire par quelqu''un d''autre le 8 juillet. Je n''ai donne procuration a personne. Le colis contenait un sac a main de marque.

Valeur declaree: 156,50 EUR

PIECES JOINTES:
- Copie de ma piece d''identite
- Capture du suivi indiquant "retire au point relais"
- Facture d''achat du sac',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C888999000FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: E*** F***
Email: e***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Vol en point relais

DESCRIPTION DES FAITS:
Je me suis presentee au point relais pour recuperer mon colis le ** juillet. Le commercant m''a indique que le colis avait deja ete retire par quelqu''un d''autre le ** juillet. Je n''ai donne procuration a personne. Le colis contenait un sac a main de marque.

Valeur declaree: 156,50 EUR

PIECES JOINTES:
- Copie de ma piece d''identite
- Capture du suivi indiquant "retire au point relais"
- Facture d''achat du sac',
    '{"numero_suivi": "6C888999000FR", "type_reclamation": "vol_point_relais", "client_nom": "Emilie Fournier", "valeur_declaree": 156.50, "date_depot": "2025-07-11"}',
    0.92,
    '2025-07-11 08:01:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e19',
    'reclamation_colis',
    'reclamations/reclamation_mauvaise_adresse_002.pdf',
    67000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C999000111FR
Date de depot: 11/07/2025

INFORMATIONS CLIENT:
Nom: Nicolas Bonnet
Email: n.bonnet@outlook.fr
Telephone: 07 99 00 11 22

TYPE DE RECLAMATION: Mauvaise adresse de livraison

DESCRIPTION DES FAITS:
Mon colis a ete livre a mon ancienne adresse malgre le changement d''adresse effectue aupres de La Poste il y a 2 mois. Le nouveau locataire de mon ancien appartement refuse de me remettre le colis. Le colis contenait des livres commandes en ligne.

Valeur declaree: 88,00 EUR

PIECES JOINTES:
- Justificatif de changement d''adresse
- Confirmation de commande avec nouvelle adresse
- Capture du suivi indiquant livraison a l''ancienne adresse',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C999000111FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: N*** B***
Email: n***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Mauvaise adresse de livraison

DESCRIPTION DES FAITS:
Mon colis a ete livre a mon ancienne adresse malgre le changement d''adresse effectue aupres de La Poste il y a 2 mois. Le nouveau locataire de mon ancien appartement refuse de me remettre le colis. Le colis contenait des livres commandes en ligne.

Valeur declaree: 88,00 EUR

PIECES JOINTES:
- Justificatif de changement d''adresse
- Confirmation de commande avec nouvelle adresse
- Capture du suivi indiquant livraison a l''ancienne adresse',
    '{"numero_suivi": "6C999000111FR", "type_reclamation": "mauvaise_adresse", "client_nom": "Nicolas Bonnet", "valeur_declaree": 88.00, "date_depot": "2025-07-11"}',
    0.91,
    '2025-07-11 08:30:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e20',
    'reclamation_colis',
    'reclamations/reclamation_retard_livraison_004.pdf',
    58000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C000111222FR
Date de depot: 12/07/2025

INFORMATIONS CLIENT:
Nom: Audrey Blanc
Email: a.blanc@gmail.com
Telephone: 06 00 11 22 33

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis envoye le 1er juillet en Colissimo domicile. Le suivi indique "en cours de traitement" depuis le 3 juillet sans aucune mise a jour. Cela fait plus de 10 jours sans mouvement. Le colis contenait un cadeau d''anniversaire deja en retard.

Valeur declaree: 42,00 EUR

PIECES JOINTES:
- Capture du suivi bloque depuis le 03/07
- Recu de depot',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C000111222FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: A*** B***
Email: a***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis envoye le ** juillet en Colissimo domicile. Le suivi indique "en cours de traitement" depuis le ** juillet sans aucune mise a jour. Cela fait plus de 10 jours sans mouvement. Le colis contenait un cadeau d''anniversaire deja en retard.

Valeur declaree: 42,00 EUR

PIECES JOINTES:
- Capture du suivi bloque depuis le **/**
- Recu de depot',
    '{"numero_suivi": "6C000111222FR", "type_reclamation": "retard_livraison", "client_nom": "Audrey Blanc", "valeur_declaree": 42.00, "date_depot": "2025-07-12"}',
    0.95,
    '2025-07-12 08:01:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

-- Documents for processing reclamations (21-25)
INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e21',
    'reclamation_colis',
    'reclamations/reclamation_colis_endommage_006.pdf',
    82000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C101112131FR
Date de depot: 12/07/2025

INFORMATIONS CLIENT:
Nom: Philippe Garnier
Email: p.garnier@free.fr
Telephone: 06 10 11 12 13

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Colis contenant une guitare acoustique recu avec le carton perce sur le cote. Le manche de la guitare est casse net au niveau de la jonction avec le corps. L''instrument est irreparable. L''emballage d''origine (etui rigide + carton renforce) etait pourtant conforme aux recommandations.

Valeur declaree: 350,00 EUR

PIECES JOINTES:
- Photos de la guitare cassee (5 photos)
- Facture d''achat de la guitare
- Photo de l''emballage d''origine conforme',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C101112131FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: P*** G***
Email: p***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis endommage

DESCRIPTION DES FAITS:
Colis contenant une guitare acoustique recu avec le carton perce sur le cote. Le manche de la guitare est casse net au niveau de la jonction avec le corps. L''instrument est irreparable. L''emballage d''origine (etui rigide + carton renforce) etait pourtant conforme aux recommandations.

Valeur declaree: 350,00 EUR

PIECES JOINTES:
- Photos de la guitare cassee (5 photos)
- Facture d''achat de la guitare
- Photo de l''emballage d''origine conforme',
    '{"numero_suivi": "6C101112131FR", "type_reclamation": "colis_endommage", "client_nom": "Philippe Garnier", "valeur_declaree": 350.00, "date_depot": "2025-07-12"}',
    0.93,
    '2025-07-12 08:45:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e22',
    'reclamation_colis',
    'reclamations/reclamation_non_livre_004.pdf',
    69000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C121314151FR
Date de depot: 12/07/2025

INFORMATIONS CLIENT:
Nom: Sandrine Chevalier
Email: s.chevalier@yahoo.fr
Telephone: 07 12 13 14 15

TYPE DE RECLAMATION: Colis non livre

DESCRIPTION DES FAITS:
Le suivi indique que mon colis a ete "livre" le 9 juillet a 14h32 mais je n''ai rien recu. J''etais presente a mon domicile toute la journee. Aucun avis de passage n''a ete depose. Mes voisins n''ont rien receptionne non plus. Le colis contenait des produits cosmetiques commandes en ligne.

Valeur declaree: 76,00 EUR

PIECES JOINTES:
- Capture du suivi indiquant "livre"
- Attestation sur l''honneur de non-reception
- Facture de la commande',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C121314151FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: S*** C***
Email: s***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis non livre

DESCRIPTION DES FAITS:
Le suivi indique que mon colis a ete "livre" le ** juillet a **h** mais je n''ai rien recu. J''etais presente a mon domicile toute la journee. Aucun avis de passage n''a ete depose. Mes voisins n''ont rien receptionne non plus. Le colis contenait des produits cosmetiques commandes en ligne.

Valeur declaree: 76,00 EUR

PIECES JOINTES:
- Capture du suivi indiquant "livre"
- Attestation sur l''honneur de non-reception
- Facture de la commande',
    '{"numero_suivi": "6C121314151FR", "type_reclamation": "non_livre", "client_nom": "Sandrine Chevalier", "valeur_declaree": 76.00, "date_depot": "2025-07-12"}',
    0.94,
    '2025-07-12 09:10:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e23',
    'reclamation_colis',
    'reclamations/reclamation_colis_perdu_005.pdf',
    87000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C131415161FR
Date de depot: 13/07/2025

INFORMATIONS CLIENT:
Nom: Julien Morel
Email: j.morel@laposte.net
Telephone: 06 13 14 15 16

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Colis envoye vers le Japon (envoi international) le 25 juin 2025. Le suivi indique que le colis est bloque en douane a Roissy depuis le 28 juin sans aucune mise a jour. Le service client m''indique que le colis est "en cours de dedouanement" mais cela fait maintenant plus de 2 semaines. Le colis contenait des produits artisanaux francais (fromages sous vide et confiseries).

Valeur declaree: 420,00 EUR

PIECES JOINTES:
- Recu de depot international
- Formulaire CN23 de declaration douaniere
- Factures des produits',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C131415161FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: J*** M***
Email: j***@***.net
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Colis perdu

DESCRIPTION DES FAITS:
Colis envoye vers le Japon (envoi international) le ** juin ****. Le suivi indique que le colis est bloque en douane a Roissy depuis le ** juin sans aucune mise a jour. Le service client m''indique que le colis est "en cours de dedouanement" mais cela fait maintenant plus de 2 semaines. Le colis contenait des produits artisanaux francais (fromages sous vide et confiseries).

Valeur declaree: 420,00 EUR

PIECES JOINTES:
- Recu de depot international
- Formulaire CN23 de declaration douaniere
- Factures des produits',
    '{"numero_suivi": "6C131415161FR", "type_reclamation": "colis_perdu", "client_nom": "Julien Morel", "valeur_declaree": 420.00, "date_depot": "2025-07-13"}',
    0.92,
    '2025-07-13 08:01:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e24',
    'reclamation_colis',
    'reclamations/reclamation_retard_livraison_005.pdf',
    75000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C141516171FR
Date de depot: 13/07/2025

INFORMATIONS CLIENT:
Nom: Veronique Blanc
Email: ve.blanc@orange.fr
Telephone: 07 14 15 16 17

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis Chronopost envoye en express le 8 juillet pour une livraison J+1. Le colis n''est toujours pas arrive 5 jours plus tard. Il contient des medicaments veterinaires urgents pour mon chat malade (traitement prescrit par le veterinaire). J''ai du racheter les medicaments en urgence chez un veterinaire local a un cout superieur.

Valeur declaree: 210,00 EUR

PIECES JOINTES:
- Recu d''envoi Chronopost express
- Ordonnance veterinaire
- Facture des medicaments rachetes en urgence',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C141516171FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: V*** B***
Email: v***@***.fr
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Retard de livraison

DESCRIPTION DES FAITS:
Colis Chronopost envoye en express le ** juillet pour une livraison J+1. Le colis n''est toujours pas arrive 5 jours plus tard. Il contient des medicaments veterinaires urgents pour mon chat malade (traitement prescrit par le veterinaire). J''ai du racheter les medicaments en urgence chez un veterinaire local a un cout superieur.

Valeur declaree: 210,00 EUR

PIECES JOINTES:
- Recu d''envoi Chronopost express
- Ordonnance veterinaire
- Facture des medicaments rachetes en urgence',
    '{"numero_suivi": "6C141516171FR", "type_reclamation": "retard_livraison", "client_nom": "Veronique Blanc", "valeur_declaree": 210.00, "date_depot": "2025-07-13"}',
    0.93,
    '2025-07-13 08:30:00',
    2,
    'fra'
) ON CONFLICT DO NOTHING;

INSERT INTO reclamation_documents (
    id, reclamation_id, document_type, file_path, file_size_bytes, mime_type,
    raw_ocr_text, raw_ocr_text_redacted,
    structured_data, ocr_confidence, ocr_processed_at,
    page_count, language
) VALUES (
    uuid_generate_v4(),
    'd1a2b3c4-e5f6-4a7b-8c9d-1a2b3c4d5e25',
    'reclamation_colis',
    'reclamations/reclamation_vol_point_relais_003.pdf',
    73000,
    'application/pdf',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C151617181FR
Date de depot: 13/07/2025

INFORMATIONS CLIENT:
Nom: Remi Faure
Email: r.faure@gmail.com
Telephone: 06 15 16 17 18

TYPE DE RECLAMATION: Vol en point relais

DESCRIPTION DES FAITS:
Mon colis a ete retire au point relais par une personne non autorisee le 11 juillet. Je n''ai donne aucune procuration et la personne qui a retire le colis a presente une fausse piece d''identite selon le commercant. Le colis contenait une tablette tactile neuve. J''ai depose une main courante au commissariat.

Valeur declaree: 299,00 EUR

PIECES JOINTES:
- Main courante deposee au commissariat
- Capture du suivi indiquant "retire au point relais"
- Facture d''achat de la tablette',
    'FORMULAIRE DE RECLAMATION - La Poste / Colissimo

Numero de suivi: 6C151617181FR
Date de depot: **/**/****

INFORMATIONS CLIENT:
Nom: R*** F***
Email: r***@***.com
Telephone: ** ** ** ** **

TYPE DE RECLAMATION: Vol en point relais

DESCRIPTION DES FAITS:
Mon colis a ete retire au point relais par une personne non autorisee le ** juillet. Je n''ai donne aucune procuration et la personne qui a retire le colis a presente une fausse piece d''identite selon le commercant. Le colis contenait une tablette tactile neuve. J''ai depose une main courante au commissariat.

Valeur declaree: 299,00 EUR

PIECES JOINTES:
- Main courante deposee au commissariat
- Capture du suivi indiquant "retire au point relais"
- Facture d''achat de la tablette',
    '{"numero_suivi": "6C151617181FR", "type_reclamation": "vol_point_relais", "client_nom": "Remi Faure", "valeur_declaree": 299.00, "date_depot": "2025-07-13"}',
    0.91,
    '2025-07-13 08:45:00',
    1,
    'fra'
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- COURRIER KNOWLEDGE BASE (15 entries, embeddings left NULL)
-- ============================================================================
INSERT INTO courrier_knowledge_base (id, title, content, category, tags, embedding, is_active) VALUES
    (uuid_generate_v4(), 'Tarifs Colissimo France métropolitaine 2025',
     'Les tarifs Colissimo pour la France métropolitaine en 2025 sont les suivants :
- Jusqu''à 250g : 4,95 EUR
- De 250g à 500g : 6,35 EUR
- De 500g à 1kg : 7,45 EUR
- De 1kg à 2kg : 8,95 EUR
- De 2kg à 5kg : 13,75 EUR
- De 5kg à 10kg : 20,05 EUR
- De 10kg à 15kg : 26,50 EUR
- De 15kg à 30kg : 33,50 EUR
La surtaxe pour livraison le samedi est de 1,50 EUR. Les envois vers la Corse et les DOM-TOM sont soumis à des tarifs spécifiques.', 'tarifs', ARRAY['colissimo', 'tarifs', 'france', 'prix', 'metropolitaine'], NULL, true),

    (uuid_generate_v4(), 'Délais de livraison Colissimo',
     'Les délais de livraison Colissimo en France métropolitaine sont :
- Colissimo domicile : 2 jours ouvrables (J+2)
- Colissimo point retrait : 2 jours ouvrables (J+2)
- Colissimo Expert (avec signature) : 2 jours ouvrables (J+2)
- Colissimo Flash (express) : 1 jour ouvrable (J+1)
Les délais sont indicatifs et non contractuels. Ils sont calculés à partir de la date de dépôt du colis en bureau de poste ou en boîte aux lettres. Des retards peuvent survenir en période de forte activité (Noël, soldes, Black Friday).', 'delais', ARRAY['colissimo', 'delais', 'livraison', 'express', 'j+1', 'j+2'], NULL, true),

    (uuid_generate_v4(), 'Règles d''emballage pour colis fragiles',
     'Pour l''envoi de colis fragiles via Colissimo, La Poste recommande :
1. Utiliser un carton double cannelure neuf et rigide
2. Envelopper chaque article individuellement dans du papier bulle (minimum 2 couches)
3. Combler les espaces vides avec du papier kraft froissé ou des chips de calage
4. Placer l''objet au centre du carton, à au moins 5 cm de chaque paroi
5. Apposer l''étiquette "FRAGILE" sur au moins 2 faces du colis
6. Poids maximum du colis : 30 kg
7. Dimensions maximales : L+2(l+h) <= 150 cm, longueur maximale 100 cm
En cas de casse, un emballage non conforme peut entraîner le rejet de la réclamation.', 'emballage', ARRAY['emballage', 'fragile', 'protection', 'carton', 'normes'], NULL, true),

    (uuid_generate_v4(), 'Procédure de déclaration de perte de colis',
     'Pour déclarer un colis perdu auprès de La Poste :
1. Attendre au minimum 10 jours ouvrables après l''envoi (15 jours pour l''international)
2. Vérifier le suivi en ligne sur laposte.fr ou via l''application mobile
3. Déposer une réclamation en ligne sur reclamation.laposte.fr ou en bureau de poste
4. Fournir : numéro de suivi, preuve d''envoi (reçu), description du contenu, valeur déclarée
5. Délai de traitement : 21 jours maximum
6. Indemnisation forfaitaire : jusqu''à 23 EUR/kg (max 1000 EUR) pour Colissimo standard
7. Pour les envois avec assurance Ad Valorem : remboursement jusqu''à la valeur déclarée (max 5000 EUR)
Le délai de prescription pour les réclamations est de 1 an à compter de la date d''envoi.', 'remboursement', ARRAY['perte', 'colis_perdu', 'declaration', 'reclamation', 'indemnisation'], NULL, true),

    (uuid_generate_v4(), 'Envois internationaux et formalités douanières',
     'Pour les envois internationaux via Colissimo :
- Hors UE : déclaration en douane obligatoire (formulaire CN23 pour les colis > 300 EUR)
- Documents requis : facture commerciale, description détaillée du contenu, valeur unitaire
- Frais de douane : à la charge du destinataire (droits de douane + TVA locale)
- Produits interdits : matières dangereuses, denrées périssables, médicaments, contrefaçons
- Délais indicatifs : 5-7 jours ouvrables (Europe), 7-15 jours (hors Europe)
- Suivi disponible dans 40 pays partenaires
- En cas de rétention en douane, le suivi affiche "Dédouanement en cours". Prévoir un délai supplémentaire de 3 à 10 jours.', 'douane', ARRAY['international', 'douane', 'cn23', 'export', 'import', 'hors_ue'], NULL, true),

    (uuid_generate_v4(), 'Assurance Ad Valorem Colissimo',
     'L''assurance Ad Valorem permet de garantir la valeur réelle du contenu :
- Souscription au moment du dépôt du colis (en bureau de poste ou en ligne)
- Couverture : perte, vol, avarie durant le transport
- Plafond : 5 000 EUR par envoi
- Tarifs : 2,50 EUR pour une valeur jusqu''à 200 EUR, puis 1 EUR par tranche de 100 EUR supplémentaire
- Pièces justificatives en cas de sinistre : facture d''achat originale, photos des dommages
- Délai de déclaration : dans les 3 jours ouvrables suivant la livraison (pour les avaries) ou 10 jours après envoi (pour les pertes)
- Non cumulable avec l''indemnisation forfaitaire standard', 'remboursement', ARRAY['assurance', 'ad_valorem', 'garantie', 'indemnisation', 'valeur'], NULL, true),

    (uuid_generate_v4(), 'Points relais Colissimo — fonctionnement',
     'Le réseau de points relais Colissimo compte plus de 17 000 points en France :
- Types : bureaux de poste, commerçants partenaires, consignes automatiques Pickup
- Horaires : variables selon le commerçant, souvent élargis (soir et week-end)
- Durée de mise à disposition : 10 jours ouvrables à compter de la réception
- Retrait : sur présentation d''une pièce d''identité et du numéro de suivi ou e-mail de notification
- Procuration : possible avec pièce d''identité du mandataire et lettre de procuration signée
- Si non retiré dans le délai : retour automatique à l''expéditeur
- En cas de litige (colis retiré par un tiers) : réclamation à déposer dans les 5 jours', 'services', ARRAY['point_relais', 'retrait', 'pickup', 'commerçant', 'consigne'], NULL, true),

    (uuid_generate_v4(), 'Indemnisation forfaitaire Colissimo',
     'En cas de perte ou d''avarie d''un Colissimo, l''indemnisation forfaitaire s''applique :
- Colissimo sans recommandation : 23 EUR/kg, plafonné à 1 000 EUR
- Colissimo avec recommandation (R1) : forfait de 50 EUR
- Colissimo avec recommandation (R2) : forfait de 200 EUR
- Colissimo avec recommandation (R3) : forfait de 500 EUR
- Retard Colissimo Express/Flash : remboursement des frais d''affranchissement uniquement
Conditions : la réclamation doit être déposée dans un délai de 1 an. L''indemnisation est versée sous 21 jours après acceptation de la réclamation. Le montant est calculé sur la base de la valeur déclarée ou du poids, selon le plus favorable pour le client.', 'remboursement', ARRAY['indemnisation', 'forfait', 'recommandation', 'remboursement', 'plafond'], NULL, true),

    (uuid_generate_v4(), 'Suivi des colis — comment lire les événements',
     'Les événements de suivi Colissimo se décomposent en étapes :
1. Prise en charge : le colis est accepté et scanné au bureau de poste
2. Tri : le colis passe par le centre de tri régional
3. En cours d''acheminement : le colis est en transit entre deux centres
4. Arrivé au centre : le colis est arrivé au centre de distribution local
5. En cours de livraison : le colis est sur le véhicule du facteur
6. Livré : le colis a été distribué avec succès
7. Avis de passage : le destinataire était absent, un avis a été déposé
8. Instance : le colis est en attente de retrait en bureau de poste
9. Retour expéditeur : le colis est renvoyé à l''expéditeur
Les mises à jour peuvent prendre 24 à 48h. En cas d''absence prolongée de scan, contacter le service client.', 'services', ARRAY['suivi', 'tracking', 'evenements', 'statut', 'scan'], NULL, true),

    (uuid_generate_v4(), 'Réclamation pour colis endommagé — procédure',
     'En cas de réception d''un colis endommagé :
1. Émettre des réserves au moment de la livraison (noter les dommages sur le terminal du facteur)
2. Prendre des photos du colis et de son contenu endommagé (dans les 48h)
3. Conserver l''emballage d''origine et tous les éléments de calage
4. Déposer une réclamation en ligne ou en bureau de poste dans les 3 jours ouvrables
5. Fournir : numéro de suivi, photos, description des dommages, facture du contenu
6. La Poste peut demander une expertise du colis (le conserver pendant 30 jours)
7. Délai de réponse : 21 jours maximum
Si les réserves n''ont pas été émises à la livraison, la réclamation reste possible mais la charge de la preuve est plus difficile.', 'remboursement', ARRAY['endommage', 'avarie', 'casse', 'reserves', 'procedure', 'photos'], NULL, true),

    (uuid_generate_v4(), 'Produits interdits dans les envois postaux',
     'La Poste interdit l''envoi des produits suivants via Colissimo :
- Matières dangereuses : explosifs, inflammables, corrosifs, radioactifs
- Batteries au lithium non conformes à la réglementation IATA
- Armes et munitions
- Stupéfiants et substances psychotropes
- Denrées périssables (sauf emballage isotherme homologué)
- Animaux vivants
- Argent liquide et moyens de paiement
- Contrefaçons
- Tabac (au-delà de 50 unités)
L''envoi de produits interdits entraîne la confiscation du colis et peut donner lieu à des poursuites. En cas de dommage lié à un contenu interdit, aucune indemnisation n''est due.', 'services', ARRAY['interdit', 'dangereux', 'restrictions', 'reglementation', 'produits'], NULL, true),

    (uuid_generate_v4(), 'Changement d''adresse et réexpédition de courrier',
     'Le service de réexpédition du courrier de La Poste :
- Réexpédition définitive : à partir de 27,50 EUR pour 6 mois, 45 EUR pour 12 mois
- Réexpédition temporaire : à partir de 24,50 EUR pour 1 mois
- Mise en place : sous 5 jours ouvrables après la demande
- Concerne : lettres, magazines, petits colis (sauf Colissimo et Chronopost)
- Les colis Colissimo suivent l''adresse indiquée sur l''étiquette, pas la réexpédition
- Pour modifier l''adresse d''un Colissimo en cours : utiliser le service "Modifier ma livraison" sur laposte.fr (disponible avant la mise en livraison)
Important : un changement d''adresse via le service réexpédition ne modifie PAS l''adresse de livraison des colis.', 'services', ARRAY['reexpedition', 'changement_adresse', 'demenagement', 'redirection'], NULL, true),

    (uuid_generate_v4(), 'Colissimo Retour — envoi de retour marchandise',
     'Le service Colissimo Retour permet de retourner un colis à un e-commerçant :
- Étiquette de retour : fournie par le e-commerçant (gratuite ou payante selon le marchand)
- Dépôt : en bureau de poste, en point relais ou en boîte aux lettres (si <3 cm d''épaisseur)
- Suivi : même suivi que l''envoi initial, avec numéro dédié
- Délai : 2-3 jours ouvrables en France métropolitaine
- Poids maximum : 30 kg
- Le e-commerçant reçoit une notification de dépôt et peut suivre le retour
- En cas de perte du colis retour, la réclamation doit être déposée par l''expéditeur du retour (le client)
- Si l''étiquette retour est expirée, contacter le service client du e-commerçant pour une nouvelle.', 'services', ARRAY['retour', 'e-commerce', 'renvoi', 'marchandise', 'etiquette_retour'], NULL, true),

    (uuid_generate_v4(), 'Emballages fournis par La Poste',
     'La Poste propose des emballages prêts à l''emploi :
- Boîte Colissimo S (format livre) : 15 x 25 x 10 cm — 1,50 EUR
- Boîte Colissimo M (format moyen) : 22 x 32 x 15 cm — 2,50 EUR
- Boîte Colissimo L (grand format) : 30 x 40 x 20 cm — 3,50 EUR
- Pochette Colissimo : format A4 renforcé — 1,00 EUR
- Tube Colissimo : pour affiches et documents — 2,00 EUR
Ces emballages sont disponibles en bureau de poste et sur boutique.laposte.fr. Ils sont conçus pour résister aux manipulations du tri automatique. L''utilisation d''un emballage Colissimo officiel facilite l''acceptation des réclamations en cas de dommage.', 'emballage', ARRAY['emballage', 'boite', 'pochette', 'tube', 'fournitures', 'achat'], NULL, true),

    (uuid_generate_v4(), 'Lettre recommandée avec accusé de réception (LRAR)',
     'La lettre recommandée avec AR est un service à valeur juridique :
- Tarifs : à partir de 5,36 EUR (jusqu''à 20g) + 1,15 EUR pour l''AR
- Niveaux de recommandation : R1 (indemnité 50 EUR), R2 (200 EUR), R3 (500 EUR)
- Suivi : numéro de suivi permettant de connaître la date de distribution
- Preuve de dépôt : reçu délivré au guichet avec horodatage
- Accusé de réception : carte retournée à l''expéditeur avec signature du destinataire et date
- Valeur juridique : fait foi pour les délais légaux (préavis, résiliation, mise en demeure)
- Conservation : La Poste conserve la preuve de distribution pendant 1 an
- En cas de perte : indemnisation automatique selon le niveau de recommandation choisi', 'services', ARRAY['recommande', 'lrar', 'accuse_reception', 'juridique', 'preuve'], NULL, true)
ON CONFLICT DO NOTHING;
