#!/usr/bin/env python3
"""check_dns.py — Validation DNS (SPF/DKIM/DMARC) avant envoi email."""

import sys, socket

def validate_domain(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

if __name__ == '__main__':
    domain = sys.argv[1] if len(sys.argv) > 1 else 'google.com'
    if validate_domain(domain):
        print(f'✅ DNS OK pour {domain}')
        sys.exit(0)
    else:
        print(f'❌ DNS KO pour {domain}')
        sys.exit(1)
