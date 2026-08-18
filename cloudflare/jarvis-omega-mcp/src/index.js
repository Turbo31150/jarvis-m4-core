/**
 * JARVIS OMEGA — façade MCP distante (Cloudflare Worker).
 *
 * Point d'entrée unique pour Claude / Codex / Gemini CLI / tout client MCP :
 *   https://jarvis-omega.<sous-domaine>.workers.dev/mcp
 *
 * Le Worker ne contient AUCUNE logique métier : il authentifie l'appelant,
 * puis relaie le JSON-RPC vers le gateway qui tourne sur le Linux (M4),
 * joignable via l'endpoint public permanent (ngrok réservé).
 *
 * Secrets attendus (wrangler secret put) :
 *   OMEGA_PUBLIC_TOKEN  jeton présenté par les clients MCP
 *   ORIGIN_URL          ex. https://thing-speckled-womanly.ngrok-free.dev/mcp
 *   ORIGIN_BASIC        "jarvis:xxxx" (basic-auth de la traffic policy ngrok)
 *   ORIGIN_TOKEN        jeton OMEGA_TOKEN du gateway local
 */

const JSON_HEADERS = { "Content-Type": "application/json" };

function erreur(code, message, id = null) {
  return new Response(
    JSON.stringify({ jsonrpc: "2.0", id, error: { code: -32000, message } }),
    { status: code, headers: JSON_HEADERS },
  );
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/" || url.pathname === "/sante") {
      return new Response(
        JSON.stringify({
          service: "jarvis-omega-mcp",
          endpoint: "/mcp",
          transport: "streamable-http",
          origine_configuree: Boolean(env.ORIGIN_URL),
        }),
        { headers: JSON_HEADERS },
      );
    }

    if (url.pathname !== "/mcp") return erreur(404, "route inconnue");
    if (request.method !== "POST") return erreur(405, "POST attendu");

    // 1. Authentifier l'appelant.
    const presente = request.headers.get("Authorization") || "";
    if (!env.OMEGA_PUBLIC_TOKEN || presente !== `Bearer ${env.OMEGA_PUBLIC_TOKEN}`) {
      return erreur(401, "jeton absent ou invalide");
    }

    // 2. Vérifier que l'origine est configurée — jamais de repli silencieux.
    if (!env.ORIGIN_URL) return erreur(503, "ORIGIN_URL non configurée sur le Worker");

    const corps = await request.text();

    // 3. Relayer vers le gateway local.
    // Deux authentifications, deux en-têtes : Authorization est réservé au
    // basic-auth du tunnel, le gateway lit son jeton dans X-Omega-Token.
    const entetes = { "Content-Type": "application/json" };
    if (env.ORIGIN_TOKEN) entetes["X-Omega-Token"] = env.ORIGIN_TOKEN;
    if (env.ORIGIN_BASIC) entetes["Authorization"] = `Basic ${btoa(env.ORIGIN_BASIC)}`;

    let reponse;
    try {
      reponse = await fetch(env.ORIGIN_URL, {
        method: "POST",
        headers: entetes,
        body: corps,
      });
    } catch (e) {
      return erreur(502, `origine injoignable : ${e.message}`);
    }

    if (!reponse.ok && reponse.status === 401) {
      return erreur(502, "origine a refusé l'authentification (basic-auth ngrok ?)");
    }

    return new Response(reponse.body, {
      status: reponse.status,
      headers: JSON_HEADERS,
    });
  },
};
