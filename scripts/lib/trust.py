#!/usr/bin/env python3
"""
trust.py — contrat de confiance de l'écosystème JARVIS. LA brique de sécurité.

Principe (rupture de privilège Source → Raisonnement → Action) : tout contenu
venant de l'extérieur — mail, page web, transcript, document — est de la
DONNÉE, jamais une INSTRUCTION. Il informe une décision, il ne la déclenche pas.

Deux invariants, et c'est tout l'intérêt du module :

1. **Le niveau de confiance vit dans la STRUCTURE, jamais dans le texte.**
   Le marqueur ⟦TRUST:external_untrusted⟧ inséré par render_for_prompt() est
   *purement informatif* : il aide un lecteur humain ou un modèle à situer le
   contenu. Le retirer, le falsifier, ou en injecter un faux ne change rien au
   niveau effectif, qui est porté par le champ trust_level de l'enveloppe.
   Un attaquant qui contrôle le texte ne contrôle donc pas sa classification.

2. **Anti-escalade : il n'existe aucune API de promotion.** Ce module ne fournit
   volontairement pas de fonction promote()/elevate()/mark_trusted(). Une
   enveloppe externe est immuable et le reste pour toute sa vie. Si tu te
   surprends à vouloir en ajouter une, c'est le design qui est faux, pas le
   module.

API : wrap_external() · wrap_internal() · is_trusted() · require_trusted()
      render_for_prompt() · classify_raw_text()
Stdlib-only.
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Tuple

TRUSTED = "trusted"
EXTERNAL_UNTRUSTED = "external_untrusted"

# Marqueur INFORMATIF uniquement. Ne jamais s'en servir pour décider.
MARKER_TMPL = "⟦TRUST:{level}⟧"
MARKER_RE = re.compile(r"⟦TRUST:[a-z_]+⟧")


class TrustViolation(Exception):
    """Levée quand du contenu non fiable atteint un point qui exige de la confiance."""


@dataclass(frozen=True)
class Envelope:
    """Contenu + sa classification. Immuable (frozen) : pas d'escalade en place."""

    content: str
    trust_level: str
    origin: str
    source_refs: Tuple[str, ...] = field(default_factory=tuple)
    content_hash: str = ""

    def __post_init__(self):
        if self.trust_level not in (TRUSTED, EXTERNAL_UNTRUSTED):
            raise ValueError(f"niveau de confiance inconnu: {self.trust_level!r}")
        if not self.content_hash:
            digest = hashlib.sha256(
                self.content.encode("utf-8", errors="replace")
            ).hexdigest()
            object.__setattr__(self, "content_hash", digest)


def wrap_external(content, origin, source_refs=()):
    """Enveloppe du contenu venu de l'extérieur. TOUJOURS external_untrusted.

    Aucun paramètre ne permet d'en sortir : c'est intentionnel. Toute acquisition
    (web, mail, media) doit passer par ici.
    """
    return Envelope(
        content=str(content),
        trust_level=EXTERNAL_UNTRUSTED,
        origin=str(origin),
        source_refs=tuple(source_refs),
    )


def wrap_internal(content, origin, source_refs=()):
    """Enveloppe du contenu produit par le système lui-même (config locale,
    résultat d'un calcul déterministe, saisie humaine directe).

    N'appelle JAMAIS ceci sur quelque chose qui a transité par l'extérieur, même
    reformulé, résumé ou traduit : un résumé de contenu non fiable reste non
    fiable — c'est précisément par là que la lethal trifecta se réintroduit.
    """
    return Envelope(
        content=str(content),
        trust_level=TRUSTED,
        origin=str(origin),
        source_refs=tuple(source_refs),
    )


def classify_raw_text(text, origin="unknown"):
    """Classe du texte brut dont on ne connaît pas la provenance structurée.

    Retourne TOUJOURS une enveloppe external_untrusted, quel que soit le contenu
    du texte — y compris s'il contient un marqueur ⟦TRUST:trusted⟧ forgé. C'est
    la contre-mesure directe à l'injection de marqueur.
    """
    return wrap_external(text, origin=origin)


def is_trusted(envelope):
    """Vrai seulement pour une Envelope structurellement trusted.

    Tout ce qui n'est pas une Envelope (str brute, dict, None) est traité comme
    non fiable : on ne fait pas confiance par défaut à ce qu'on ne comprend pas.
    """
    return isinstance(envelope, Envelope) and envelope.trust_level == TRUSTED


def require_trusted(envelope, action="action"):
    """Garde de frontière : lève TrustViolation si le contenu n'est pas fiable.

    À appeler avant tout effet de bord (loi A4), jamais après.
    """
    if not is_trusted(envelope):
        level = (
            envelope.trust_level
            if isinstance(envelope, Envelope)
            else type(envelope).__name__
        )
        origin = envelope.origin if isinstance(envelope, Envelope) else "?"
        raise TrustViolation(
            f"'{action}' exige du contenu trusted ; reçu {level} (origine: {origin}). "
            f"Un contenu externe ne déclenche jamais une action directement (A0)."
        )
    return envelope


def strip_marker(text):
    """Retire les marqueurs de confiance d'un texte. Utilitaire d'affichage.

    Ne change évidemment aucun niveau : les marqueurs n'en portaient aucun.
    """
    return MARKER_RE.sub("", text)


def render_for_prompt(envelope):
    """Rend l'enveloppe sous forme de texte pour un prompt, marqueur informatif inclus.

    Le marqueur aide le modèle à situer le contenu ; il n'est pas un contrôle de
    sécurité. Le contrôle, c'est require_trusted() côté effet de bord.
    """
    if not isinstance(envelope, Envelope):
        envelope = classify_raw_text(str(envelope))
    marker = MARKER_TMPL.format(level=envelope.trust_level)
    return f"{marker} (origine: {envelope.origin})\n{envelope.content}"
