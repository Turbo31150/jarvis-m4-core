[user] [
  {
    "modelCompatibilityType": "gguf",
    "runtime": {
      "hardwareSurveyResult": {
        "compatibility": {
          "status": "compatible"
        },
        "cpuSurveyResult": {
          "result": {
            "code": "Success",
            "message": ""
          },
          "cpuInfo": {
            "name": "",
            "architecture": "x86_64",
            "supportedInstructionSetExtensions": [
              "AVX2",
              "AVX"
            ]
          }
        },
        "memoryInfo": {
          "ramCapacity": 49358659584,
          "vramCapacity": 16375349248,
          "totalMemory": 65734008832
        },
        "gpuSurveyResult": {
          "result": {
            "code": "Success",
            "message": ""
          },
          "gpuInfo": [
            {
              "name": "NVIDIA GeForce GTX 1660 SUPER",
              "deviceId": 0,
              "totalMemoryCapacityBytes": 6027608064,
              "dedicatedMemoryCapacityBytes": 6027608064,
              "integrationType": "Discrete",
              "detectionPlatform": "CUDA",
              "detectionPlatformVersion": "",
              "otherInfo": {
                "deviceUUID": "d062d3e62c08a524bc0ba597c1407c92",
                "driverVersion": "13020",
                "computeCapability": "7.5"
              }
            },
            {
              "name": "NVIDIA GeForce RTX 3080",
              "deviceId": 1,
              "totalMemoryCapacityBytes": 10347741184,
     

[assistant] Le noyau ne voit que **4 GPU** sur les 6 — le problème n'est pas CUDA, il est en amont (PCI/riser). Je creuse.

[assistant] 4 GPU seulement au niveau PCI. L'arbre révèle un splitter avec **2 slots vides**. Je vérifie s'ils sont récupérables et d'où vient la restriction CUDA.

[assistant] Cause trouvée. Je cherche le drop-in qui bride LMS et je tente de récupérer les 2 cartes absentes.

[assistant] Rescan négatif : les 2 cartes manquantes sont **absentes du bus PCI** — c'est matériel, pas logiciel. Je recâble les 4 réellement présentes.

[assistant] Message reçu — le splitter porte bien 4× 1660S. Deux ne sont **pas énumérées par le bus PCI** (bus 07 et 09 vides). Je pousse le diagnostic sur ces 2 ports et j'applique le recâblage des cartes présentes.

[assistant] Diagnostic clos sur le matériel : les ports 1 et 5 du splitter ont une fenêtre PCI allouée mais **zéro endpoint** — les 2 cartes ne répondent pas électriquement. Je recâble maintenant les 4 présentes.

[assistant] Maintenant le garde-fou thermique persistant : 70 W sur toute 1660S (s'appliquera aussi aux 2 qui reviendront).

[assistant] LMS a la bonne configuration. Un process résiduel traîne avec l'ancienne env — je le traque et je vérifie ce que LMS voit vraiment.

[assistant] PATH cassé (`/sbin/home/turbo/.lmstudio/bin` — il manque un `:`). J'utilise le chemin complet et je charge un modèle pour vérifier la répartition réelle.

[assistant] Modèle **réparti sur les 4 GPU** — le recâblage fonctionne. Je termine par ollama (bridé sur 1 seul GPU) et le PATH cassé.

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/systematic-debugging

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, 