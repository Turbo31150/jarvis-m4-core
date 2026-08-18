"""capture.py — Extraction : DOM, HTML, CSS, JS, navigation, balises, événements.

Chaque fonction « avale » une facette de la page via le canal CDP et renvoie des
données pures (dict/list). Aucune écriture disque ici (séparation capture/mémoire).
"""

import json
from .cdp import WALK

# Balises de navigation + éléments interactifs ciblés.
NAV_TAGS = ("NAV", "A", "BUTTON", "MENU", "HEADER", "FOOTER", "ASIDE")


def page_meta(cdp):
    return (
        cdp.evl(
            "({url:location.href,title:document.title,"
            "lang:document.documentElement.lang,"
            "charset:document.characterSet,"
            "readyState:document.readyState})"
        )
        or {}
    )


def html(cdp):
    """Code source HTML complet (documentElement.outerHTML)."""
    return cdp.evl("document.documentElement.outerHTML") or ""


def navigation(cdp, shadow=True):
    """Balises de navigation + liens + leur cible (shadow-DOM inclus si demandé)."""
    root = "w(document)" if shadow else "document.querySelectorAll('*')"
    prelude = WALK if shadow else ""
    return (
        cdp.evl(
            f"""(()=>{{{prelude}
        const NAV={json.dumps(NAV_TAGS)};
        const items=[];
        const it = {root};
        for(const e of it){{
          if(!NAV.includes(e.tagName)) continue;
          const r=e.getBoundingClientRect&&e.getBoundingClientRect();
          items.push({{
            tag:e.tagName,
            role:e.getAttribute&&e.getAttribute('role'),
            text:(e.innerText||e.getAttribute&&e.getAttribute('aria-label')||'').trim().slice(0,80),
            href:e.tagName==='A'?e.href:null,
            visible:!!(r&&r.width>0&&r.height>0)
          }});
        }}
        return items.slice(0,300);
        }})()"""
        )
        or []
    )


def links(cdp, same_origin_only=True):
    """Liens internes (pour la série d'actions / parcours utilisateur)."""
    return (
        cdp.evl(
            f"""(()=>{{
        const o=location.origin;
        const set=new Set();
        for(const a of document.querySelectorAll('a[href]')){{
          try{{const u=new URL(a.href);
            if({str(same_origin_only).lower()} && u.origin!==o) continue;
            if(u.protocol.startsWith('http')) set.add(u.href.split('#')[0]);
          }}catch(e){{}}
        }}
        return [...set].slice(0,200);
        }})()"""
        )
        or []
    )


def resources(cdp):
    """CSS, JS, médias, formulaires, tableaux détectés."""
    return (
        cdp.evl(
            """(()=>({
        css:[...document.querySelectorAll('link[rel=stylesheet]')].map(l=>l.href).slice(0,60),
        inlineStyles:document.querySelectorAll('style').length,
        js:[...document.scripts].map(s=>s.src).filter(Boolean).slice(0,60),
        inlineScripts:[...document.scripts].filter(s=>!s.src).length,
        images:[...document.images].map(i=>i.src).slice(0,60),
        forms:[...document.forms].map(f=>({action:f.action,method:f.method,fields:f.elements.length})).slice(0,30),
        tables:document.querySelectorAll('table').length
        }))()"""
        )
        or {}
    )


def events(cdp, secs=4):
    """Événements réseau/navigation captés pendant `secs` (chronologie live)."""
    evs = cdp.events(secs)
    reqs, nav = [], []
    for e in evs:
        p = e.get("params", {})
        if e["method"] == "Network.requestWillBeSent":
            reqs.append(
                {
                    "url": p.get("request", {}).get("url", "")[:120],
                    "method": p.get("request", {}).get("method"),
                }
            )
        elif e["method"] == "Page.frameNavigated":
            nav.append(p.get("frame", {}).get("url", ""))
    return {"requests": reqs[:80], "navigations": nav[:20], "count": len(evs)}


def dom_tree(cdp, shadow=True):
    """Représentation hiérarchique compacte (balise → compte + profondeur max)."""
    prelude = WALK if shadow else ""
    it = "w(document)" if shadow else "document.querySelectorAll('*')"
    return (
        cdp.evl(
            f"""(()=>{{{prelude}
        let n=0,depth=0,tags={{}};
        for(const e of {it}){{n++;tags[e.tagName]=(tags[e.tagName]||0)+1;
          let d=0,p=e;while(p){{d++;p=p.parentElement;}}if(d>depth)depth=d;}}
        const top=Object.entries(tags).sort((a,b)=>b[1]-a[1]).slice(0,25);
        return {{nodes:n, maxDepth:depth, shadowHosts:[...{it}].filter(e=>e.shadowRoot).length, topTags:top}};
        }})()"""
        )
        or {}
    )


def capture_page(cdp, strat, fast=False):
    """Avale UNE page complète selon la stratégie protocole → dict unifié.

    fast=True (mode multi-onglets) : snapshot rapide, fenêtre réseau réduite à ~0,8 s
    (on ne suit pas de liens, inutile d'écouter le trafic longtemps).
    """
    ev_secs = 0.8 if fast else int(strat.get("settle", 1)) + 2
    return {
        "meta": page_meta(cdp),
        "navigation": navigation(cdp, shadow=strat["shadow"]),
        "resources": resources(cdp),
        "dom": dom_tree(cdp, shadow=strat["shadow"]),
        "events": events(cdp, secs=ev_secs),
        "html": html(cdp),
        "links": links(cdp),
    }
