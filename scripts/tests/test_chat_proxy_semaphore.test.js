// Tests de la borne de concurrence par backend du routeur LLM unifié (chat_proxy.js).
// Lancer : node --test /home/pamerys/jarvis/scripts/tests/test_chat_proxy_semaphore.test.js
// Le module n'ouvre aucun port lorsqu'il est require() (garde require.main).

const test = require('node:test');
const assert = require('node:assert');

const { getSemaphore } = require('/home/pamerys/jarvis/scripts/chat_proxy.js');

// rem-linux (100.113.121.61) sert l'inférence en CPU pur sur 8 cœurs et héberge
// aussi le Leader Swarm de production : il doit être borné comme Ollama local,
// et surtout pas hériter de la limite par défaut (999) réservée aux backends
// distants élastiques (cloud, Gemini).
test('rem-linux refuse une requête supplémentaire au-delà de 2 en cours + 1 en file', async () => {
  const sem = getSemaphore('rem-linux');

  assert.strictEqual(await sem.acquire(true), true, '1re requête doit passer');
  assert.strictEqual(await sem.acquire(true), true, '2e requête doit passer');

  // 3e : les 2 places sont prises, la file est vide → elle attend (promesse pendante).
  const enAttente = sem.acquire(true);

  // 4e : une requête patiente déjà → refus immédiat, la cascade bascule sur M1.
  assert.strictEqual(await sem.acquire(true), false, '4e requête doit être refusée immédiatement');

  // Libère pour ne pas laisser la promesse en attente à la fin du test.
  sem.release();
  await enAttente;
  sem.release();
  sem.release();
});

test('ollama local reste borné à 2 requêtes simultanées', () => {
  assert.strictEqual(getSemaphore('ollama').max, 2);
});

test('un backend distant élastique garde la limite large par défaut', () => {
  assert.strictEqual(getSemaphore('ollama-cloud').max, 999);
});
