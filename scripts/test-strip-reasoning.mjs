#!/usr/bin/env node
// Test unitaire isolé de stripReasoning (défense en profondeur anti-fuite reasoning).
// N'ouvre AUCUN port : chat_proxy.js garde son listen derrière require.main === module.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { stripReasoning } = require('./chat_proxy.js');

let fails = 0;
function eq(name, got, want) {
  if (got === want) { console.log(`  ok  ${name}`); }
  else { console.log(`  FAIL ${name}\n    got:  ${JSON.stringify(got)}\n    want: ${JSON.stringify(want)}`); fails++; }
}

// 1. bloc <think>...</think> retiré, réponse conservée + trim
eq('think ferme retire', stripReasoning('<think>Thinking Process: bla bla</think>\n\nRome'), 'Rome');
// 2. <think> non fermé => tout ce qui suit retiré
eq('think non ferme => vide', stripReasoning('Réponse partielle\n<think>je réfléchis sans fin...'), 'Réponse partielle');
// 3. texte sans think inchangé (juste trim)
eq('sans think inchange', stripReasoning('  Rome  '), 'Rome');
// 4. texte only-think => chaine vide
eq('only think => vide', stripReasoning('<think>Thinking Process: 1+1=2</think>'), '');
// 5. only think non ferme => vide
eq('only think non ferme => vide', stripReasoning('<think>raisonnement interminable'), '');
// 6. multiligne non-greedy : deux blocs, garde le texte entre/après
eq('multi think', stripReasoning('<think>a\nb</think>X<think>c</think>Y'), 'XY');
// 7. non-string / null => chaine vide (robustesse)
eq('null => vide', stripReasoning(null), '');
// 8. <think> avec attribut => retiré correctement
eq('think avec id=1', stripReasoning('<think id=1>x</think>Rome'), 'Rome');
// 9. </think > avec espace avant fermeture => retiré correctement
eq('think avec espace fermeture', stripReasoning('<think >x</think >Rome'), 'Rome');

if (fails) { console.error(`\n${fails} test(s) échoué(s)`); process.exit(1); }
console.log('\nTOUS LES TESTS PASSENT');
