#!/usr/bin/env bash
# Sentinelle LM Studio — relève le plancher souverain :1234 quand il est TOMBÉ.
#
# Pourquoi : quand LMS s'arrête, rien ne le relançait. Tout le 0-token bascule
# alors en repli (filler « LMS indisponible », prod-loop « backends froids » puis
# timeout) et la charge s'effondre sur Ollama. Panne silencieuse et coûteuse.
#
# Principe : on ne redémarre QUE si le service est réellement mort — jamais de
# force-reload ni de kill. Un LMS lent à chauffer n'est pas un LMS mort : le
# confondre fabrique un flap (cf. lms-qwen-warm).
set -u

URL="http://127.0.0.1:1234/v1/models"
UNITE="lms-headless.service"

if curl -s -m 8 -o /dev/null "$URL"; then
  exit 0                       # répond : rien à faire
fi

# Pas de réponse HTTP : est-ce mort, ou seulement en train de démarrer ?
if pgrep -f "LM-Studio.*AppImage" >/dev/null 2>&1; then
  echo "lms-sentinelle: process présent mais API muette — warmup, on laisse faire"
  exit 0
fi

if systemctl --user is-active --quiet "$UNITE"; then
  echo "lms-sentinelle: $UNITE actif sans process ni API — redémarrage"
  systemctl --user restart "$UNITE"
else
  echo "lms-sentinelle: LM Studio absent — démarrage de $UNITE"
  systemctl --user start "$UNITE"
fi
exit 0
