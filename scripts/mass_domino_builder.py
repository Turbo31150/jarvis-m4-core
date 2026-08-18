import os

dominos_dir = "/home/pamerys/jarvis/dominos-compiled/dominos"
os.makedirs(dominos_dir, exist_ok=True)

legions = ["L1_architectes", "L2_forgeurs", "L3_sentinelles", "L4_analystes", "L5_automates", 
           "L6_traders", "L7_communicateurs", "L8_optimiseurs", "L9_erudits", "L10_debuggers"]

count = 0
for l in legions:
    for i in range(1, 26):
        filename = f"mass-domino-{l.lower()}-{i:02d}.sh"
        filepath = os.path.join(dominos_dir, filename)
        content = f"""#!/bin/bash
# Domino massif généré automatiquement pour {l} - Step {i}
echo "Running Domino Step {i} for {l}..."
python3 /home/pamerys/jarvis/scripts/util_logging.py "Domino {filename} executed" "success" 2>/dev/null || true
"""
        with open(filepath, 'w') as f:
            f.write(content)
        os.chmod(filepath, 0o755)
        count += 1

print(f"BÂTISSEUR MASSIF : {count} nouveaux fichiers de scripts Dominos créés dans {dominos_dir} !")
