#!/usr/bin/env python3
"""Index SQL de l'inventaire système (apps/services) — trier & organiser vite.
Table `inventaire` : categorie, nom, chemin, taille_mo, statut(actif/doublon/archive),
service, note. Interrogeable via inv.py. Idempotent (UPSERT sur chemin)."""
import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), "inventory.db")

# (categorie, nom, chemin, taille_mo, statut, service, note)
ITEMS = [
 ("voice","lumen-transcription (ACTIF)","/home/pamerys/IA/Research/lumen-transcription-multilangue",199,"actif","jarvis-lumen/whisper/whisperflow-9743","VERSION VIVANTE — ne pas toucher"),
 ("voice","lumen (ancien)","/home/pamerys/jarvis/lumen",69,"doublon","","copie non utilisée par un service actif"),
 ("voice","whisperflow (ancien)","/home/pamerys/whisper-flow-m4/whisperflow",73,"doublon","","ancienne app whisperflow"),
 ("voice","Workspaces/lumen","/home/pamerys/Workspaces/lumen",0.3,"doublon","","copie légère"),
 ("voice","etoile/whisperflow","/home/pamerys/etoile/whisperflow",0.14,"doublon","","copie légère"),
 ("voice","lumen-sessions","/home/pamerys/lumen-sessions",0.09,"doublon","","sessions anciennes"),
 ("voice","jarvis-voice-platform","/home/pamerys/jarvis-voice-platform",0.28,"doublon","","plateforme voice ancienne"),
 ("voice","voice_widget (BOUCLE)","/home/pamerys/jarvis/scripts/voice_widget.py",0,"stoppe","jarvis-voice-widget(disabled)","crash-loop 9291x stoppé ; fix=DISPLAY=:1 si réparation"),
 ("dictionnaire","jarvis_lexicon.db","/home/pamerys/machine-m4-pamerys/db/jarvis_lexicon.db",0,"actif","","lexique transcription"),
 ("dictionnaire","BDQT config","/home/pamerys/.config/bdqt",0,"actif","","base vocabulaire+corrections (Whisper hotwords)"),
]
SCHEMA="""CREATE TABLE IF NOT EXISTS inventaire(
  id INTEGER PRIMARY KEY AUTOINCREMENT, categorie TEXT, nom TEXT, chemin TEXT UNIQUE,
  taille_mo REAL, statut TEXT, service TEXT, note TEXT,
  updated_at TEXT DEFAULT (datetime('now','localtime')));"""
def main():
    c=sqlite3.connect(DB); c.execute(SCHEMA)
    for it in ITEMS:
        c.execute("""INSERT INTO inventaire(categorie,nom,chemin,taille_mo,statut,service,note) VALUES(?,?,?,?,?,?,?)
                     ON CONFLICT(chemin) DO UPDATE SET statut=excluded.statut,taille_mo=excluded.taille_mo,
                       service=excluded.service,note=excluded.note,updated_at=datetime('now','localtime')""",it)
    c.commit()
    n=c.execute("SELECT COUNT(*) FROM inventaire").fetchone()[0]
    dbl=c.execute("SELECT COUNT(*),ROUND(SUM(taille_mo)) FROM inventaire WHERE statut='doublon'").fetchone()
    print(f"✅ {n} items indexés | {dbl[0]} doublons = {dbl[1]:.0f} Mo archivables")
    c.close()
if __name__=="__main__": main()
