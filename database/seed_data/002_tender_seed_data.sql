-- ============================================================================
-- Seed Data: Vinci Construction - Tender Pipeline Demo
-- Description: Realistic French BTP data for Vinci Construction demo
--              Includes references, historical tenders, capabilities,
--              and pending tenders for live demo.
-- ============================================================================

-- Clean existing tender-related data
DELETE FROM tender_processing_logs;
DELETE FROM tender_decisions;
DELETE FROM tender_documents;
DELETE FROM tenders;
DELETE FROM vinci_references;
DELETE FROM vinci_capabilities;
DELETE FROM historical_tenders;

-- ============================================================================
-- 1. VINCI REFERENCES — 10 completed projects
-- ============================================================================
INSERT INTO vinci_references (
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
-- 3. VINCI CAPABILITIES — 20 entries (8 certifications, 6 materiel, 6 personnel)
-- ============================================================================
INSERT INTO vinci_capabilities (
    id, category, name, description, valid_until, region, availability, details, is_active
) VALUES

-- ===== CERTIFICATIONS (8) =====

(
    gen_random_uuid(),
    'certification',
    'ISO 9001:2015 - Management de la qualite',
    'Certification ISO 9001 version 2015 couvrant l''ensemble des activites de construction, rehabilitation et genie civil de Vinci Construction France. Auditee annuellement par Bureau Veritas.',
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
    'VINCI-IDF',
    'AO-2026-0042',
    'Marche public',
    '/claim_documents/ao/ao_2026_0042.pdf',
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
    'VINCI-IDF',
    'AO-2026-0043',
    'Marche prive',
    '/claim_documents/ao/ao_2026_0043.pdf',
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
    'VINCI-ARA',
    'AO-2026-0044',
    'Conception-realisation',
    '/claim_documents/ao/ao_2026_0044.pdf',
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
    'VINCI-IDF',
    'AO-2026-0045',
    'Marche public',
    '/claim_documents/ao/ao_2026_0045.pdf',
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
    'VINCI-NAQ',
    'AO-2026-0046',
    'Marche public',
    '/claim_documents/ao/ao_2026_0046.pdf',
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


-- ============================================================================
-- Verification counts (uncomment to run)
-- ============================================================================
-- SELECT 'vinci_references' AS table_name, COUNT(*) AS row_count FROM vinci_references
-- UNION ALL
-- SELECT 'historical_tenders', COUNT(*) FROM historical_tenders
-- UNION ALL
-- SELECT 'vinci_capabilities', COUNT(*) FROM vinci_capabilities
-- UNION ALL
-- SELECT 'tenders (pending)', COUNT(*) FROM tenders WHERE status = 'pending';
