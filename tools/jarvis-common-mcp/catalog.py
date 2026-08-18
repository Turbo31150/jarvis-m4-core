"""Safe, read-only catalogue for the JARVIS shared document roots."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Source:
    name: str
    path: Path
    description: str
    restricted: bool = False


SOURCES = {
    "service_aide_automatisation": Source(
        "service_aide_automatisation", Path("/home/turbo/Documents/service-aide-automatisation"),
        "Projet d'automatisation et ses livrables.",
    ),
    "reparation_ia": Source(
        "reparation_ia", Path("/home/turbo/Documents/reparation-ia"),
        "Maquettes et documents de réparation IA.",
    ),
    "commande_directe_bibliotheque": Source(
        "commande_directe_bibliotheque", Path("/home/turbo/Documents/Commande_Directe_Bibliotheque"),
        "Bibliothèque de commandes et documentation.",
    ),
    "exports_html": Source("exports_html", Path("/home/turbo/Documents/exports-html"), "Exports HTML."),
    "cluster": Source("cluster", Path("/home/turbo/Documents/cluster"), "Configurations de cluster."),
    "cluster_share": Source("cluster_share", Path("/home/turbo/Documents/cluster-share"), "Partages de cluster."),
    "requestly": Source("requestly", Path("/home/turbo/Documents/Requestly"), "Catalogue Requestly."),
    "api_request": Source("api_request", Path("/home/turbo/Documents/api request"), "Catalogue de requêtes API."),
    "admin_prive": Source(
        "admin_prive", Path("/home/turbo/Documents/_admin-prive"), "Documents administratifs privés.", True,
    ),
    "connexion": Source(
        "connexion", Path("/home/turbo/Documents/connexion"), "Documents réseau et connexion privés.", True,
    ),
}

TEXT_EXTENSIONS = {
    ".csv", ".html", ".htm", ".json", ".js", ".jsx", ".md", ".mjs", ".py", ".toml",
    ".ts", ".tsx", ".txt", ".yaml", ".yml", ".xml",
}
SENSITIVE_NAME = re.compile(r"(?:^|[._-])(secret|token|password|credential|apikey|api[_-]?key|private[_-]?key)(?:[._-]|$)", re.I)
SECRET_VALUE = re.compile(r"(?i)(\b(?:api[_-]?key|token|secret|password|authorization)\b\s*[:=]\s*)([^\s,'\"}]+)")


class CatalogError(ValueError):
    pass


def get_source(name: str) -> Source:
    source = SOURCES.get(name)
    if source is None:
        raise CatalogError(f"Source inconnue : {name}")
    return source


def resolve(source_name: str, relative_path: str = "") -> Path:
    source = get_source(source_name)
    if source.restricted:
        raise CatalogError(f"La source {source_name} est restreinte et n'est pas exposée au MCP.")
    root = source.path.resolve()
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise CatalogError("Chemin hors de la source autorisée.")
    if not candidate.exists():
        raise CatalogError("Chemin introuvable.")
    if SENSITIVE_NAME.search(candidate.name):
        raise CatalogError("Fichier potentiellement sensible : accès refusé.")
    return candidate


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS and path.is_file()


def redact(value: str) -> str:
    return SECRET_VALUE.sub(r"\1[REDACTED]", value)


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and not SENSITIVE_NAME.search(path.name):
            yield path
