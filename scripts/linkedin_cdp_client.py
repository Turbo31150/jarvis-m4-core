#!/usr/bin/env python3
"""
linkedin_cdp_client.py — Module CDP WebSocket client pour LinkedIn

Fournit:
- get_or_create_linkedin_tab() : ouvre/réutilise un tab LinkedIn messaging
- CDPSession : session WS dédiée à un tab (Runtime.evaluate, navigate, etc.)
- extract_inbox_messages() : scrape les conversations LinkedIn
- send_reply_to_conversation() : injecte + envoie une réponse
"""

import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

import websocket  # type: ignore

import urllib.request

CDP_HOST = "http://127.0.0.1:9222"
LI_MESSAGING_URL = "https://www.linkedin.com/messaging/"

log = logging.getLogger("li-cdp")


# ─── HTTP helpers (CDP REST) ─────────────────────────────────────────────
def _http_get(path: str) -> Any:
    with urllib.request.urlopen(f"{CDP_HOST}{path}", timeout=5) as r:
        return json.loads(r.read().decode())


def _http_put(path: str) -> dict:
    req = urllib.request.Request(f"{CDP_HOST}{path}", method="PUT")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode())


def list_tabs() -> list[dict]:
    return _http_get("/json/list")


def get_or_create_linkedin_tab() -> dict:
    """Trouve un tab LinkedIn existant ou en crée un nouveau."""
    for t in list_tabs():
        if t.get("type") == "page" and "linkedin.com" in t.get("url", ""):
            return t
    return _http_put(f"/json/new?{LI_MESSAGING_URL}")


# ─── CDP WebSocket session ───────────────────────────────────────────────
class CDPSession:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws: websocket.WebSocket | None = None
        self.msg_id = 0

    def __enter__(self):
        self.ws = websocket.create_connection(self.ws_url, timeout=15)
        return self

    def __exit__(self, *args):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def send(
        self, method: str, params: dict | None = None, timeout: float = 10.0
    ) -> Any:
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method, "params": params or {}}
        assert self.ws
        self.ws.settimeout(timeout)
        self.ws.send(json.dumps(msg))
        while True:
            raw = self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self.msg_id:
                if "error" in data:
                    raise RuntimeError(f"CDP error {method}: {data['error']}")
                return data.get("result", {})
            # ignore les events asynchrones

    def evaluate(
        self, expr: str, await_promise: bool = False, timeout: float = 15.0
    ) -> Any:
        res = self.send(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True, "awaitPromise": await_promise},
            timeout=timeout,
        )
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS exception: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def navigate(self, url: str):
        self.send("Page.enable")
        self.send("Page.navigate", {"url": url}, timeout=15.0)
        time.sleep(2.0)  # laisser le DOM se construire

    def wait_for_selector(self, selector: str, max_wait: float = 20.0) -> bool:
        """Polls jusqu'à ce que le sélecteur soit trouvé."""
        end = time.time() + max_wait
        while time.time() < end:
            try:
                found = self.evaluate(
                    f"!!document.querySelector({json.dumps(selector)})"
                )
                if found:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False


@contextmanager
def linkedin_session() -> Iterator[CDPSession]:
    """Context manager : ouvre/retrouve tab LinkedIn et fournit une session CDP."""
    tab = get_or_create_linkedin_tab()
    ws_url = tab["webSocketDebuggerUrl"]
    log.info(f"Connect CDP WS: {tab.get('url', '?')[:60]}")
    with CDPSession(ws_url) as sess:
        # Si pas sur la page messaging, naviguer
        if "messaging" not in tab.get("url", ""):
            sess.navigate(LI_MESSAGING_URL)
        yield sess


# ─── Scraping inbox ──────────────────────────────────────────────────────
EXTRACT_JS = r"""
(() => {
    // Tente plusieurs sélecteurs (LinkedIn fait évoluer son DOM)
    const SELECTORS = [
        '.msg-conversations-container__convo-item',
        '.msg-conversation-listitem',
        'li.msg-conversation-listitem',
    ];
    let items = [];
    for (const sel of SELECTORS) {
        items = document.querySelectorAll(sel);
        if (items.length) break;
    }
    const out = [];
    items.forEach((el, idx) => {
        const senderEl = el.querySelector('h3, .msg-conversation-listitem__participant-names, .artdeco-entity-lockup__title');
        const previewEl = el.querySelector('p, .msg-conversation-card__message-snippet, .msg-conversation-listitem__message-snippet-body');
        const unreadEl = el.querySelector('.notification-badge, .notification-badge--show, .msg-conversation-card__unread-count');
        const timeEl = el.querySelector('time, .msg-conversation-listitem__time-stamp');
        out.push({
            idx,
            sender: senderEl ? senderEl.innerText.trim() : '',
            preview: previewEl ? previewEl.innerText.trim() : '',
            unread: !!unreadEl,
            time: timeEl ? timeEl.innerText.trim() : '',
            data_conv_id: el.getAttribute('data-control-name') || el.id || '',
        });
    });
    return { count: out.length, items: out };
})()
"""


def extract_inbox_messages(sess: CDPSession) -> list[dict]:
    """Extrait les conversations visibles depuis l'inbox LinkedIn."""
    if not sess.wait_for_selector(
        ".msg-conversations-container__convo-item, .msg-conversation-listitem",
        max_wait=12.0,
    ):
        log.warning("Sélecteur inbox introuvable — page non chargée ou login requis ?")
        return []
    result = sess.evaluate(EXTRACT_JS)
    if not result:
        return []
    log.info(f"Extracted {result['count']} conversations")
    return result["items"]


# ─── Lecture d'une conversation ──────────────────────────────────────────
OPEN_CONV_JS = """
((idx) => {
    const sels = ['.msg-conversations-container__convo-item', '.msg-conversation-listitem'];
    let items = [];
    for (const s of sels) { items = document.querySelectorAll(s); if (items.length) break; }
    if (idx >= items.length) return false;
    items[idx].click();
    return true;
})(%d)
"""

READ_MESSAGES_JS = r"""
(() => {
    const SELECTORS = [
        '.msg-s-message-list__event',
        '.msg-s-event-listitem',
    ];
    let items = [];
    for (const sel of SELECTORS) { items = document.querySelectorAll(sel); if (items.length) break; }
    const out = [];
    items.forEach(el => {
        const senderEl = el.querySelector('.msg-s-message-group__name, .msg-s-event-listitem__name');
        const textEl = el.querySelector('.msg-s-event-listitem__body, p');
        const timeEl = el.querySelector('time');
        out.push({
            sender: senderEl ? senderEl.innerText.trim() : '',
            text: textEl ? textEl.innerText.trim() : '',
            time: timeEl ? timeEl.innerText.trim() : '',
        });
    });
    return out;
})()
"""


def open_conversation(sess: CDPSession, idx: int) -> bool:
    return bool(sess.evaluate(OPEN_CONV_JS % idx))


def read_conversation_messages(sess: CDPSession) -> list[dict]:
    if not sess.wait_for_selector(
        ".msg-s-message-list__event, .msg-s-event-listitem", max_wait=8.0
    ):
        return []
    time.sleep(1.0)
    return sess.evaluate(READ_MESSAGES_JS) or []


# ─── Envoi réponse ───────────────────────────────────────────────────────
SEND_REPLY_JS = r"""
((text) => {
    // Trouve la zone de saisie
    const editor =
        document.querySelector('.msg-form__contenteditable') ||
        document.querySelector('[role="textbox"][contenteditable]');
    if (!editor) return {ok:false, err:'no editor'};
    editor.focus();
    // Insère le texte via execCommand (compatible LinkedIn)
    document.execCommand('insertText', false, text);
    // Trouve le bouton envoyer
    const btn =
        document.querySelector('.msg-form__send-btn, button[data-control-name="send_message"]') ||
        Array.from(document.querySelectorAll('button')).find(b => /envoyer|send/i.test(b.innerText));
    if (!btn) return {ok:false, err:'no send btn', text_set:true};
    if (btn.disabled) return {ok:false, err:'btn disabled', text_set:true};
    btn.click();
    return {ok:true};
})(%s)
"""


def send_reply_via_cdp(sess: CDPSession, text: str) -> dict:
    """Injecte text + clic envoyer. Retourne {ok, err?}."""
    expr = SEND_REPLY_JS % json.dumps(text)
    result = sess.evaluate(expr)
    log.info(f"send_reply result: {result}")
    return result or {"ok": False, "err": "no result"}


# ─── CLI test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    with linkedin_session() as sess:
        msgs = extract_inbox_messages(sess)
        print(f"\nInbox conversations: {len(msgs)}")
        for m in msgs[:10]:
            mark = "🔴" if m["unread"] else "  "
            print(f"  {mark} [{m['idx']}] {m['sender'][:30]:30} | {m['preview'][:60]}")
