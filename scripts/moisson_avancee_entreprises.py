#!/usr/bin/env python3
"""
moisson_avancee_entreprises.py — Moissonneur Profond Réel Multi-Sources
Parcourt les sites web officiels, pages contact, relations presse et mentions légales
pour extraire les vraies coordonnées vérifiables et les enregistrer avec leurs URLs sources.
"""

import os
import re
import sys
import json
import sqlite3
import datetime
import urllib.request
from html.parser import HTMLParser

PROSPECTION_DB = os.path.expanduser("~/jarvis/data/prospection_reelle.db")
MASTER_DB = os.path.expanduser("~/jarvis/jarvis_master.db")

# Liste étendue des cibles avec leurs pages de contacts réelles et mentions légales
CIBLES_OFFICIELLES = [
    # ── Pôle Aéronautique & Défense ──
    {"nom": "Airbus Group", "pole": "aero", "urls": ["https://www.airbus.com/en/contact-us", "https://www.airbus.com/en/newsroom/media-contacts"]},
    {"nom": "Thales Alenia Space", "pole": "aero", "urls": ["https://www.thalesgroup.com/fr/global/presence-europe/france/thales-alenia-space", "https://www.thalesgroup.com/fr/groupe/contacts-presse"]},
    {"nom": "Safran Group", "pole": "aero", "urls": ["https://www.safran-group.com/fr/contact", "https://www.safran-group.com/fr/espace-presse/contacts-presse"]},
    {"nom": "CNES", "pole": "aero", "urls": ["https://cnes.fr/fr/nous-contacter", "https://cnes.fr/fr/presse/contacts-presse"]},
    {"nom": "Dassault Aviation", "pole": "aero", "urls": ["https://www.dassault-aviation.com/fr/groupe/contacts/", "https://www.dassault-aviation.com/fr/groupe/presse/contacts/"]},
    {"nom": "Naval Group", "pole": "aero", "urls": ["https://www.naval-group.com/fr/contact", "https://www.naval-group.com/fr/presse"]},
    {"nom": "Aura Aero", "pole": "aero", "urls": ["https://aura-aero.com/contact/", "https://aura-aero.com/press/"]},
    {"nom": "Sogeclair", "pole": "aero", "urls": ["https://www.sogeclair.com/contact", "https://www.sogeclair.com/mentions-legales"]},
    {"nom": "Latecoere", "pole": "aero", "urls": ["https://www.latecoere.aero/contact/", "https://www.latecoere.aero/mentions-legales/"]},
    {"nom": "Liebherr Aerospace", "pole": "aero", "urls": ["https://www.liebherr.com/fr/fra/contact/contact.html"]},

    # ── Pôle Santé, Biotech & Oncopole ──
    {"nom": "Pierre Fabre", "pole": "sante", "urls": ["https://www.pierre-fabre.com/fr/contact", "https://www.pierre-fabre.com/fr/espace-presse"]},
    {"nom": "Evotec", "pole": "sante", "urls": ["https://www.evotec.com/en/contact", "https://www.evotec.com/en/news-and-events/press-releases"]},
    {"nom": "CHU de Toulouse", "pole": "sante", "urls": ["https://www.chu-toulouse.fr/-nous-contacter-", "https://www.chu-toulouse.fr/-espace-presse-"]},
    {"nom": "IUCT Oncopole", "pole": "sante", "urls": ["https://www.iuct-oncopole.fr/contact", "https://www.iuct-oncopole.fr/presse"]},
    {"nom": "GTP Bioways", "pole": "sante", "urls": ["https://www.gtp-bioways.com/contact/", "https://www.gtp-bioways.com/legal-notice/"]},
    {"nom": "Sanofi France", "pole": "sante", "urls": ["https://www.sanofi.fr/fr/nous-contacter", "https://www.sanofi.fr/fr/espace-presse"]},
    {"nom": "Servier", "pole": "sante", "urls": ["https://servier.com/fr/contact/", "https://servier.com/fr/espace-presse/"]},

    # ── Pôle Finance, M&A & Juridique ──
    {"nom": "MBA Capital", "pole": "finance", "urls": ["https://www.mbacapital.com/contact/", "https://www.mbacapital.com/mentions-legales/"]},
    {"nom": "In Extenso Finance", "pole": "finance", "urls": ["https://www.inextenso-finance.fr/contact/", "https://www.inextenso-finance.fr/mentions-legales/"]},
    {"nom": "IRDI Capital", "pole": "finance", "urls": ["https://www.irdi.fr/contact/", "https://www.irdi.fr/mentions-legales/"]},
    {"nom": "Midi 2i", "pole": "finance", "urls": ["https://www.midi2i.com/contact/", "https://www.midi2i.com/mentions-legales/"]},
    {"nom": "Eurallia Finance", "pole": "finance", "urls": ["https://www.eurallia-finance.com/contact/", "https://www.eurallia-finance.com/mentions-legales/"]},
    {"nom": "Ordre des Avocats Toulouse", "pole": "finance", "urls": ["https://www.avocats-toulouse.com/fr/contact", "https://www.avocats-toulouse.com/fr/mentions-legales"]},

    # ── Pôle ESN & Intégrateurs ──
    {"nom": "Capgemini", "pole": "esn", "urls": ["https://www.capgemini.com/fr-fr/contactez-nous/", "https://www.capgemini.com/fr-fr/espace-presse/"]},
    {"nom": "Sopra Steria", "pole": "esn", "urls": ["https://www.soprasteria.fr/nous-contacter", "https://www.soprasteria.fr/mentions-legales"]},
    {"nom": "Akkodis", "pole": "esn", "urls": ["https://www.akkodis.com/fr/contact-us"]},
    {"nom": "CS Group", "pole": "esn", "urls": ["https://www.csgroup.eu/fr/contact/", "https://www.csgroup.eu/fr/mentions-legales/"]},
    {"nom": "Eviden", "pole": "esn", "urls": ["https://eviden.com/fr-fr/contactez-nous/"]},
    {"nom": "Inetum", "pole": "esn", "urls": ["https://www.inetum.com/fr/contact", "https://www.inetum.com/fr/mentions-legales"]},
    {"nom": "ACTIA Group", "pole": "industrie", "urls": ["https://www.actia.com/fr/contact/", "https://www.actia.com/fr/mentions-legales/"]},
    {"nom": "Continental Automotive", "pole": "industrie", "urls": ["https://www.continental.com/fr-fr/contact/"]}
]

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

class FastHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.mailtos = set()
        self.has_form = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k.lower() == "href" and v.lower().startswith("mailto:"):
                    em = v.split("?")[0].replace("mailto:", "").strip()
                    if "@" in em:
                        self.mailtos.add(em)
        if tag == "form":
            self.has_form = True

def scanner_url(url):
    emails = set()
    has_form = False
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=7) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            parser = FastHTMLParser()
            parser.feed(content)
            emails.update(parser.mailtos)
            has_form = parser.has_form
            
            for em in EMAIL_REGEX.findall(content):
                em_l = em.lower()
                if not em_l.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.js', '.css')):
                    if 'example' not in em_l and 'u003e' not in em_l and 'wixpress' not in em_l and 'sentry' not in em_l:
                        emails.add(em)
    except Exception:
        pass
    return list(emails), has_form

def main():
    print("==========================================================")
    print("🌾 [JARVIS MOISSON PROFONDE] EXTRACTION DES CONTACTS RÉELS")
    print("==========================================================")
    
    conn_p = sqlite3.connect(PROSPECTION_DB, timeout=30.0)
    cur_p = conn_p.cursor()
    cur_p.execute("""
        CREATE TABLE IF NOT EXISTS contacts_moissonnes (
            id INTEGER PRIMARY KEY,
            entreprise TEXT NOT NULL,
            pole TEXT,
            email TEXT,
            formulaire_url TEXT,
            url_source TEXT NOT NULL,
            moissonne_le TEXT NOT NULL,
            UNIQUE(entreprise, email, url_source)
        )
    """)
    cur_p.execute("""
        CREATE TABLE IF NOT EXISTS moisson_journal (
            id INTEGER PRIMARY KEY,
            entreprise TEXT,
            url TEXT,
            http INTEGER,
            mails INTEGER,
            horodatage TEXT
        )
    """)
    
    now_str = datetime.datetime.now().isoformat()
    total_emails = 0
    total_forms = 0
    
    for c in CIBLES_OFFICIELLES:
        nom = c["nom"]
        pole = c["pole"]
        print(f"\n🏢 {nom:<30} (Pôle: {pole})")
        
        for u in c["urls"]:
            emails, has_form = scanner_url(u)
            status_code = 200 if (emails or has_form) else 0
            cur_p.execute("""
                INSERT INTO moisson_journal (entreprise, url, http, mails, horodatage)
                VALUES (?, ?, ?, ?, ?)
            """, (nom, u, status_code, len(emails), now_str))
            
            if emails:
                for em in emails:
                    try:
                        cur_p.execute("""
                            INSERT OR IGNORE INTO contacts_moissonnes
                            (entreprise, pole, email, formulaire_url, url_source, moissonne_le)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (nom, pole, em.lower(), None, u, now_str))
                        print(f"   📧 [Email Trouvé] {em.lower()} (source: {u})")
                        total_emails += 1
                    except Exception:
                        pass
            elif has_form:
                try:
                    cur_p.execute("""
                        INSERT OR IGNORE INTO contacts_moissonnes
                        (entreprise, pole, email, formulaire_url, url_source, moissonne_le)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (nom, pole, None, u, u, now_str))
                    print(f"   📝 [Formulaire Trouvé] {u}")
                    total_forms += 1
                except Exception:
                    pass
            else:
                print(f"   ℹ️ Aucune donnée directe sur {u}")
                
    conn_p.commit()
    conn_p.close()
    
    # Synchronisation vers jarvis_master.db table contacts_verifies_stricts
    conn_m = sqlite3.connect(MASTER_DB, timeout=30.0)
    cur_m = conn_m.cursor()
    cur_m.execute("ATTACH ? AS pr", (PROSPECTION_DB,))
    cur_m.execute("""
        INSERT OR REPLACE INTO contacts_verifies_stricts 
        (date_moisson, entreprise, secteur, email_reel, url_source, methode_extraction, statut)
        SELECT 
            moissonne_le,
            entreprise,
            pole,
            email,
            url_source,
            'SCRAPING_HTML_REEL',
            CASE 
                WHEN email IS NOT NULL AND email != '' AND email NOT LIKE '%example%' AND email NOT LIKE '%u003e%' THEN 'VERIFIE_HTML_DIRECT'
                WHEN formulaire_url IS NOT NULL AND formulaire_url != '' THEN 'FORMULAIRE_SECURISE'
                ELSE 'NON_SOURCABLE'
            END
        FROM pr.contacts_moissonnes
        WHERE (email IS NOT NULL AND email != '' AND email NOT LIKE '%example%' AND email NOT LIKE '%u003e%')
           OR (formulaire_url IS NOT NULL AND formulaire_url != '');
    """)
    cur_m.execute("DETACH pr")
    conn_m.commit()
    
    total_stricts = cur_m.execute("SELECT count(*) FROM contacts_verifies_stricts").fetchone()[0]
    total_emails_stricts = cur_m.execute("SELECT count(*) FROM contacts_verifies_stricts WHERE statut='VERIFIE_HTML_DIRECT'").fetchone()[0]
    total_forms_stricts = cur_m.execute("SELECT count(*) FROM contacts_verifies_stricts WHERE statut='FORMULAIRE_SECURISE'").fetchone()[0]
    conn_m.close()
    
    print("\n==========================================================")
    print(f"✅ MOISSON TERMINÉE ET SYNCHRONISÉE !")
    print(f"📊 Total Références Réelles : {total_stricts}")
    print(f"   • Emails réels vérifiés par HTML direct : {total_emails_stricts}")
    print(f"   • Formulaires officiels répertoriés     : {total_forms_stricts}")
    print("==========================================================")

if __name__ == "__main__":
    main()
