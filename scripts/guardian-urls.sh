#!/usr/bin/env bash
# guardian-urls.sh — surveille la disponibilité des URLs de vente.
# Fail-safe : sort toujours en 0 pour ne jamais faire échouer le timer systemd.
set -euo pipefail

readonly CONF_FILE="${GUARDIAN_CONF:-/home/pamerys/jarvis/config/guardian-urls.txt}"
readonly LOG_FILE="${GUARDIAN_LOG:-/home/pamerys/jarvis/logs/guardian-urls.log}"
readonly ALERT_LOG="${GUARDIAN_ALERT_LOG:-/home/pamerys/jarvis/logs/guardian-alerts.log}"
readonly VAULT_FILE="/home/pamerys/jarvis/secrets-vault/secrets.enc.env"
readonly AGE_KEY_FILE="/home/pamerys/.config/sops/age/keys.txt"
readonly CURL_TIMEOUT=10

TG_TOKEN=""
TG_CHAT=""
TG_READY=0

now() { date -Is; }

log_line() {
    # niveau <TAB> code <TAB> url
    printf '%s\t%s\t%s\t%s\n' "$(now)" "$1" "$2" "$3" >>"$LOG_FILE"
}

ensure_paths() {
    mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$ALERT_LOG")"
    touch "$LOG_FILE" "$ALERT_LOG"
}

read_urls() {
    [[ -r "$CONF_FILE" ]] || return 0
    sed -e 's/#.*//' -e 's/[[:space:]]//g' "$CONF_FILE" | grep -E '^https?://' || true
}

check_url() {
    local url="$1" code
    code="$(curl -s -o /dev/null -w '%{http_code}' -m "$CURL_TIMEOUT" -L "$url" 2>/dev/null || true)"
    [[ -n "$code" ]] || code="000"
    printf '%s' "$code"
}

code_is_healthy() {
    # 200 ou 3xx = OK (curl -L suit déjà les redirections, un 3xx résiduel reste acceptable)
    [[ "$1" == "200" || "$1" =~ ^3[0-9][0-9]$ ]]
}

load_telegram_creds() {
    # Priorité aux variables d'environnement déjà exportées, sinon coffre sops+age.
    # Les secrets ne sont jamais écrits sur disque ni journalisés.
    TG_TOKEN="${TELEGRAM_TOKEN:-${TELEGRAM_BOT_TOKEN:-}}"
    TG_CHAT="${TELEGRAM_CHAT_ID:-${TELEGRAM_CHAT:-}}"

    if [[ -z "$TG_TOKEN" || -z "$TG_CHAT" ]]; then
        if command -v sops >/dev/null 2>&1 && [[ -r "$VAULT_FILE" && -r "$AGE_KEY_FILE" ]]; then
            local plain
            plain="$(SOPS_AGE_KEY_FILE="$AGE_KEY_FILE" sops -d "$VAULT_FILE" 2>/dev/null || true)"
            if [[ -n "$plain" ]]; then
                [[ -n "$TG_TOKEN" ]] || TG_TOKEN="$(printf '%s\n' "$plain" | awk -F= '/^TELEGRAM_TOKEN=/{sub(/^[^=]*=/,""); gsub(/"/,""); print; exit}')"
                [[ -n "$TG_CHAT" ]] || TG_CHAT="$(printf '%s\n' "$plain" | awk -F= '/^TELEGRAM_CHAT_ID=/{sub(/^[^=]*=/,""); gsub(/"/,""); print; exit}')"
            fi
            unset plain
        fi
    fi

    if [[ -n "$TG_TOKEN" && -n "$TG_CHAT" ]]; then
        TG_READY=1
    else
        TG_READY=0
    fi
}

send_telegram() {
    local message="$1" api_code
    [[ "$TG_READY" -eq 1 ]] || return 1
    api_code="$(curl -s -o /dev/null -w '%{http_code}' -m "$CURL_TIMEOUT" \
        "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -d "chat_id=${TG_CHAT}" \
        -d "text=${message}" 2>/dev/null || true)"
    [[ "$api_code" =~ ^2[0-9][0-9]$ ]]
}

raise_alert() {
    local url="$1" code="$2" channel="log"
    if send_telegram "🔴 URL de vente en panne — HTTP ${code} — ${url}"; then
        channel="telegram"
    fi
    printf '%s\tALERT\t%s\t%s\tcanal=%s\n' "$(now)" "$code" "$url" "$channel" >>"$ALERT_LOG"
}

run_checks() {
    local url code ko=0 total=0
    while IFS= read -r url; do
        [[ -n "$url" ]] || continue
        total=$((total + 1))
        code="$(check_url "$url")"
        if code_is_healthy "$code"; then
            log_line "OK" "$code" "$url"
        else
            log_line "ALERT" "$code" "$url"
            raise_alert "$url" "$code"
            ko=$((ko + 1))
        fi
    done < <(read_urls)
    log_line "SUMMARY" "${ko}/${total}" "urls_en_echec"
}

main() {
    ensure_paths
    load_telegram_creds
    run_checks
}

main "$@" || printf '%s\tERROR\t000\tguardian_interne\n' "$(now)" >>"$LOG_FILE"
exit 0
