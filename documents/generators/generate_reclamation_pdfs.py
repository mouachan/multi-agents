#!/usr/bin/env python3
"""
Generate realistic reclamation (postal complaint) PDF documents for the multi-agents platform.
Outputs to documents/reclamations/ with filenames matching the seed data.

Each PDF is a formal complaint document (reclamation) as would be submitted to La Poste.
Generates 30 FR + 30 EN = 60 PDFs total.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ============================================================================
# Reclamation scenarios matching seed SQL (30 entries)
# ============================================================================
SCENARIOS = [
    # 1-10: completed
    {
        "filename": "reclamation_colis_endommage_001",
        "type": "colis_endommage",
        "numero_suivi": "6C198745632FR",
        "reclamation_number": "RECL-2025-0001",
        "client": "Jean-Pierre Dupont",
        "email": "jp.dupont@gmail.com",
        "telephone": "06 12 34 56 78",
        "date_envoi": "06/06/2025",
        "date_reception": "08/06/2025",
        "description_fr": (
            "Colis recu avec le carton completement ecrase. Le contenu (service a the en "
            "porcelaine de Limoges, 6 tasses et soucoupes) est brise en plusieurs morceaux. "
            "L'emballage presentait des traces d'ecrasement severe sur la face superieure et "
            "le cote droit. J'ai emis des reserves au moment de la livraison aupres du facteur. "
            "Photos des dommages jointes a cette reclamation."
        ),
        "description_en": (
            "Package received with the box completely crushed. The contents (Limoges porcelain "
            "tea set, 6 cups and saucers) are broken into multiple pieces. The packaging showed "
            "severe crushing marks on the top and right side. I noted reservations at the time "
            "of delivery with the postal carrier. Photos of the damage are attached to this claim."
        ),
        "valeur": "89.90 EUR",
        "expediteur": "Maison de la Porcelaine, Limoges",
        "destination": "Marseille 6e",
    },
    {
        "filename": "reclamation_colis_perdu_001",
        "type": "colis_perdu",
        "numero_suivi": "6C234567891FR",
        "reclamation_number": "RECL-2025-0002",
        "client": "Marie-Claire Lefebvre",
        "email": "mc.lefebvre@orange.fr",
        "telephone": "07 23 45 67 89",
        "date_envoi": "02/06/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis expedie le 2 juin depuis Bordeaux Meriadeck, toujours pas recu a ce jour. "
            "Le suivi en ligne indique un dernier scan au centre de tri de Roissy le 4 juin a "
            "08h00 avec le statut 'En cours de traitement'. Depuis, aucune mise a jour. "
            "Le colis contenait des vetements de marque commandes en ligne. J'ai contacte le "
            "service client par telephone le 10 juin sans obtenir d'information supplementaire."
        ),
        "description_en": (
            "Package shipped on June 2nd from Bordeaux Meriadeck, still not received to date. "
            "Online tracking shows a last scan at Roissy sorting center on June 4th at 8:00 AM "
            "with status 'Processing'. No update since then. The package contained brand-name "
            "clothing ordered online. I contacted customer service by phone on June 10th without "
            "getting any additional information."
        ),
        "valeur": "245.00 EUR",
        "expediteur": "Particulier (vente en ligne)",
        "destination": "Paris 15e",
    },
    {
        "filename": "reclamation_non_livre_001",
        "type": "non_livre",
        "numero_suivi": "6C345678912FR",
        "reclamation_number": "RECL-2025-0003",
        "client": "Francois Martin",
        "email": "f.martin@free.fr",
        "telephone": "06 34 56 78 90",
        "date_envoi": "12/06/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Le livreur a laisse un avis de passage alors que j'etais present a mon domicile "
            "toute la journee. Aucune tentative de sonnette n'a eu lieu. Je travaille en "
            "teletravail et mon bureau donne directement sur la porte d'entree. Ma camera "
            "de surveillance confirme qu'aucune personne ne s'est presentee a ma porte. "
            "L'avis de passage a ete depose directement dans la boite aux lettres sans tentative."
        ),
        "description_en": (
            "The delivery person left a notice of passage while I was home all day. No doorbell "
            "attempt was made. I work from home and my office directly overlooks the front door. "
            "My security camera confirms that no person came to my door. The delivery notice "
            "was placed directly in the mailbox without any actual delivery attempt."
        ),
        "valeur": "32.50 EUR",
        "expediteur": "Amazon Logistique",
        "destination": "Paris 11e",
    },
    {
        "filename": "reclamation_retard_livraison_001",
        "type": "retard_livraison",
        "numero_suivi": "6C456789123FR",
        "reclamation_number": "RECL-2025-0004",
        "client": "Sophie Bernard",
        "email": "sophie.bernard@laposte.net",
        "telephone": "06 45 67 89 01",
        "date_envoi": "08/06/2025",
        "date_reception": "15/06/2025",
        "description_fr": (
            "Colis commande en Colissimo J+2 le 8 juin depuis Toulouse. Malgre le service "
            "rapide choisi et paye, le colis n'a ete livre que le 15 juin, soit 5 jours de "
            "retard. Le suivi montre une erreur d'acheminement via Limoges au lieu du trajet "
            "direct vers Strasbourg. Le colis contenait un cadeau d'anniversaire qui est arrive "
            "bien trop tard pour l'occasion prevue le 10 juin."
        ),
        "description_en": (
            "Package ordered via Colissimo J+2 on June 8th from Toulouse. Despite choosing and "
            "paying for the fast service, the package was only delivered on June 15th, 5 days "
            "late. Tracking shows a routing error via Limoges instead of a direct route to "
            "Strasbourg. The package contained a birthday present that arrived far too late "
            "for the occasion planned on June 10th."
        ),
        "valeur": "67.00 EUR",
        "expediteur": "Boutique en ligne",
        "destination": "Strasbourg Centre",
    },
    {
        "filename": "reclamation_vol_point_relais_001",
        "type": "vol_point_relais",
        "numero_suivi": "6C567891234FR",
        "reclamation_number": "RECL-2025-0005",
        "client": "Ahmed Benali",
        "email": "a.benali@hotmail.fr",
        "telephone": "07 56 78 90 12",
        "date_envoi": "16/06/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Mon colis a ete marque comme livre au point relais Tabac Presse du Marais (PR-75004-12), "
            "mais le commercant affirme ne jamais l'avoir recu. Le suivi indique une livraison "
            "le 18 juin a 14h00 au point relais. Lorsque je me suis presente le 19 juin, le "
            "commercant m'a confirme n'avoir recu aucun colis a mon nom. Le colis contenait "
            "un smartphone reconditionne de valeur."
        ),
        "description_en": (
            "My package was marked as delivered to the Tabac Presse du Marais pickup point "
            "(PR-75004-12), but the shopkeeper claims to have never received it. Tracking "
            "shows delivery on June 18th at 2:00 PM at the pickup point. When I went on "
            "June 19th, the shopkeeper confirmed he had not received any package in my name. "
            "The package contained a refurbished smartphone of significant value."
        ),
        "valeur": "189.99 EUR",
        "expediteur": "BackMarket",
        "destination": "Paris 4e (point relais)",
    },
    {
        "filename": "reclamation_colis_endommage_002",
        "type": "colis_endommage",
        "numero_suivi": "6C678912345FR",
        "reclamation_number": "RECL-2025-0006",
        "client": "Isabelle Moreau",
        "email": "i.moreau@sfr.fr",
        "telephone": "06 67 89 01 23",
        "date_envoi": "18/06/2025",
        "date_reception": "20/06/2025",
        "description_fr": (
            "Emballage exterieur intact mais l'interieur du colis sentait fortement l'humidite. "
            "Les 4 livres commandes sont completement gondoles et inutilisables. Le carton "
            "interieur presentait des taches d'eau sur le fond. Les livres ont absorbe l'humidite "
            "et les pages sont collees entre elles. Probablement stocke dans un endroit humide "
            "ou expose a la pluie durant le transport."
        ),
        "description_en": (
            "Outer packaging was intact but the inside of the box had a strong moisture smell. "
            "The 4 books ordered are completely warped and unusable. The inner cardboard had "
            "water stains on the bottom. The books absorbed the moisture and pages are stuck "
            "together. Likely stored in a damp location or exposed to rain during transport."
        ),
        "valeur": "54.80 EUR",
        "expediteur": "Librairie en ligne",
        "destination": "Montpellier Centre",
    },
    {
        "filename": "reclamation_mauvaise_adresse_001",
        "type": "mauvaise_adresse",
        "numero_suivi": "6C789123456FR",
        "reclamation_number": "RECL-2025-0007",
        "client": "Pierre Dubois",
        "email": "p.dubois@gmail.com",
        "telephone": "06 78 90 12 34",
        "date_envoi": "22/06/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis livre au 12 rue des Lilas au lieu du 12 rue des Tilleuls a Grenoble. "
            "Le facteur s'est trompe de rue malgre l'adresse correcte sur l'etiquette. "
            "Le voisin qui a recu le colis refuse de me le remettre. J'ai contacte le bureau "
            "de poste de Grenoble Europole qui m'a confirme l'erreur de livraison. Le colis "
            "contenait du materiel de sport commande en ligne."
        ),
        "description_en": (
            "Package delivered to 12 rue des Lilas instead of 12 rue des Tilleuls in Grenoble. "
            "The postal carrier mixed up the streets despite the correct address on the label. "
            "The neighbor who received the package refuses to give it to me. I contacted the "
            "Grenoble Europole post office who confirmed the delivery error. The package "
            "contained sports equipment ordered online."
        ),
        "valeur": "125.00 EUR",
        "expediteur": "Decathlon",
        "destination": "Grenoble Centre",
    },
    {
        "filename": "reclamation_colis_perdu_002",
        "type": "colis_perdu",
        "numero_suivi": "6C891234567FR",
        "reclamation_number": "RECL-2025-0008",
        "client": "Nathalie Girard",
        "email": "n.girard@yahoo.fr",
        "telephone": "07 89 01 23 45",
        "date_envoi": "05/06/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis expedie depuis la Belgique (Bruxelles Centre). Le suivi s'arrete a la "
            "douane de Lille depuis 3 semaines avec le statut 'Dedouanement en cours'. "
            "Aucune information disponible malgre mes appels repetes. Le colis contenait "
            "des chocolats artisanaux belges et des produits de boulangerie fine. J'ai fourni "
            "tous les documents demandes pour le dedouanement sans resultat."
        ),
        "description_en": (
            "Package shipped from Belgium (Brussels Centre). Tracking stops at Lille customs "
            "for 3 weeks with status 'Customs clearance in progress'. No information available "
            "despite my repeated calls. The package contained artisanal Belgian chocolates and "
            "fine bakery products. I provided all documents requested for customs clearance "
            "with no result."
        ),
        "valeur": "340.00 EUR",
        "expediteur": "Chocolaterie belge (particulier)",
        "destination": "Lyon 3e",
    },
    {
        "filename": "reclamation_non_livre_002",
        "type": "non_livre",
        "numero_suivi": "6C912345678FR",
        "reclamation_number": "RECL-2025-0009",
        "client": "Laurent Petit",
        "email": "l.petit@outlook.fr",
        "telephone": "06 90 12 34 56",
        "date_envoi": "26/06/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Troisieme tentative de livraison echouee. Je suis en teletravail et personne ne "
            "sonne. La camera de surveillance ne montre aucun passage du facteur aux heures "
            "indiquees dans le suivi. Le bureau de poste m'indique que le colis sera mis en "
            "instance apres la 3eme tentative. J'ai pourtant un interphone fonctionnel et "
            "je suis toujours disponible en journee."
        ),
        "description_en": (
            "Third failed delivery attempt. I work from home and nobody rings the doorbell. "
            "Security camera shows no postal carrier visit at the times indicated in tracking. "
            "The post office tells me the package will be held after the 3rd attempt. I have "
            "a working intercom and am always available during the day."
        ),
        "valeur": "78.50 EUR",
        "expediteur": "Fnac.com",
        "destination": "Annecy Centre",
    },
    {
        "filename": "reclamation_retard_livraison_002",
        "type": "retard_livraison",
        "numero_suivi": "6C123456789FR",
        "reclamation_number": "RECL-2025-0010",
        "client": "Camille Roux",
        "email": "c.roux@gmail.com",
        "telephone": "07 01 23 45 67",
        "date_envoi": "30/06/2025",
        "date_reception": "03/07/2025",
        "description_fr": (
            "Colissimo express 24h envoye le lundi 30 juin depuis Aix-en-Provence, recu seulement "
            "le jeudi 3 juillet soit 3 jours de retard. Le suivi montre un blocage au centre "
            "de tri de Paris Gennevilliers pour 'surcharge plateforme'. Le contenu etait des "
            "chocolats artisanaux qui ont fondu pendant le transit prolonge en pleine canicule. "
            "Les chocolats sont arrives dans un etat inutilisable."
        ),
        "description_en": (
            "Colissimo express 24h shipped Monday June 30th from Aix-en-Provence, received only "
            "on Thursday July 3rd, 3 days late. Tracking shows a hold at Paris Gennevilliers "
            "sorting center for 'platform overload'. The content was artisanal chocolates that "
            "melted during the prolonged transit in the heat wave. The chocolates arrived in "
            "an unusable state."
        ),
        "valeur": "95.00 EUR",
        "expediteur": "Chocolaterie artisanale",
        "destination": "Tours Centre",
    },
    # 11-15: rejected
    {
        "filename": "reclamation_colis_endommage_003",
        "type": "colis_endommage",
        "numero_suivi": "6C111222333FR",
        "reclamation_number": "RECL-2025-0011",
        "client": "Gerard Fontaine",
        "email": "g.fontaine@wanadoo.fr",
        "telephone": "06 11 22 33 44",
        "date_envoi": "01/07/2025",
        "date_reception": "03/07/2025",
        "description_fr": (
            "Legere eraflure sur le carton d'emballage exterieur. Le contenu (vetements) "
            "est intact et en parfait etat. Je souhaite neanmoins etre indemnise pour le "
            "dommage cause a l'emballage qui presentait une marque de frottement sur un coin."
        ),
        "description_en": (
            "Slight scuff on the outer packaging box. The contents (clothing) are intact and "
            "in perfect condition. I would nevertheless like to be compensated for the damage "
            "to the packaging which had a friction mark on one corner."
        ),
        "valeur": "29.90 EUR",
        "expediteur": "Zalando",
        "destination": "Perpignan Centre",
    },
    {
        "filename": "reclamation_retard_livraison_003",
        "type": "retard_livraison",
        "numero_suivi": "6C222333444FR",
        "reclamation_number": "RECL-2025-0012",
        "client": "Monique Duval",
        "email": "m.duval@free.fr",
        "telephone": "07 22 33 44 55",
        "date_envoi": "02/07/2025",
        "date_reception": "05/07/2025",
        "description_fr": (
            "Colis livre avec 1 jour de retard sur la date estimee. Pas de prejudice "
            "particulier, mais c'est le principe. Le service devrait respecter ses engagements."
        ),
        "description_en": (
            "Package delivered 1 day late compared to the estimated date. No particular harm "
            "done, but it's the principle. The service should meet its commitments."
        ),
        "valeur": "15.00 EUR",
        "expediteur": "Particulier",
        "destination": "Caen Centre",
    },
    {
        "filename": "reclamation_colis_perdu_003",
        "type": "colis_perdu",
        "numero_suivi": "6C333444555FR",
        "reclamation_number": "RECL-2025-0013",
        "client": "Eric Leroy",
        "email": "e.leroy@gmail.com",
        "telephone": "06 33 44 55 66",
        "date_envoi": "03/07/2025",
        "date_reception": "05/07/2025",
        "description_fr": (
            "Je n'ai pas recu mon colis. EDIT: en fait il etait chez le gardien de mon "
            "immeuble, je ne l'avais pas vu. Desole pour le derangement."
        ),
        "description_en": (
            "I did not receive my package. EDIT: actually it was with the building concierge, "
            "I had not noticed. Sorry for the inconvenience."
        ),
        "valeur": "45.00 EUR",
        "expediteur": "Amazon",
        "destination": "Nancy Centre",
    },
    {
        "filename": "reclamation_non_livre_003",
        "type": "non_livre",
        "numero_suivi": "6C444555666FR",
        "reclamation_number": "RECL-2025-0014",
        "client": "Valerie Simon",
        "email": "v.simon@orange.fr",
        "telephone": "07 44 55 66 77",
        "date_envoi": "04/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis non livre. En verifiant, je me suis rendu compte que j'avais donne une "
            "mauvaise adresse lors de la commande. Le colis a ete retourne a l'expediteur."
        ),
        "description_en": (
            "Package not delivered. Upon checking, I realized I had given the wrong address "
            "when placing the order. The package was returned to sender."
        ),
        "valeur": "22.00 EUR",
        "expediteur": "Particulier",
        "destination": "Poitiers Centre",
    },
    {
        "filename": "reclamation_colis_endommage_004",
        "type": "colis_endommage",
        "numero_suivi": "6C555666777FR",
        "reclamation_number": "RECL-2025-0015",
        "client": "Thierry Lambert",
        "email": "t.lambert@laposte.net",
        "telephone": "06 55 66 77 88",
        "date_envoi": "10/05/2024",
        "date_reception": "12/05/2024",
        "description_fr": (
            "Reclamation pour colis endommage datant de 14 mois. Je viens seulement de "
            "m'en apercevoir en ouvrant le carton que j'avais stocke dans mon garage. "
            "Le contenu (outils de jardinage) est rouille."
        ),
        "description_en": (
            "Claim for damaged package dating back 14 months. I only just noticed when "
            "opening the box I had stored in my garage. The contents (gardening tools) "
            "are rusted."
        ),
        "valeur": "180.00 EUR",
        "expediteur": "Jardinerie en ligne",
        "destination": "Toulon Centre",
    },
    # 16-20: pending
    {
        "filename": "reclamation_colis_endommage_005",
        "type": "colis_endommage",
        "numero_suivi": "6C666777888FR",
        "reclamation_number": "RECL-2025-0016",
        "client": "Claire Rousseau",
        "email": "c.rousseau@gmail.com",
        "telephone": "06 66 77 88 99",
        "date_envoi": "05/07/2025",
        "date_reception": "08/07/2025",
        "description_fr": (
            "Recu un colis dont le contenu (appareil photo Canon EOS R6) est casse. "
            "L'objectif est fele et le boitier raye profondement. L'emballage exterieur "
            "montre des traces de chute. Le colis etait etiquete 'FRAGILE'. L'emballage "
            "interieur etait insuffisant (simple papier journal)."
        ),
        "description_en": (
            "Received a package with broken contents (Canon EOS R6 camera). The lens is "
            "cracked and the body deeply scratched. The outer packaging shows drop marks. "
            "The package was labeled 'FRAGILE'. The inner packaging was insufficient "
            "(simple newspaper)."
        ),
        "valeur": "499.00 EUR",
        "expediteur": "Vendeur particulier (LeBonCoin)",
        "destination": "Bordeaux Centre",
    },
    {
        "filename": "reclamation_colis_perdu_004",
        "type": "colis_perdu",
        "numero_suivi": "6C777888999FR",
        "reclamation_number": "RECL-2025-0017",
        "client": "David Mercier",
        "email": "d.mercier@hotmail.fr",
        "telephone": "07 77 88 99 00",
        "date_envoi": "05/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Envoi recommande avec AR contenant des documents administratifs importants "
            "(acte de naissance, carte d'identite, justificatifs de domicile). Perdu depuis "
            "le 5 juillet. Le suivi montre un dernier scan au centre de tri. Ces documents "
            "sont necessaires pour une procedure administrative urgente."
        ),
        "description_en": (
            "Registered letter with acknowledgment of receipt containing important administrative "
            "documents (birth certificate, ID card, proof of residence). Lost since July 5th. "
            "Tracking shows a last scan at the sorting center. These documents are needed for "
            "an urgent administrative procedure."
        ),
        "valeur": "50.00 EUR",
        "expediteur": "Particulier",
        "destination": "Paris 20e",
    },
    {
        "filename": "reclamation_vol_point_relais_002",
        "type": "vol_point_relais",
        "numero_suivi": "6C888999000FR",
        "reclamation_number": "RECL-2025-0018",
        "client": "Emilie Fournier",
        "email": "e.fournier@sfr.fr",
        "telephone": "06 88 99 00 11",
        "date_envoi": "06/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis depose en point relais (Relais Colis Boulangerie Martin, Lyon 3e). "
            "Quand je suis allee le chercher, on m'a dit qu'il avait deja ete retire par "
            "quelqu'un d'autre. Je n'ai autorise personne a le retirer. Le colis contenait "
            "un bijou fantaisie commande sur Etsy."
        ),
        "description_en": (
            "Package deposited at pickup point (Relais Colis Boulangerie Martin, Lyon 3rd). "
            "When I went to collect it, I was told it had already been picked up by someone "
            "else. I did not authorize anyone to collect it. The package contained a fashion "
            "jewelry item ordered on Etsy."
        ),
        "valeur": "156.50 EUR",
        "expediteur": "Vendeur Etsy",
        "destination": "Lyon 3e (point relais)",
    },
    {
        "filename": "reclamation_mauvaise_adresse_002",
        "type": "mauvaise_adresse",
        "numero_suivi": "6C999000111FR",
        "reclamation_number": "RECL-2025-0019",
        "client": "Nicolas Bonnet",
        "email": "n.bonnet@outlook.fr",
        "telephone": "07 99 00 11 22",
        "date_envoi": "07/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Mon colis a ete livre a mon ancienne adresse malgre un changement d'adresse "
            "effectue il y a 2 mois aupres de La Poste (service reexpedition definitive). "
            "Mon ancien voisin a refuse de me transmettre le colis. Le service de reexpedition "
            "ne semble pas fonctionner pour les colis Colissimo."
        ),
        "description_en": (
            "My package was delivered to my old address despite an address change made 2 months "
            "ago with La Poste (permanent forwarding service). My former neighbor refused to "
            "forward the package to me. The forwarding service does not seem to work for "
            "Colissimo packages."
        ),
        "valeur": "88.00 EUR",
        "expediteur": "CDiscount",
        "destination": "Nantes Centre",
    },
    {
        "filename": "reclamation_retard_livraison_004",
        "type": "retard_livraison",
        "numero_suivi": "6C000111222FR",
        "reclamation_number": "RECL-2025-0020",
        "client": "Audrey Blanc",
        "email": "a.blanc@gmail.com",
        "telephone": "06 00 11 22 33",
        "date_envoi": "02/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Commande passee il y a 10 jours en Colissimo 48h. Le suivi est bloque sur "
            "'en cours de traitement' depuis le depart du colis. Aucune mise a jour en 10 jours. "
            "Le vendeur confirme avoir expedie le colis et fourni le numero de suivi. "
            "Je souhaite savoir ou se trouve mon colis."
        ),
        "description_en": (
            "Order placed 10 days ago via Colissimo 48h. Tracking is stuck on 'processing' "
            "since the package departed. No update in 10 days. The seller confirms having "
            "shipped the package and provided the tracking number. I want to know where "
            "my package is."
        ),
        "valeur": "42.00 EUR",
        "expediteur": "Vendeur en ligne",
        "destination": "Toulouse Centre",
    },
    # 21-25: processing
    {
        "filename": "reclamation_colis_endommage_006",
        "type": "colis_endommage",
        "numero_suivi": "6C101112131FR",
        "reclamation_number": "RECL-2025-0021",
        "client": "Philippe Garnier",
        "email": "p.garnier@free.fr",
        "telephone": "06 10 11 12 13",
        "date_envoi": "08/07/2025",
        "date_reception": "10/07/2025",
        "description_fr": (
            "Colis contenant une guitare classique Yamaha C40. Le manche est casse net. "
            "L'emballage exterieur presente des traces evidentes de mauvaise manipulation "
            "(choc violent sur le cote). L'etiquette 'FRAGILE' a ete ignoree. La guitare "
            "etait correctement emballee avec du polystyrene par l'expediteur."
        ),
        "description_en": (
            "Package containing a Yamaha C40 classical guitar. The neck is cleanly broken. "
            "The outer packaging shows obvious signs of mishandling (violent impact on the "
            "side). The 'FRAGILE' label was ignored. The guitar was properly packed with "
            "polystyrene by the sender."
        ),
        "valeur": "350.00 EUR",
        "expediteur": "Woodbrass.com",
        "destination": "Marseille 8e",
    },
    {
        "filename": "reclamation_non_livre_004",
        "type": "non_livre",
        "numero_suivi": "6C121314151FR",
        "reclamation_number": "RECL-2025-0022",
        "client": "Sandrine Chevalier",
        "email": "s.chevalier@yahoo.fr",
        "telephone": "07 12 13 14 15",
        "date_envoi": "05/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis marque comme livre le 9 juillet, mais je n'ai rien recu. Pas d'avis de "
            "passage, rien dans la boite aux lettres, rien chez les voisins. Le suivi indique "
            "'Distribue' sans signature. J'habite dans un immeuble securise avec code d'acces."
        ),
        "description_en": (
            "Package marked as delivered on July 9th, but I received nothing. No delivery "
            "notice, nothing in the mailbox, nothing with neighbors. Tracking shows "
            "'Delivered' without signature. I live in a secure building with access code."
        ),
        "valeur": "76.00 EUR",
        "expediteur": "Cultura.com",
        "destination": "Nice Centre",
    },
    {
        "filename": "reclamation_colis_perdu_005",
        "type": "colis_perdu",
        "numero_suivi": "6C131415161FR",
        "reclamation_number": "RECL-2025-0023",
        "client": "Julien Morel",
        "email": "j.morel@laposte.net",
        "telephone": "06 13 14 15 16",
        "date_envoi": "01/06/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis international (Japon -> France) bloque en douane depuis plus d'un mois. "
            "Aucune mise a jour du suivi. Le colis contenait des figurines de collection "
            "et du materiel de calligraphie japonaise. J'ai fourni tous les documents "
            "douaniers demandes (facture, description du contenu)."
        ),
        "description_en": (
            "International package (Japan -> France) stuck in customs for over a month. "
            "No tracking update. The package contained collectible figurines and Japanese "
            "calligraphy materials. I provided all requested customs documents (invoice, "
            "content description)."
        ),
        "valeur": "420.00 EUR",
        "expediteur": "Boutique japonaise",
        "destination": "Paris 13e",
    },
    {
        "filename": "reclamation_retard_livraison_005",
        "type": "retard_livraison",
        "numero_suivi": "6C141516171FR",
        "reclamation_number": "RECL-2025-0024",
        "client": "Veronique Blanc",
        "email": "ve.blanc@orange.fr",
        "telephone": "07 14 15 16 17",
        "date_envoi": "07/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis Chronopost (sous-traite par La Poste) en retard de 5 jours. Contenu: "
            "medicaments veterinaires urgents pour mon chien malade. Le veterinaire avait "
            "prescrit un traitement a commencer immediatement. J'ai du me rendre chez un "
            "veterinaire local pour obtenir un traitement de remplacement en urgence."
        ),
        "description_en": (
            "Chronopost package (subcontracted by La Poste) 5 days late. Contents: urgent "
            "veterinary medication for my sick dog. The vet had prescribed a treatment to "
            "start immediately. I had to visit a local vet to get emergency replacement "
            "treatment."
        ),
        "valeur": "210.00 EUR",
        "expediteur": "Pharmacie veterinaire en ligne",
        "destination": "Lille Centre",
    },
    {
        "filename": "reclamation_vol_point_relais_003",
        "type": "vol_point_relais",
        "numero_suivi": "6C151617181FR",
        "reclamation_number": "RECL-2025-0025",
        "client": "Remi Faure",
        "email": "r.faure@gmail.com",
        "telephone": "06 15 16 17 18",
        "date_envoi": "08/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis recupere par une personne non autorisee au point relais. Le commercant "
            "dit avoir verifie la piece d'identite mais le nom ne correspond pas au mien. "
            "Comment une personne avec un nom different a-t-elle pu retirer mon colis? "
            "Le colis contenait des ecouteurs sans fil haut de gamme."
        ),
        "description_en": (
            "Package collected by an unauthorized person at the pickup point. The shopkeeper "
            "claims to have checked the ID but the name does not match mine. How could a "
            "person with a different name collect my package? The package contained "
            "high-end wireless earbuds."
        ),
        "valeur": "299.00 EUR",
        "expediteur": "Boulanger.com",
        "destination": "Toulouse (point relais)",
    },
    # 26-28: manual_review
    {
        "filename": "reclamation_colis_endommage_007",
        "type": "colis_endommage",
        "numero_suivi": "6C161718191FR",
        "reclamation_number": "RECL-2025-0026",
        "client": "Helene Picard",
        "email": "h.picard@sfr.fr",
        "telephone": "07 16 17 18 19",
        "date_envoi": "09/07/2025",
        "date_reception": "11/07/2025",
        "description_fr": (
            "Colis contenant du materiel informatique (carte graphique RTX 4090). Le produit "
            "ne fonctionne plus apres livraison. L'emballage exterieur ne presente pas de "
            "dommages visibles mais l'emballage d'origine du produit semble avoir ete "
            "insuffisant. Impossible de determiner si le dommage est du au transport ou "
            "a un defaut d'emballage de l'expediteur."
        ),
        "description_en": (
            "Package containing computer hardware (RTX 4090 graphics card). The product no "
            "longer works after delivery. The outer packaging shows no visible damage but "
            "the product's original packaging seems to have been insufficient. Unable to "
            "determine if the damage is due to transport or the sender's packaging defect."
        ),
        "valeur": "500.00 EUR",
        "expediteur": "Vendeur LDLC Marketplace",
        "destination": "Strasbourg Centre",
    },
    {
        "filename": "reclamation_colis_perdu_006",
        "type": "colis_perdu",
        "numero_suivi": "6C171819202FR",
        "reclamation_number": "RECL-2025-0027",
        "client": "Yannick Lemaire",
        "email": "y.lemaire@hotmail.fr",
        "telephone": "06 17 18 19 20",
        "date_envoi": "10/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Envoi de bijoux de valeur (bague en or 18 carats). Le suivi montre une "
            "livraison mais je n'ai rien recu. C'est ma troisieme reclamation similaire "
            "en 6 mois pour des colis de valeur. J'ai depose une main courante au "
            "commissariat. Les deux precedentes reclamations ont ete indemnisees."
        ),
        "description_en": (
            "Shipment of valuable jewelry (18-karat gold ring). Tracking shows delivery but "
            "I received nothing. This is my third similar claim in 6 months for valuable "
            "packages. I filed a report at the police station. The two previous claims "
            "were compensated."
        ),
        "valeur": "480.00 EUR",
        "expediteur": "Bijouterie en ligne",
        "destination": "Paris 16e",
    },
    {
        "filename": "reclamation_mauvaise_adresse_003",
        "type": "mauvaise_adresse",
        "numero_suivi": "6C181920213FR",
        "reclamation_number": "RECL-2025-0028",
        "client": "Stephanie Vincent",
        "email": "s.vincent@gmail.com",
        "telephone": "07 18 19 20 21",
        "date_envoi": "10/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Le colis a ete livre a un homonyme habitant dans la meme rue. Le destinataire "
            "refuse de restituer le colis car il pense que c'est le sien. Situation complexe: "
            "meme nom de famille, meme rue, numeros proches (14 et 14 bis). Le bureau de "
            "poste est au courant mais n'a pas pu intervenir."
        ),
        "description_en": (
            "The package was delivered to a person with the same name living on the same "
            "street. The recipient refuses to return the package because they think it's "
            "theirs. Complex situation: same last name, same street, close numbers (14 and "
            "14 bis). The post office is aware but could not intervene."
        ),
        "valeur": "175.00 EUR",
        "expediteur": "Zara.com",
        "destination": "Montpellier Centre",
    },
    # 29-30: escalated
    {
        "filename": "reclamation_vol_point_relais_004",
        "type": "vol_point_relais",
        "numero_suivi": "6C192021224FR",
        "reclamation_number": "RECL-2025-0029",
        "client": "Marc-Antoine Dupuis",
        "email": "ma.dupuis@orange.fr",
        "telephone": "06 19 20 21 22",
        "date_envoi": "09/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Vol organise au point relais: 3 colis de clients differents ont disparu le meme "
            "jour. Le commercant est soupconne de complicite. Une plainte a ete deposee au "
            "commissariat (PV-2025-07890). D'autres clients ont signale le meme probleme "
            "sur les reseaux sociaux. Le point relais a ete desactive depuis."
        ),
        "description_en": (
            "Organized theft at the pickup point: 3 packages from different customers "
            "disappeared on the same day. The shopkeeper is suspected of complicity. A police "
            "report was filed (PV-2025-07890). Other customers reported the same issue on "
            "social media. The pickup point has since been deactivated."
        ),
        "valeur": "450.00 EUR",
        "expediteur": "Samsung.com",
        "destination": "Lyon 7e (point relais)",
    },
    {
        "filename": "reclamation_colis_perdu_007",
        "type": "colis_perdu",
        "numero_suivi": "6C202122235FR",
        "reclamation_number": "RECL-2025-0030",
        "client": "Christine Delorme",
        "email": "c.delorme@free.fr",
        "telephone": "07 20 21 22 23",
        "date_envoi": "01/07/2025",
        "date_reception": "N/A",
        "description_fr": (
            "Colis contenant un tableau de valeur (oeuvre d'art originale d'un artiste "
            "contemporain). Disparu depuis 3 semaines. Assurance ad valorem souscrite a "
            "hauteur de 2 500 EUR. Litige avec l'assureur sur le montant d'indemnisation: "
            "l'assureur propose 500 EUR alors que l'oeuvre est estimee a 2 500 EUR par un "
            "expert. Expertise independante en cours."
        ),
        "description_en": (
            "Package containing a valuable painting (original artwork by a contemporary "
            "artist). Missing for 3 weeks. Ad valorem insurance taken out for 2,500 EUR. "
            "Dispute with the insurer over the compensation amount: the insurer offers "
            "500 EUR while the work is valued at 2,500 EUR by an expert. Independent "
            "appraisal in progress."
        ),
        "valeur": "500.00 EUR (declare), 2 500.00 EUR (estime)",
        "expediteur": "Galerie d'art",
        "destination": "Paris 6e",
    },
]

# ============================================================================
# Type labels for header
# ============================================================================
TYPE_LABELS_FR = {
    "colis_endommage": "COLIS ENDOMMAGE",
    "colis_perdu": "COLIS PERDU",
    "non_livre": "NON LIVRE",
    "mauvaise_adresse": "MAUVAISE ADRESSE",
    "vol_point_relais": "VOL EN POINT RELAIS",
    "retard_livraison": "RETARD DE LIVRAISON",
}

TYPE_LABELS_EN = {
    "colis_endommage": "DAMAGED PACKAGE",
    "colis_perdu": "LOST PACKAGE",
    "non_livre": "NOT DELIVERED",
    "mauvaise_adresse": "WRONG ADDRESS",
    "vol_point_relais": "THEFT AT PICKUP POINT",
    "retard_livraison": "DELIVERY DELAY",
}


def generate_reclamation_pdf(scenario: dict, lang: str, output_dir: str):
    """Generate a single reclamation PDF (FR or EN)."""
    suffix = "_en" if lang == "en" else ""
    filename = f"{scenario['filename']}{suffix}.pdf"
    filepath = os.path.join(output_dir, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # Header
    y = height - 2 * cm

    if lang == "fr":
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, y, "LA POSTE - RECLAMATION")
        y -= 0.6 * cm
        c.setFont("Helvetica", 8)
        c.drawString(2 * cm, y, "Service Consommateurs - 99999 LA POSTE")
        type_label = TYPE_LABELS_FR.get(scenario["type"], scenario["type"].upper())
    else:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, y, "LA POSTE - COMPLAINT FORM")
        y -= 0.6 * cm
        c.setFont("Helvetica", 8)
        c.drawString(2 * cm, y, "Customer Service - 99999 LA POSTE")
        type_label = TYPE_LABELS_EN.get(scenario["type"], scenario["type"].upper())

    # Horizontal line
    y -= 0.5 * cm
    c.setLineWidth(1)
    c.line(2 * cm, y, width - 2 * cm, y)

    # Reclamation type badge
    y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, type_label)

    # Reclamation number & tracking
    y -= 0.8 * cm
    c.setFont("Helvetica-Bold", 10)
    if lang == "fr":
        c.drawString(2 * cm, y, f"N de reclamation: {scenario['reclamation_number']}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"N de suivi: {scenario['numero_suivi']}")
    else:
        c.drawString(2 * cm, y, f"Claim number: {scenario['reclamation_number']}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Tracking number: {scenario['numero_suivi']}")

    # Client info section
    y -= 1 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "INFORMATIONS CLIENT" if lang == "fr" else "CLIENT INFORMATION")
    y -= 0.3 * cm
    c.setLineWidth(0.5)
    c.line(2 * cm, y, width - 2 * cm, y)

    y -= 0.6 * cm
    c.setFont("Helvetica", 9)
    fields = [
        ("Nom / Name", scenario["client"]),
        ("Email", scenario["email"]),
        ("Telephone / Phone", scenario["telephone"]),
    ]
    for label, value in fields:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2 * cm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(6.5 * cm, y, value)
        y -= 0.5 * cm

    # Shipment info section
    y -= 0.6 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "DETAILS DE L'ENVOI" if lang == "fr" else "SHIPMENT DETAILS")
    y -= 0.3 * cm
    c.line(2 * cm, y, width - 2 * cm, y)

    y -= 0.6 * cm
    c.setFont("Helvetica", 9)
    date_label = "Date d'envoi" if lang == "fr" else "Shipping date"
    recv_label = "Date de reception" if lang == "fr" else "Delivery date"
    from_label = "Expediteur" if lang == "fr" else "Sender"
    to_label = "Destination" if lang == "fr" else "Destination"
    val_label = "Valeur declaree" if lang == "fr" else "Declared value"

    ship_fields = [
        (date_label, scenario["date_envoi"]),
        (recv_label, scenario["date_reception"]),
        (from_label, scenario["expediteur"]),
        (to_label, scenario["destination"]),
        (val_label, scenario["valeur"]),
    ]
    for label, value in ship_fields:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2 * cm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(6.5 * cm, y, value)
        y -= 0.5 * cm

    # Description section
    y -= 0.6 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "DESCRIPTION DU PROBLEME" if lang == "fr" else "PROBLEM DESCRIPTION")
    y -= 0.3 * cm
    c.line(2 * cm, y, width - 2 * cm, y)

    y -= 0.6 * cm
    c.setFont("Helvetica", 9)
    desc = scenario["description_fr"] if lang == "fr" else scenario["description_en"]

    # Word wrap the description
    max_width = width - 4 * cm
    words = desc.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if c.stringWidth(test_line, "Helvetica", 9) < max_width:
            line = test_line
        else:
            c.drawString(2 * cm, y, line)
            y -= 0.4 * cm
            line = word
            if y < 3 * cm:
                c.showPage()
                y = height - 2 * cm
    if line:
        c.drawString(2 * cm, y, line)
        y -= 0.4 * cm

    # Signature section
    y -= 1.5 * cm
    if y < 5 * cm:
        c.showPage()
        y = height - 2 * cm

    c.setFont("Helvetica-Bold", 10)
    if lang == "fr":
        c.drawString(2 * cm, y, "DEMANDE DU CLIENT")
        y -= 0.3 * cm
        c.line(2 * cm, y, width - 2 * cm, y)
        y -= 0.6 * cm
        c.setFont("Helvetica", 9)
        demands = {
            "colis_endommage": "Remboursement de la valeur declaree du contenu endommage.",
            "colis_perdu": "Remboursement de la valeur declaree du colis perdu.",
            "non_livre": "Nouvelle livraison ou remboursement integral.",
            "mauvaise_adresse": "Reexpedition du colis a l'adresse correcte.",
            "vol_point_relais": "Remboursement de la valeur declaree du colis vole.",
            "retard_livraison": "Remboursement des frais d'expedition et indemnite de retard.",
        }
        c.drawString(2 * cm, y, demands.get(scenario["type"], "Indemnisation."))
    else:
        c.drawString(2 * cm, y, "CLIENT REQUEST")
        y -= 0.3 * cm
        c.line(2 * cm, y, width - 2 * cm, y)
        y -= 0.6 * cm
        c.setFont("Helvetica", 9)
        demands_en = {
            "colis_endommage": "Reimbursement of the declared value of the damaged contents.",
            "colis_perdu": "Reimbursement of the declared value of the lost package.",
            "non_livre": "New delivery or full refund.",
            "mauvaise_adresse": "Re-shipment of the package to the correct address.",
            "vol_point_relais": "Reimbursement of the declared value of the stolen package.",
            "retard_livraison": "Refund of shipping costs and delay compensation.",
        }
        c.drawString(2 * cm, y, demands_en.get(scenario["type"], "Compensation."))

    # Date and signature
    y -= 1.5 * cm
    c.setFont("Helvetica", 9)
    if lang == "fr":
        c.drawString(2 * cm, y, f"Fait le: {scenario['date_envoi']}")
    else:
        c.drawString(2 * cm, y, f"Date: {scenario['date_envoi']}")

    y -= 0.8 * cm
    c.drawString(2 * cm, y, f"Signature: {scenario['client']}")

    # Footer
    c.setFont("Helvetica", 7)
    if lang == "fr":
        c.drawString(2 * cm, 1.5 * cm,
                      "Document genere automatiquement - La Poste - Service Reclamations")
        c.drawString(2 * cm, 1 * cm,
                      "Delai de traitement: 21 jours maximum. Conservez ce document.")
    else:
        c.drawString(2 * cm, 1.5 * cm,
                      "Automatically generated document - La Poste - Claims Service")
        c.drawString(2 * cm, 1 * cm,
                      "Processing time: 21 days maximum. Keep this document.")

    c.save()
    return filepath


def main():
    # Output directory
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "documents", "reclamations"
    )
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating reclamation PDFs in {output_dir}")

    fr_count = 0
    en_count = 0

    for scenario in SCENARIOS:
        # Generate FR version
        path_fr = generate_reclamation_pdf(scenario, "fr", output_dir)
        fr_count += 1
        print(f"  FR: {os.path.basename(path_fr)}")

        # Generate EN version
        path_en = generate_reclamation_pdf(scenario, "en", output_dir)
        en_count += 1
        print(f"  EN: {os.path.basename(path_en)}")

    print(f"\nDone! Generated {fr_count} FR + {en_count} EN = {fr_count + en_count} PDFs")


if __name__ == "__main__":
    main()
