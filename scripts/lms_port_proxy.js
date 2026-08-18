#!/usr/bin/env node
const http = require('http');

const PORT = 1234;
const TARGET_PORT = 11235;
const TARGET_HOST = '127.0.0.1';

const server = http.createServer((req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Access-Control-Allow-Methods', '*');
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  let targetUrl = req.url;
  let modifyBody = false;

  console.log(`[proxy] Incoming: ${req.method} ${req.url}`);

  if (req.url.startsWith('/api/v1/chat')) {
    targetUrl = '/v1/responses';
    modifyBody = true;
    console.log(`[proxy] Detected /api/v1/chat -> rewriting to /v1/responses`);
  }

  if (modifyBody && (req.method === 'POST' || req.method === 'PUT')) {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      let payload;
      try {
        payload = JSON.parse(body);
        if (payload.system_prompt !== undefined) {
          payload.instructions = payload.system_prompt;
          delete payload.system_prompt;
        }
      } catch (e) {
        payload = body;
      }

      console.log(`[proxy] Request body parsed. Size: ${body.length} chars. System prompt mapped? ${payload.instructions !== undefined}`);

      const newBody = typeof payload === 'string' ? payload : JSON.stringify(payload);
      const headers = { ...req.headers };
      delete headers['content-length'];
      headers['content-length'] = Buffer.byteLength(newBody);
      headers['host'] = `${TARGET_HOST}:${TARGET_PORT}`;

      const options = {
        hostname: TARGET_HOST,
        port: TARGET_PORT,
        path: targetUrl,
        method: req.method,
        headers: headers
      };

      console.log(`[proxy] Forwarding to target: http://${TARGET_HOST}:${TARGET_PORT}${targetUrl}`);

      const proxyReq = http.request(options, proxyRes => {
        console.log(`[proxy] Response from target: HTTP ${proxyRes.statusCode}`);
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res);
      });

      proxyReq.on('error', err => {
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Proxy request failed', details: err.message }));
      });

      proxyReq.write(newBody);
      proxyReq.end();
    });
  } else {
    // Direct pipe for all other endpoints to support streaming and binary data
    const headers = { ...req.headers };
    headers['host'] = `${TARGET_HOST}:${TARGET_PORT}`;

    const options = {
      hostname: TARGET_HOST,
      port: TARGET_PORT,
      path: targetUrl,
      method: req.method,
      headers: headers
    };

    const proxyReq = http.request(options, proxyRes => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });

    proxyReq.on('error', err => {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Proxy request failed', details: err.message }));
    });

    req.pipe(proxyReq);
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`LM Studio Port Proxy listening on port ${PORT} -> Forwarding to ${TARGET_PORT}`);
});
