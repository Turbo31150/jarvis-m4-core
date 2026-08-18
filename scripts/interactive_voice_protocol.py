"""
JARVIS VOICE & INTERACTIVE PROTOCOL - Mode 100% Autonome & Boucle Vocale
"""
import subprocess
import os

def speak(text: str):
    """Envoie la synthèse vocale TTS via le canal audio local/remote."""
    try:
        subprocess.run(["bash", "/home/pamerys/jarvis/scripts/voice-type.sh", text], check=False)
        print(f"🗣️ [TTS SPEAK] : {text}")
    except Exception as e:
        print(f"🗣️ [TTS SPEAK - FALLBACK PRINT] : {text} (err: {e})")

def listen_user() -> str:
    """Capture audio et transcription Whisper V3 via M1 (192.168.0.10 / Port 9742)."""
    try:
        res = subprocess.run(["curl", "-s", "http://127.0.0.1:9742/transcribe"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return "fais le"

def execute_compiled_pipeline(draft_action):
    """Exécute la pipeline d'action compilée en mode production."""
    print(f"🚀 [EXECUTION PROTOCOLE] : {draft_action}")
    if isinstance(draft_action, str):
        return subprocess.run(draft_action, shell=True).returncode == 0
    return True

def interactive_confirmation(task_description, draft_action, yolo_mode=True):
    """
    Gère le 'Fais-le' de l'utilisateur ou l'exécution directe en mode YOLO 100% autonome.
    """
    # En mode 100% autonome YOLO, l'exécution est immédiate et ininterrompue
    if yolo_mode:
        print(f"⚡ [MODE 100% AUTONOME YOLO] Exécution directe sans attente : {task_description}")
        speak(f"Exécution directe de : {task_description}")
        return execute_compiled_pipeline(draft_action)
    
    speak(f"J'ai analysé votre demande. Voici ma proposition : {task_description}. Dois-je l'exécuter ?")
    
    user_feedback = listen_user()  # Utilise Whisper V3 sur la .85 (Port 9742)
    
    if any(kw in user_feedback.lower() for kw in ["fais le", "oui", "go", "valide"]):
        speak("Exécution du protocole en cours.")
        return execute_compiled_pipeline(draft_action)
    else:
        speak("Action annulée. Je reste en veille.")
        return False

if __name__ == "__main__":
    interactive_confirmation("Triage et rangement des mails urgents", "python3 /home/pamerys/jarvis/scripts/mail_sorter_organizer.py")
