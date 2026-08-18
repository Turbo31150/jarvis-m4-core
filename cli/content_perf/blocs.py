"""Blocs TSV 'nom<TAB>source<TAB>danger<TAB>bloc' + fusion index avec dédup (nom, source)."""

from pathlib import Path


def _clean(s):
    return str(s).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def make_blocs(platform, fiche_path, prompt_path):
    return [
        (f"{platform}-pro-fiche", "contentperf", "🟢", f"xdg-open '{fiche_path}'"),
        (f"{platform}-pro-prompt", "contentperf", "🟢", f"cat '{prompt_path}'"),
    ]


def merge_index(rows, index_path):
    index_path = Path(index_path)
    if not index_path.exists():
        index_path.write_text("nom\tsource\tdanger\tbloc\n")
    seen = set()
    for line in index_path.read_text().splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 2:
            seen.add((parts[0], parts[1]))
    added = 0
    with index_path.open("a") as fh:
        for nom, source, danger, bloc in rows:
            key = (_clean(nom), _clean(source))
            if key in seen:
                continue
            fh.write(
                "\t".join((_clean(nom), _clean(source), _clean(danger), _clean(bloc)))
                + "\n"
            )
            seen.add(key)
            added += 1
    return added
