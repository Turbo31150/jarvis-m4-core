"""protocol.py — Détection du type de page et adaptation de la stratégie de capture.

« Adapter automatiquement la logique protocole » : selon la structure détectée
(statique, SPA, contenu dynamique/shadow-DOM), on choisit combien attendre, si on
suit les liens en dur (<a href>) ou les routes JS, et si on traverse les shadow roots.
"""

from .cdp import WALK

# Signaux détectés dans la page → profil de stratégie.
STRATEGIES = {
    "statique": {"wait": 1.0, "shadow": False, "follow": "href", "settle": 0},
    "spa": {"wait": 3.0, "shadow": True, "follow": "route", "settle": 1.5},
    "dynamique": {"wait": 4.0, "shadow": True, "follow": "href", "settle": 2.0},
}


def detect(cdp):
    """Renvoie (type, stratégie, signaux) en sondant le DOM courant."""
    sig = (
        cdp.evl(
            f"""(()=>{{{WALK}
        let shadowHosts=0,total=0;
        for(const e of w(document)){{total++;if(e.shadowRoot)shadowHosts++;}}
        const scripts=[...document.scripts];
        const src=scripts.map(s=>s.src||'').join(' ');
        const framework=/react|angular|vue|svelte|next|nuxt/i.test(src+document.documentElement.outerHTML.slice(0,4000));
        const rootApp=!!document.querySelector('[ng-version],[data-reactroot],#__next,#app,#root');
        return {{total, shadowHosts, scripts:scripts.length,
                 framework, rootApp,
                 anchors:document.querySelectorAll('a[href]').length,
                 hasRouter: !!(window.history && window.history.pushState) && rootApp}};
        }})()"""
        )
        or {}
    )

    is_spa = (
        bool(sig.get("framework") or sig.get("rootApp")) and sig.get("anchors", 0) < 30
    )
    is_dyn = sig.get("shadowHosts", 0) > 3 or sig.get("scripts", 0) > 15
    typ = "spa" if is_spa else ("dynamique" if is_dyn else "statique")
    return typ, dict(STRATEGIES[typ]), sig
