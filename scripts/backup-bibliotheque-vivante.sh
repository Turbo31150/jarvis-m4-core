#!/usr/bin/env bash
# backup-bibliotheque-vivante.sh — sauvegarde la partie NON-SQLite de la
# bibliotheque vivante, que le pipeline SQL ne couvre pas.
#
# Le driver SQL sauvegarde les bases (.db). Mais la bibliotheque vivante, c'est
# aussi : l'index de blocs, les exports du catalogue, les escouades generees,
# les agents et les prompts maitres. Rien de tout cela n'est regenerable sans
# re-aspirer le site ou relancer toute la chaine.
#
# Usage : backup-bibliotheque-vivante.sh [--push]
#   sans --push : archive locale seulement
#   --push      : depose aussi dans le repo jarvis-sql-backups et pousse
set -u

TS="$(date +%Y%m%d_%H%M%S)"
DEST="$HOME/jarvis/backups/biblio_vivante_$TS"
REPO="$HOME/jarvis-sql-backups"
LOG="$HOME/jarvis/logs/backup-biblio.log"
PUSH=0
[ "${1:-}" = "--push" ] && PUSH=1

mkdir -p "$DEST" "$(dirname "$LOG")"
journal() { printf '%s\t%s\n' "$(date -Is)" "$*" >> "$LOG"; echo "$*"; }

journal "DEBUT $DEST"

# ── sources : chemin -> nom d'archive
copie() {                       # copie(source, nom)
  local src="$1" nom="$2"
  if [ -e "$src" ]; then
    tar czf "$DEST/$nom.tar.gz" -C "$(dirname "$src")" "$(basename "$src")" 2>/dev/null \
      && journal "  OK   $nom ($(du -h "$DEST/$nom.tar.gz" | cut -f1))" \
      || journal "  ECHEC $nom"
  else
    journal "  absent $src"
  fi
}

copie "$HOME/labo/bibliotheque/lib"                 "blocs-index"
copie "$HOME/labo/bibliotheque/skillsmp/export"     "skillsmp-export"
copie "$HOME/.openclaw/squads"                      "escouades-openclaw"
copie "$HOME/jarvis/artefacts"                      "artefacts"
copie "$HOME/jarvis/plans"                          "plans-intention"
copie "$HOME/jarvis/runs"                           "runs-dag"

# agents d'escouade seuls (le dossier complet contient 151 agents non generes)
if compgen -G "$HOME/.claude/agents/squad-*.md" >/dev/null; then
  tar czf "$DEST/escouades-claude.tar.gz" -C "$HOME/.claude/agents" \
    $(cd "$HOME/.claude/agents" && ls squad-*.md) 2>/dev/null \
    && journal "  OK   escouades-claude ($(ls "$HOME"/.claude/agents/squad-*.md | wc -l) agents)"
fi

# prompts maitres
if compgen -G "$HOME/prompts/*.md" >/dev/null; then
  tar czf "$DEST/prompts-maitres.tar.gz" -C "$HOME/prompts" \
    $(cd "$HOME/prompts" && ls *.md) 2>/dev/null \
    && journal "  OK   prompts-maitres"
fi

# ── table ronde : les debats produits + le moteur qui les produit
# Le corpus interroge (board.db) part par le pipeline SQL ; ce qui manquait,
# c'est ce qui l'exploite (dispatcher, moteur, MCP) et ce qu'il a produit
# (les debats). Un board restaure sans cela redemarre muet.
if [ -d "$HOME/jarvis/data/tables-rondes" ]; then
  tar czf "$DEST/table-ronde.tar.gz" -C "$HOME" \
    jarvis/data/tables-rondes \
    jarvis/board/dispatch_table_ronde.py \
    jarvis/board/board.py \
    jarvis/bin/table-ronde-fast \
    jarvis/scripts/produce_table_ronde.py \
    jarvis/scripts/studio_v2_table_ronde.html \
    jarvis/mcp/board_mcp.py \
    .local/bin/jarvis-table-ronde 2>/dev/null
  # une archive qui ne se relit pas est un faux succes : on verifie avant de compter
  if [ -s "$DEST/table-ronde.tar.gz" ] && tar tzf "$DEST/table-ronde.tar.gz" >/dev/null 2>&1; then
    journal "  OK   table-ronde ($(du -h "$DEST/table-ronde.tar.gz" | cut -f1), $(tar tzf "$DEST/table-ronde.tar.gz" | wc -l) entrees)"
  else
    journal "  ECHEC table-ronde"; rm -f "$DEST/table-ronde.tar.gz"
  fi
else
  journal "  absent $HOME/jarvis/data/tables-rondes"
fi

# ── manifeste de verification
( cd "$DEST" && sha256sum ./*.tar.gz > MANIFEST.sha256 2>/dev/null )
TAILLE=$(du -sh "$DEST" | cut -f1)
NB=$(ls "$DEST"/*.tar.gz 2>/dev/null | wc -l)
journal "archives : $NB · taille : $TAILLE"

# ── depot dans le repo de sauvegarde
if [ "$PUSH" -eq 1 ]; then
  if [ -d "$REPO/.git" ]; then
    mkdir -p "$REPO/biblio_vivante_$TS"
    cp "$DEST"/*.tar.gz "$DEST/MANIFEST.sha256" "$REPO/biblio_vivante_$TS/" 2>/dev/null
    ( cd "$REPO" \
      && git add "biblio_vivante_$TS" >/dev/null 2>&1 \
      && git -c user.email=backup@m1 -c user.name="M1 Biblio Backup" \
             commit -q -m "biblio vivante $TS ($NB archives, $TAILLE)" >/dev/null 2>&1 \
      && git push -q 2>&1 | tail -2 ) \
      && journal "PUSH OK vers $REPO" \
      || journal "PUSH ECHEC (repo non pret ou reseau) — archive locale conservee"
  else
    journal "PUSH ignore : $REPO n'est pas un depot git"
  fi
fi

journal "FIN $DEST"
echo "→ $DEST"
