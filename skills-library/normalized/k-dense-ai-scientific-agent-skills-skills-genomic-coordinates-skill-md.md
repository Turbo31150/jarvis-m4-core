---
{
  "name": "genomic-coordinates",
  "source": "https://skillsmp.com/creators/k-dense-ai/scientific-agent-skills/skills-genomic-coordinates",
  "repository": "https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/genomic-coordinates",
  "author": "K-Dense-AI",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:16+00:00",
  "verified": false,
  "quality_score": 89,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "88b3bf4a19fadabe7175ff21acb97fe7831444868e4a513abc9e893965bd10cb"
}
---

# Résumé
Convert genomic intervals between coordinate conventions, normalise and compare variant representations, and detect assembly or contig-naming mismatches before they corrupt an analysis. Use whenever coordinates cross a format, tool, or assembly boundary - converting between BED, GFF/GTF, VCF, SAM/BAM, WIG, PSL, genePred, Picard interval_list, or region strings; reconciling 0-based half-open with 1-based inclusive; left-aligning or trimming indels; checking whether two variant records describe the same change; mapping genomic to transcript, CDS, or protein positions; auditing a BED/GTF/VCF for convention violations; or diagnosing GRCh37 vs hg19 vs GRCh38 vs T2T, chr-prefix, and liftover problems. Triggers include "off by one", "0-based", "1-based", "half-open", "coordinate system", "left-align", "normalize variant", "bcftools norm", "chr prefix", "wrong genome build", "liftover", "REF mismatch", and "HGVS".

# Source originale
- SkillsMP : https://skillsmp.com/creators/k-dense-ai/scientific-agent-skills/skills-genomic-coordinates
- Dépôt    : https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/genomic-coordinates

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
