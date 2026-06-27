const http = require('http');

const LLM_URL = 'http://127.0.0.1:1234/v1/chat/completions';
const MODEL = 'qwen/qwen3.5-9b';

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.url === '/health' || req.url === '/') {
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify({status: 'ok', proxy: 'JARVIS-chat'}));
    return;
  }
  
  if (req.url === '/chat' && req.method === 'POST') {
    let body = '';
    req.on('data', d => body += d);
    req.on('end', () => {
      let payload;
      try { payload = JSON.parse(body); } catch(e) { payload = {messages: [{role:'user', content: body}]}; }
      
      const messages = payload.messages || [{role:'user', content: payload.text || payload.content || body}];
      const llmReq = JSON.stringify({model: MODEL, messages, max_tokens: 512, stream: false});
      
      const options = {
        hostname: '127.0.0.1', port: 1234,
        path: '/v1/chat/completions', method: 'POST',
        headers: {'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(llmReq)}
      };
      
      const llm = http.request(options, (r) => {
        let data = '';
        r.on('data', d => data += d);
        r.on('end', () => {
          try {
            const resp = JSON.parse(data);
            const text = resp.choices?.[0]?.message?.content || 'Pas de réponse';
            res.writeHead(200, {'Content-Type': 'application/json'});
            res.end(JSON.stringify({text, model: MODEL}));
          } catch(e) {
            res.writeHead(500); res.end(JSON.stringify({error: e.message}));
          }
        });
      });
      llm.on('error', e => { res.writeHead(502); res.end(JSON.stringify({error: e.message, text: 'LLM indisponible'})); });
      llm.write(llmReq);
      llm.end();
    });
    return;
  }
  
  // Fallback dashboard
  res.writeHead(200, {'Content-Type': 'application/json'});
  res.end(JSON.stringify({status: 'JARVIS Chat Proxy', routes: ['/chat', '/health']}));
});

server.listen(18800, '0.0.0.0', () => console.log('JARVIS Chat Proxy on :18800'));
