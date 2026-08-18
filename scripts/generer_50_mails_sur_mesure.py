#!/usr/bin/env python3
"""
generer_50_mails_sur_mesure.py — Génération de 50 emails uniques, ultra-personnalisés par client
pour l'écosystème Grands Comptes et Région Toulousaine.
"""

import os
import json
import sqlite3
import datetime

OUTPUT_DIR = "/home/pamerys/Bureau/prospection_grands_comptes/emails_personnalises"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MASTER_DB = os.path.expanduser("~/jarvis/jarvis_master.db")
PLAQUETTE_PDF = "/home/pamerys/Bureau/prospection_grands_comptes/PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf"
CV_PDF = "/home/pamerys/Bureau/prospection_grands_comptes/CV_Franck_Delmas_AI_Architect.pdf"

TARGETS_DATA = [
    # 1-15: Aéro, Spatial, Défense
    ("Airbus Commercial", "DSI Aéronautique", "Aéronautique", "Pack Enterprise (75 000 €)",
     "Protection des données avioniques & calculs d'assemblage",
     "Vos équipes gèrent des millions de paramètres avioniques et de manuels de maintenance sans pouvoir exposer ces données au Cloud US. JARVIS OS déploie un cluster local on-premise capable d'auditer et d'orchestrer vos documentations en mode avion complet."),
    
    ("Airbus Defence & Space", "Head of AI Infrastructure", "Spatial & Défense", "Pack Enterprise (75 000 €)",
     "Souveraineté spatiale & télémesures confidentielles",
     "Face aux exigences de secret de défense et d'étanchéité totale, JARVIS OS apporte un Board d'experts IA opérant à 100% sur vos serveurs internes sécurisés."),

    ("Thales Alenia Space", "Directeur Systèmes Critiques", "Spatial", "Pack Enterprise (75 000 €)",
     "Ingénierie des charges utiles & 0-Token",
     "Nous éliminons les risques d'exfiltration sur vos programmes spatiaux tout en divisant vos temps de revue technique par 10 grâce à notre moteur de citation stricte."),

    ("CNES Toulouse", "DSI & Données Spatiales", "Spatial / État", "Pack Enterprise (75 000 €)",
     "Valorisation de la recherche spatiale française",
     "Une appliance IA souveraine installée à Toulouse Rangueil pour traiter vos archives scientifiques et techniques sans dépendre des infrastructures cloud américaines."),

    ("Safran Nacelles", "Direction Ingénierie Souveraine", "Aéronautique", "Pack Enterprise (75 000 €)",
     "Protection de la Propriété Industrielle & brevets propulsion",
     "Vos plans et brevets sur les nacelles et inverseurs restent dans vos murs. JARVIS OS analyse vos flux documentaires en coût marginal nul."),

    ("Safran Electrical & Power", "Direction R&D", "Aéronautique", "Pack Enterprise (75 000 €)",
     "Câblages critiques & certification aéronautique",
     "Automatisez la validation des dossiers de certification avec la garantie formelle de citation [n] sans aucune hallucination probabiliste."),

    ("ATR Aircraft", "Direction Transformation Digitale", "Aéronautique", "Pack Enterprise (75 000 €)",
     "Gestion de flotte & manuels de vol en circuit fermé",
     "Une IA locale clé en main pour interroger instantanément toute la documentation technique des avions régionaux sans risque de fuite."),

    ("Liebherr-Aerospace Toulouse", "Directeur Systèmes Embarqués", "Aéro / Systèmes", "Pack Enterprise (75 000 €)",
     "Systèmes d'air & commandes de vol",
     "Traitement étanche de vos spécifications et exigences système pour garantir le secret industriel face à la concurrence mondiale."),

    ("Latécoère", "Direction Innovation & R&D", "Aéronautique", "Pack Enterprise (75 000 €)",
     "Systèmes d'interconnexion & portes d'avions",
     "Accélérez les cycles de réponse aux appels d'offres aéronautiques avec un état-major d'agents experts dédié à votre bureau d'études."),

    ("Stelia Aerospace / Premium AEROTEC", "DSI Bureau d'Études", "Aéronautique", "Pack Enterprise (75 000 €)",
     "Aérostructures complexes & calculs éléments finis",
     "Ingestion locale de vos historiques de calculs et rapports de test sans abonnement récurrent."),

    ("Hemeria / KalySphere", "Direction Nanosatellites", "Spatial / Défense", "Pack Enterprise (75 000 €)",
     "Constellations souveraines & data defense",
     "L'agilité d'un OS multi-agents pour traiter vos télémesures et données critiques en local."),

    ("Aura Aéro", "Direction Technique Avions Décarbonés", "Aéro Innovation", "Pack Enterprise (75 000 €)",
     "Conception avion électrique & bureau d'études innovant",
     "Une appliance IA plug & play qui booste l'ingénierie de vos prototypes ERA et Integral sans dépendre des API cloud."),

    ("Naval Group", "DSI Systèmes Navals Critiques", "Défense", "Pack Enterprise (75 000 €)",
     "Sous-marins & frégates - Données Secret Défense",
     "Un système d'exploitation IA 100% hors-ligne déployable en environnement hautement confiné ou embarqué."),

    ("Dassault Aviation", "Direction IA Souveraine & Rafale/Falcon", "Défense / Aéro", "Pack Enterprise (75 000 €)",
     "Secret de fabrication & programmes souverains",
     "Garantissez la non-ingérence étrangère sur vos données stratégiques grâce à nos clusters locaux quantifiés."),

    ("MBDA France", "Direction Systèmes de Missile", "Défense", "Pack Enterprise (75 000 €)",
     "Systèmes d'armes & conformité militaire stricte",
     "Une infrastructure IA locale fermée, auditable et sans dépendance externe."),

    # 16-25: Santé, Pharma, Biotech
    ("Laboratoires Pierre Fabre", "DSI Groupe & Données Santé", "Santé / Pharma", "Pack Enterprise (75 000 €)",
     "Conformité HDS & formulations dermo-cosmétiques",
     "Protégez vos formules exclusives et dossiers réglementaires avec une IA locale respectant strictement le secret de fabrication."),

    ("Sanofi France", "Direction Données Cliniques & R&D", "Pharma", "Pack Enterprise (75 000 €)",
     "Essais cliniques & secret de recherche thérapeutique",
     "Analysez des milliers d'essais cliniques avec citation exacte des molécules sans exposition des brevets."),

    ("Servier", "Directeur Conformité & RAG Local", "Pharma", "Pack Enterprise (75 000 €)",
     "Pharmacovigilance & conformité réglementaire",
     "Une délibération multi-experts locale pour croiser les retours de pharmacovigilance en toute sécurité."),

    ("Evotec France", "Direction Recherche Oncopole", "Biotech / Santé", "Pack Enterprise (75 000 €)",
     "Screening moléculaire & recherche translationnelle",
     "Une station GPU dédiée sur votre site de l'Oncopole pour accélérer l'analyse de littérature scientifique."),

    ("CHU de Toulouse", "DSI & Dossiers Médicaux", "Santé Publique", "Pack Enterprise (75 000 €)",
     "Confidentialité patient & valorisation des données hospitalières",
     "Un système IA on-premise garantissant qu'aucune donnée de santé ne quitte le réseau de l'hôpital."),

    ("IUCT Oncopole", "Direction Data Cancérologie", "Santé Recherche", "Pack Enterprise (75 000 €)",
     "Cancérologie & recherche clinique avancée",
     "Synthétisez les publications internationales et cas complexes avec contrôle anti-hallucination formel."),

    ("GTP Bioways", "R&D Bioproduction", "Biotech", "Pack Enterprise (75 000 €)",
     "Bioprocédés & culture cellulaire",
     "Sécurisez vos protocoles de bioproduction sur une infrastructure privée 0-token."),

    ("BioMérieux", "Direction Systèmes Diagnostics", "Santé / Diagnostic", "Pack Enterprise (75 000 €)",
     "Microbiologie & diagnostic in vitro",
     "Ingestion sécurisée des données de diagnostic avec garantie de traçabilité des sources."),

    ("Guerbet", "Direction Imagerie Médicale & IA", "Santé / Pharma", "Pack Enterprise (75 000 €)",
     "Produits de contraste & imagerie IA",
     "Un état-major IA privé pour auditer les protocoles d'imagerie sans transfert externe."),

    ("Ipsen", "Directeur Transformation Digitale", "Pharma", "Pack Enterprise (75 000 €)",
     "Médecine de spécialité & oncologie",
     "Déployez un actif IA amorti au bilan pour éliminer la dépendance aux abonnements cloud."),

    # 26-35: Finance, M&A, Fonds & Juridique
    ("Rothschild & Co", "Associé M&A / Due Diligence", "Finance M&A", "Pack Executive (29 000 €)",
     "Audit de Data Rooms en mode avion en 10 minutes",
     "Épluchez 5 000 pages de contrats et bilans avec citation exacte [n] de chaque clause sans risquer votre responsabilité professionnelle."),

    ("Lazard Frères", "Partner M&A", "Finance M&A", "Pack Executive (29 000 €)",
     "Due diligence M&A confidentielle",
     "Une appliance dédiée pour auditer les opérations de cession sans aucune transmission vers le Cloud US."),

    ("MBA Capital Toulouse", "Associés Fusions-Acquisitions", "Finance M&A", "Pack Executive (29 000 €)",
     "Transmission d'ETI en Occitanie",
     "Offrez à vos clients régionaux la garantie que leurs chiffres stratégiques ne quittent jamais la pièce lors des audits."),

    ("In Extenso Finance", "Direction M&A Régionale", "Finance M&A", "Pack Executive (29 000 €)",
     "Évaluation d'entreprises & transmission PME",
     "Détectez immédiatement les clauses de passif et litiges cachés dans les data rooms volumineuses."),

    ("Eurallia Finance", "Associés Cession ETI", "Finance M&A", "Pack Executive (29 000 €)",
     "Mandats d'acquisition & secret des affaires",
     "Un Board IA privé sur votre bureau pour arbitrer les valorisations et montages financiers."),

    ("IRDI Capital Investissement", "Directeur des Participations", "Capital Risque", "Pack Executive (29 000 €)",
     "Audit des participations régionales",
     "Auditez instantanément le reporting et la santé financière de vos 100+ participations en portefeuille."),

    ("Midi 2i / Caisse d'Épargne", "Direction Investissements", "Banque & Finance", "Pack Executive (29 000 €)",
     "Conformité bancaire & private equity",
     "Analysez les risques de vos investissements régionaux sur une infrastructure 100% privée."),

    ("Bredin Prat", "Associés Avocats d'Affaires M&A", "Juridique", "Pack Executive (29 000 €)",
     "Secret professionnel absolu & contentieux complexes",
     "Révisez vos pactes d'actionnaires et contrats commerciaux avec une garantie mathématique anti-hallucination."),

    ("Darrois Villey Maillot Brochier", "Associés Droit des Affaires", "Juridique", "Pack Executive (29 000 €)",
     "Grandes opérations M&A & arbitrage",
     "Un outil d'analyse contractuelle hors-ligne pour préserver l'inviolabilité de vos dossiers clients."),

    ("Barreau de Toulouse (Pôle Affaires)", "Avocats Conseil d'Entreprise", "Juridique", "Pack Executive (29 000 €)",
     "Déontologie & souveraineté juridique",
     "Une solution locale pour les cabinets d'avocats toulousains, garantissant le respect de l'art. 66-5 sur le secret professionnel."),

    # 36-45: ESN, Intégrateurs & Conseil IT
    ("Capgemini France", "Directeur Alliances Stratégiques IA", "ESN / IT", "Cession Licence & Source (190 000 €)",
     "Distribution en Marque Blanche & Déploiement Grands Comptes",
     "Intégrez JARVIS OS à votre catalogue de solutions souveraines et déployez chez vos clients donneurs d'ordres."),

    ("Sopra Steria", "Direction Défense & Aéro", "ESN / IT", "Cession Licence & Source (190 000 €)",
     "Intégration d'appliances souveraines chez les donneurs d'ordres",
     "Acquérez la licence complète du code source pour bâtir vos offres IA étanches sur les secteurs Aéro & Défense."),

    ("Akkodis / Altran", "Directeur Systèmes Autonomes", "ESN / IT", "Cession Licence & Source (190 000 €)",
     "Ingénierie embarquée & agents locaux",
     "Déployez notre réseau multi-agents chez vos clients industriels de la région toulousaine."),

    ("CS Group", "Directeur Systèmes Souverains", "ESN / IT", "Cession Licence & Source (190 000 €)",
     "Conformité NIS2 & cyberdéfense",
     "Une brique IA 100% française et autonome pour vos projets de sécurisation des infrastructures critiques."),

    ("Eviden / Atos", "Pôle HPC & Souveraineté", "ESN / IT", "Cession Licence & Source (190 000 €)",
     "Supercalculateurs & appliances dédiées",
     "Embarquez JARVIS OS sur vos clusters matériels pour fournir des appliances IA clé en main."),

    ("Inetum / GFI", "Pôle Secteur Public & Industrie", "ESN / IT", "Cession Licence & Source (190 000 €)",
     "Modernisation documentaire sans cloud",
     "Accompagnez le secteur public et les ETI vers l'autonomie numérique totale."),

    ("Alten", "Directeur Ingénierie & Solutions IA", "ESN / Conseil", "Cession Licence & Source (190 000 €)",
     "Accélération R&D chez les industriels",
     "Monétisez notre technologie auprès de vos clients grands comptes sans coûts de licences tierces."),

    ("Aubay", "Pôle Conseil Bancaire & Assurance", "ESN / Conseil", "Cession Licence & Source (190 000 €)",
     "Transformation bancaire sécurisée",
     "Proposez une solution de conformité documentaire et de tri intelligent des flux financiers."),

    ("Wavestone", "Direction Cybersécurité & IA", "Conseil / Audit", "Cession Licence & Source (190 000 €)",
     "Audit de sécurité IA & résilience NIS2",
     "Un cas d'usage concret d'IA privée et résiliente pour vos missions de conseil auprès des Comex."),

    ("Neurones", "Pôle Infrastructure & Cloud Privé", "ESN / Infra", "Cession Licence & Source (190 000 €)",
     "Hébergement on-premise & infogérance IA",
     "Ajoutez une offre d'IA souveraine opérée à votre catalogue d'infrastructures managées."),

    # 46-50: Industrie, Électronique & Systèmes Critiques
    ("Continental Automotive France", "Direction Systèmes Embarqués", "Industrie Auto", "Pack Enterprise (75 000 €)",
     "Véhicules connectés & secrets de fabrication",
     "Protégez vos algorithmes de conduite et données télématiques sur un cluster local fermé."),

    ("Vitesco Technologies", "R&D Électronique de Puissance", "Industrie Auto", "Pack Enterprise (75 000 €)",
     "Mobilité électrique & brevets semi-conducteurs",
     "Auditez vos dossiers de brevets et spécifications techniques sans risque d'espionnage industriel."),

    ("NXP Semiconductors", "Direction Sécurité Hardware", "Microélectronique", "Pack Enterprise (75 000 €)",
     "Microélectronique & cryptographie matérielle",
     "Une station IA souveraine pour assister vos ingénieurs de conception en toute confidentialité."),

    ("ACTIA Group", "Direction Télématique Industrielle", "Électronique", "Pack Enterprise (75 000 €)",
     "Électronique industrielle & diagnostic embarqué",
     "Ingestion complète de votre patrimoine technique avec déploiement sur site à Toulouse."),

    ("Schneider Electric", "Directeur Systèmes Industriels & IA", "Industrie Énergie", "Pack Enterprise (75 000 €)",
     "Gestion d'énergie & automatismes industriels",
     "Un Board IA souverain pour optimiser vos opérations industrielles critiques sans dépendance externe.")
]

print("==========================================================")
print("✍️ [GÉNÉRATEUR SUR-MESURE] CRÉATION DES 50 EMAILS UNIQUES")
print("==========================================================")

emails_manifest = []

for i, (ent, role, sec, off, hook, pitch) in enumerate(TARGETS_DATA, 1):
    safe_name = ent.lower().replace(" ", "_").replace("/", "_").replace("&", "et").replace("(", "").replace(")", "")
    filename = f"email_{i:02d}_{safe_name}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    email_content = f"""# 📧 EMAIL DE PROSPECTION STRATÉGIQUE #{i:02d}

**Destinataire :** {role} — {ent}  
**Secteur :** {sec}  
**Offre Clé en Main :** {off}  
**Pièces Jointes :** 
1. `PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf` (Plaquette Commerciale HD)
2. `CV_Franck_Delmas_AI_Architect.pdf` (CV Portfolio Concepteur)

---

### Objet :
**{ent} : Appliance IA 100% Souveraine & On-Premise ({hook})**

---

### Corps du Message :

Bonjour,

En tant que {role} chez **{ent}**, vous devez concilier l'accélération par l'intelligence artificielle et l'impératif absolu de **confidentialité des données stratégiques** (interdiction du Cloud US, secret des affaires, RGPD/NIS2).

{pitch}

Nous avons conçu et déployé **JARVIS OS**, un système d'exploitation IA souverain orchestrant un comité d'experts autonomes (Finance, Juridique, Technique, Ops) directement sur vos propres serveurs ou stations dédiées :

✅ **100% On-Premise & Hors-Ligne** : Vos données ne quittent JAMAIS vos locaux (fonctionnement certifié en 'mode avion').  
✅ **Zéro Hallucination Probabiliste** : Règle formelle de citation vérifiée [n] dans votre corpus documentaire (pas de source = pas de réponse).  
✅ **Acquisition d'Actif Pérenne (One-Shot)** : Investissement amorti dès le 6ᵉ mois sans aucune rente d'abonnements cloud récurrents.  
✅ **Déploiement et Support Direct sur Site** (proximité immédiate en région toulousaine / France).

📄 Je vous joins notre synthèse exécutive (**Plaquette JARVIS OS v2**) ainsi que mon profil (**CV Ingénieur & Architecte IA**).

Seriez-vous disponible pour une démonstration directe de 15 minutes en 'mode avion' sur un échantillon de vos cas d'usage réels ?

Bien à vous,

**Franc Delmas**  
*Ingénieur IA & Architecte Concepteur JARVIS OS*  
📍 Toulouse / Occitanie  
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(email_content)
        
    emails_manifest.append({
        "id": i,
        "entreprise": ent,
        "role": role,
        "file": filepath,
        "offre": off
    })
    print(f"  ✓ [{i:02d}/50] Email généré : {ent} -> {filename}")

# Sauvegarde du manifeste JSON
manifest_path = os.path.join(OUTPUT_DIR, "manifest_50_emails.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(emails_manifest, f, indent=2, ensure_ascii=False)

print("\n==========================================================")
print(f"✅ 50 EMAILS SUR-MESURE GÉNÉRÉS DANS : {OUTPUT_DIR}")
print(f"📁 Manifeste consolidé : {manifest_path}")
print("==========================================================")
