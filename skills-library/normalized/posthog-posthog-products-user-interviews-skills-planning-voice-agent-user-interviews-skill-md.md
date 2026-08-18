---
{
  "name": "planning-voice-agent-user-interviews",
  "source": "https://skillsmp.com/creators/posthog/posthog/products-user-interviews-skills-planning-voice-agent-user-interviews",
  "repository": "https://github.com/PostHog/posthog/tree/master/products/user_interviews/skills/planning-voice-agent-user-interviews",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:11+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "b7ec24bee02e4a6be43b8fde00b2834e0360c664a5a9e88ba58d63d56fce56f1"
}
---

# Résumé
Plan a round of user interviews conducted by PostHog's AI voice agent (a "robo interviewer") — the automated voice-agent interview product. Captures a UserInterviewTopic (who to target, what to ask, framing context, question list) and calls user-interview-topics-create. ONLY trigger when the user clearly wants an AI voice agent to actually run the interview calls (e.g. "set up robo user interviews", "have the voice agent interview these users"). Do NOT trigger for ordinary user research that does not involve the voice agent — finding or shortlisting users to talk to ("who'd be a good fit to interview about Y"), planning questions for a human-run interview, or analysing feedback are audience discovery, handled with normal data queries, not this skill. Also do NOT trigger for uploading a recorded interview audio file or browsing topics with user-interview-topics-list. When intent is ambiguous, first confirm what kind of research it is and whether they want an AI voice agent to conduct it (see Step 0).

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/products-user-interviews-skills-planning-voice-agent-user-interviews
- Dépôt    : https://github.com/PostHog/posthog/tree/master/products/user_interviews/skills/planning-voice-agent-user-interviews

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
