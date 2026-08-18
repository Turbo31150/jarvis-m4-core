#!/usr/bin/env python3
"""
Garde-fou exécutable des frontières M1/M2 (guard_frontiers.py).
Vérifie Σ.1 (unicité OWNS), Σ.2 (agent feuille), Σ.3 (acyclicité Kahn).
"""
import json
import sys
import os

def check_frontiers():
    frontiers_file = "/home/pamerys/jarvis/scripts/audit/frontiers/frontiers.json"
    dag_file = "/home/pamerys/jarvis/scripts/audit/frontiers/dag.json"
    
    if not os.path.exists(frontiers_file) or not os.path.exists(dag_file):
        print("❌ Manifestes introuvables")
        sys.exit(77)
        
    with open(frontiers_file) as f:
        frontiers = json.load(f)
    with open(dag_file) as f:
        dag = json.load(f)

    # 1. Unicité OWNS (Σ.1)
    owners = list(frontiers.values())
    if len(owners) != len(set(owners)):
        print("❌ Σ.1 Violation: Capacité possédée par plusieurs briques")
        sys.exit(77)

    # 2. Agent = feuille (Σ.2)
    if dag.get("agent") != []:
        print("❌ Σ.2 Violation: agent n'est pas une feuille")
        sys.exit(77)

    # 3. Acyclicité (Σ.3) - Hors Ω
    nodes = [n for n in dag.keys() if n != "Ω"]
    in_degree = {u: 0 for u in nodes}
    for u in nodes:
        for v in dag.get(u, []):
            if v in in_degree:
                in_degree[v] += 1
                
    queue = [u for u in nodes if in_degree[u] == 0]
    count = 0
    while queue:
        u = queue.pop(0)
        count += 1
        for v in dag.get(u, []):
            if v in in_degree:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
    if count != len(nodes):
        print("❌ Σ.3 Violation: Cycle détecté dans le DAG des briques")
        sys.exit(77)

    print("✅ Invariants Σ.1, Σ.2, Σ.3 validés avec succès !")
    sys.exit(0)

if __name__ == "__main__":
    check_frontiers()
