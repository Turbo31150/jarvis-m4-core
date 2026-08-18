#!/usr/bin/env python3
"""
webguard.py — garde SSRF de la brique `web` (loi A3).

La classification d'une IP (privée/loopback/link-local/ULA) n'est PAS la partie
difficile : `ipaddress` la fait bien, y compris pour les formes obfusquées, parce
qu'on classe APRÈS résolution. Les deux vraies failles sont ailleurs, et toutes
deux ont des CVE 2026 sur des composants IA :

1. **TOCTOU / rebinding DNS.** Valider avec getaddrinfo() puis appeler
   urlopen(url) laisse le client HTTP RE-RÉSOUDRE le nom au moment du connect.
   Entre les deux, l'attaquant change sa réponse DNS. C'est CVE-2026-27826
   (mcp-atlassian) : le garde résolvait, validait chaque IP… puis jetait l'IP.
   Parade : ÉPINGLER le socket sur l'IP exacte qui a passé la validation.

2. **Redirections.** Un client qui suit les 30x tout seul contourne le garde :
   l'URL initiale est publique et valide, la destination finale est interne.
   C'est crewAI#6520 / CVE-2026-2286. Parade : ne jamais suivre automatiquement,
   re-valider ET ré-épingler à CHAQUE saut.

Ce module ne fait donc pas que dire oui/non sur une URL : il porte le fetch,
parce que séparer la décision de la connexion est précisément le bug.

API : validate(url) -> (ip, hostname, port, scheme) · fetch(url) -> dict
Stdlib-only.
"""

import socket
import ssl
import ipaddress
import http.client
import urllib.parse

ALLOWED_SCHEMES = ("http", "https")
MAX_REDIRECTS = 5
MAX_BYTES = 8 * 1024 * 1024  # 8 Mo
TIMEOUT = 10
USER_AGENT = "JARVIS-Sovereign-Web/3.0"

# En-têtes qu'on ne rejoue jamais après un saut cross-origin (fuite de creds).
SENSITIVE_HEADERS = ("authorization", "cookie", "proxy-authorization")


class SSRFBlocked(Exception):
    """Levée quand une URL — ou un saut de redirection — vise une cible interne."""


def ip_is_forbidden(ip_str):
    """True si l'IP n'est pas routable publiquement.

    Couvre loopback, RFC1918, link-local 169.254 (IMDS IPv4), réservé, multicast,
    non spécifié, et — via is_private — les ULA fc00::/7, donc l'IMDS IPv6
    fd00:ec2::254 qui a cassé Craft CMS (CVE-2026-27129) parce que ce n'est PAS
    du link-local et qu'une deny-list écrite « 169.254 » le laisse passer.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # non parsable => refus prudent
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped  # ::ffff:127.0.0.1 => on juge l'IPv4 réelle
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate(url, endpoints_locaux_autorises=None):
    """Valide une URL et retourne l'IP à épingler.

    Refuse si UNE SEULE des adresses résolues est interne : on ne laisse pas
    l'attaquant jouer sur l'ordre de résolution (round-robin A/AAAA).

    `endpoints_locaux_autorises` : itérable de "host:port" explicitement permis
    malgré leur caractère interne (l'Auto-API souveraine locale, par exemple).
    C'est une autorité bornée A5 : elle DOIT être passée explicitement par
    l'appelant, n'est jamais active par défaut, et ne porte que sur le couple
    hôte:port exact — pas sur une plage. Ne jamais la dériver d'un contenu
    external_untrusted.

    Retourne (ip_epinglee, hostname, port, scheme).
    """
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFBlocked(
            f"schéma non autorisé: {scheme or '(vide)'} — seuls http/https le sont"
        )
    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlocked("URL sans hôte")
    port = parsed.port or (443 if scheme == "https" else 80)

    autorises = set(endpoints_locaux_autorises or ())
    if f"{hostname}:{port}" in autorises:
        # cible interne DÉCLARÉE : on résout pour épingler, sans juger l'IP.
        try:
            infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        except (socket.gaierror, UnicodeError, OSError) as exc:
            raise SSRFBlocked(f"résolution impossible pour {hostname}: {exc}") from exc
        return infos[0][4][0], hostname, port, scheme

    try:
        infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, OSError) as exc:
        raise SSRFBlocked(f"résolution impossible pour {hostname}: {exc}") from exc
    if not infos:
        raise SSRFBlocked(f"aucune adresse pour {hostname}")

    addresses = [info[4][0] for info in infos]
    for addr in addresses:
        if ip_is_forbidden(addr):
            raise SSRFBlocked(f"{hostname} résout vers une adresse interne: {addr}")

    # toutes validées : on épingle la première et on ne re-résoudra plus
    return addresses[0], hostname, port, scheme


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTP dont le socket va sur l'IP validée, pas sur une re-résolution du nom."""

    def __init__(self, host, pinned_ip, **kwargs):
        super().__init__(host, **kwargs)
        self._pinned_ip = pinned_ip

    def connect(self):
        self.sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS épinglé. Le certificat reste validé contre le HOSTNAME (SNI), pas l'IP."""

    def __init__(self, host, pinned_ip, **kwargs):
        super().__init__(host, **kwargs)
        self._pinned_ip = pinned_ip

    def connect(self):
        sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def _open(url, extra_headers=None, endpoints_locaux_autorises=None):
    """Une requête, une seule, sur IP épinglée. Ne suit aucune redirection."""
    ip, hostname, port, scheme = validate(url, endpoints_locaux_autorises)
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    if scheme == "https":
        conn = _PinnedHTTPSConnection(
            hostname,
            ip,
            port=port,
            timeout=TIMEOUT,
            context=ssl.create_default_context(),
        )
    else:
        conn = _PinnedHTTPConnection(hostname, ip, port=port, timeout=TIMEOUT)

    headers = {"User-Agent": USER_AGENT, "Accept": "*/*", "Connection": "close"}
    if extra_headers:
        headers.update(extra_headers)
    conn.request("GET", path, headers=headers)
    return conn, conn.getresponse(), ip


def fetch(url, endpoints_locaux_autorises=None):
    """Récupère une URL en re-validant et ré-épinglant à chaque redirection.

    Retourne {url_finale, status, body, ip, sauts}. Lève SSRFBlocked si un saut
    quelconque de la chaîne vise une cible interne — c'est le point que le
    one-shot manquait.
    """
    current = url
    hops = []
    for _ in range(MAX_REDIRECTS + 1):
        conn, resp, ip = _open(
            current, endpoints_locaux_autorises=endpoints_locaux_autorises
        )
        hops.append({"url": current, "ip": ip, "status": resp.status})
        if resp.status in (301, 302, 303, 307, 308):
            location = resp.getheader("Location")
            conn.close()
            if not location:
                raise SSRFBlocked(f"redirection {resp.status} sans en-tête Location")
            nxt = urllib.parse.urljoin(current, location)
            # LE point critique : le saut suivant repasse par validate() +
            # épinglage. Une 302 vers 169.254.169.254 meurt ici.
            current = nxt
            continue
        try:
            body = resp.read(MAX_BYTES + 1)
        finally:
            conn.close()
        if len(body) > MAX_BYTES:
            raise SSRFBlocked(
                f"réponse dépassant la taille maximale ({MAX_BYTES} octets)"
            )
        return {
            "url_finale": current,
            "status": resp.status,
            "body": body.decode("utf-8", errors="replace"),
            "ip": ip,
            "sauts": hops,
        }
    raise SSRFBlocked(f"trop de redirections (> {MAX_REDIRECTS})")
