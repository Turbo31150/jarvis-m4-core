---
{
  "name": "bulk-rnaseq",
  "source": "https://skillsmp.com/creators/k-dense-ai/scientific-agent-skills/skills-bulk-rnaseq",
  "repository": "https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/bulk-rnaseq",
  "author": "K-Dense-AI",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:16+00:00",
  "verified": false,
  "quality_score": 89,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "452b84aea219eaaa4ecf7bf31690228af0ef36825e0cf8c5e4b1cf235c0d85d8"
}
---

# Résumé
End-to-end bulk RNA-seq orchestrator — takes raw FASTQ reads through QC and trimming (FastQC, fastp/Trim Galore), alignment and quantification (STAR, Salmon, featureCounts), assembles a gene-level counts matrix, then hands off to differential expression (pydeseq2), pathway/GSEA enrichment (pathway-enrichment), and publication figures (scientific-visualization). Use whenever the user has bulk RNA-seq reads or quant output and wants a complete, reproducible differential-expression workflow — e.g. "analyze my RNA-seq", "FASTQ to DESeq2", "run nf-core/rnaseq", "STAR/Salmon quantification", "build a counts matrix for DESeq2", or "go from reads to differentially expressed genes and enriched pathways". Routes between an nf-core/rnaseq (Nextflow) path and a standalone STAR/Salmon path, and covers experimental design, strandedness, and QC gates. For single-cell RNA-seq use the scanpy skill instead.

# Source originale
- SkillsMP : https://skillsmp.com/creators/k-dense-ai/scientific-agent-skills/skills-bulk-rnaseq
- Dépôt    : https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/bulk-rnaseq

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
