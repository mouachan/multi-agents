-- ============================================================================
-- Unified Seed Data for Multi-Agents Platform
-- Contains: Claims domain (users, contracts, claims, knowledge base)
--           Tenders domain (references, capabilities, historical, tenders)
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
