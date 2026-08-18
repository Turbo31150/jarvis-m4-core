#!/home/pamerys/.local/share/uv/tools/mistral-vibe/bin/python3
"""
MISTRAL RAG & DOCUMENT SEARCH — JARVIS OMEGA INTEGRATION
Permet l'upload de documents vers une Library Mistral AI et le requêtage conversationnel
ancré sur les documents via l'API retrieval (RAG natif Mistral).
"""

import os
import sys
import time
import argparse
from pathlib import Path

try:
    from mistralai.client import Mistral
except ImportError:
    try:
        from mistralai import Mistral
    except ImportError:
        print("❌ Erreur: Le package 'mistralai' n'est pas accessible.")
        sys.exit(1)


def get_client(api_key: str = None) -> Mistral:
    key = api_key or os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("❌ Erreur : MISTRAL_API_KEY manquante. Définissez la variable d'environnement ou passez --api-key.")
        sys.exit(1)
    return Mistral(api_key=key)


def upload_document(client: Mistral, file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Erreur : Fichier introuvable : {file_path}")
        sys.exit(1)
    
    print(f"📤 Upload du fichier '{path.name}' ({path.stat().st_size} octets) vers Mistral Library...")
    with open(path, "rb") as f:
        file_obj = client.files.upload(
            file={
                "file_name": path.name,
                "content": f.read(),
            },
            purpose="retrieval"
        )
    file_id = file_obj.id
    print(f"✅ Fichier téléversé avec succès. File ID : {file_id}")
    return file_id


def wait_for_processing(client: Mistral, file_id: str, timeout: int = 300) -> bool:
    print(f"⏳ Indexation et traitement du document '{file_id}' en cours...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        file_info = client.files.retrieve(file_id=file_id)
        status = getattr(file_info, "status", str(file_info))
        if status == "processed":
            print(f"✅ Document indexé et prêt pour le RAG (en {int(time.time() - start_time)}s).")
            return True
        elif status == "failed":
            print(f"❌ Échec de l'indexation du document : {file_info}")
            return False
        print(f"  Statut actuel : {status}... attente")
        time.sleep(2)
    print("❌ Timeout dépassé lors de l'attente du traitement.")
    return False


def query_rag(client: Mistral, file_id: str, query: str, model: str = "mistral-medium-latest") -> str:
    print(f"\n🔍 Interrogation RAG avec le modèle '{model}'...")
    print(f"❓ Question : « {query} »\n")
    
    response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        documents=[{"type": "file", "id": file_id}],
    )
    
    answer = response.choices[0].message.content
    return answer


def main():
    parser = argparse.ArgumentParser(
        description="Mistral AI RAG Document Search CLI — JARVIS OMEGA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :
  # 1. Upload d'un document et interrogation immédiate :
  mistral-rag -f company-handbook.pdf -q "Quelle est la politique de télétravail ?"

  # 2. Interrogation d'un document déjà uploadé par son File ID :
  mistral-rag -i <file_id> -q "Quels sont les avantages sociaux ?"

  # 3. Spécifier un modèle particulier :
  mistral-rag -f contrat.pdf -q "Résumé des clauses résolutoires" -m mistral-large-latest
        """
    )
    parser.add_argument("--file", "-f", help="Chemin du document à uploader (PDF, TXT, DOCX, MD)")
    parser.add_argument("--file-id", "-i", help="ID d'un fichier déjà uploadé et indexé")
    parser.add_argument("--query", "-q", required=True, help="Question à poser au modèle ancré sur le document")
    parser.add_argument("--model", "-m", default="mistral-medium-latest", help="Modèle Mistral à utiliser (défaut: mistral-medium-latest)")
    parser.add_argument("--api-key", "-k", help="Clé API Mistral (ou via variable MISTRAL_API_KEY)")
    
    args = parser.parse_args()
    
    client = get_client(args.api_key)
    
    file_id = args.file_id
    if not file_id:
        if not args.file:
            print("❌ Erreur : Vous devez spécifier soit un fichier (--file) soit un ID existant (--file-id).")
            sys.exit(1)
        file_id = upload_document(client, args.file)
        if not wait_for_processing(client, file_id):
            sys.exit(1)
    
    answer = query_rag(client, file_id, args.query, model=args.model)
    print("=" * 60)
    print("📖 RÉPONSE RAG MISTRAL :")
    print("=" * 60)
    print(answer)
    print("=" * 60)


if __name__ == "__main__":
    main()
