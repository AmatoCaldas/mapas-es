// Regras de arquitetura do cliente como testes (fitness functions), lendo o código-fonte.
// Espelho do servidor/testes/test_arquitetura.py. O porquê de cada regra está nos ADRs
// (projeto/jogo/docs/arquitetura/adr). Rodam com o resto: npm run testar.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = dirname(fileURLToPath(import.meta.url));

// Núcleo puro: regra de jogo sem Phaser e sem DOM, testável com node:test e espelhada do Python
// quando precisa dar o mesmo resultado (ADR-0004). Fica de fora o jogo/dicas-regras.ts, que guarda
// a memória das dicas no localStorage.
const PUROS = [
  "iso.ts", "html.ts", "tipos.ts",
  "jogo/padroes.ts", "jogo/previa.ts", "jogo/previa-golpe.ts", "jogo/catalogo-v3.ts",
  "jogo/pvpve/regras.ts", "mochila/forma.ts", "mochila/regras.ts",
];

function arquivosTs(pasta = SRC) {
  return readdirSync(pasta).flatMap((nome) => {
    const caminho = join(pasta, nome);
    if (statSync(caminho).isDirectory()) return arquivosTs(caminho);
    return nome.endsWith(".ts") && !nome.endsWith(".d.ts") ? [caminho] : [];
  });
}

const rel = (caminho) => relative(SRC, caminho).split(sep).join("/");
const ler = (r) => readFileSync(join(SRC, r), "utf8");
const semComentarios = (codigo) => codigo.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

/** Imports de valor (ignora `import type`, que some no build) de um arquivo, já resolvidos. */
function importsDe(r) {
  const codigo = semComentarios(ler(r));
  const achados = [...codigo.matchAll(/^\s*import\s+(type\s+)?(?:[^"';]*?\s+from\s+)?["']([^"']+)["']/gm)];
  return achados
    .filter(([, soTipo]) => !soTipo)
    .map(([, , alvo]) => {
      if (!alvo.startsWith(".")) return alvo;                       // pacote: "phaser"
      const base = rel(resolve(dirname(join(SRC, r)), alvo));
      return /\.(css|json)$/.test(base) ? base : base.replace(/\.ts$/, "") + ".ts";
    });
}

const TODOS = arquivosTs().map(rel);

test("o grafo enxerga os imports (sanidade das regras abaixo)", () => {
  assert.ok(TODOS.includes("jogo/cena.ts") && TODOS.includes("api.ts"));
  assert.ok(importsDe("jogo/cena.ts").includes("phaser"));
  assert.ok(importsDe("mochila/regras.ts").includes("mochila/forma.ts"));
});

test("só o api.ts faz HTTP (fetch): token, erro e formato num lugar só", () => {
  const usam = TODOS.filter((r) => /\bfetch\s*\(/.test(semComentarios(ler(r))));
  assert.deepEqual(usam, ["api.ts"]);
});

test("só a partida abre WebSocket (uma conexão por partida, com reconexão)", () => {
  const usam = TODOS.filter((r) => /new\s+WebSocket\s*\(/.test(semComentarios(ler(r))));
  assert.deepEqual(usam, ["jogo/partida.ts"]);
});

test("Phaser fica dentro do jogo/ (telas, mochila e ui são DOM puro)", () => {
  const fora = TODOS.filter((r) => importsDe(r).includes("phaser"))
    .filter((r) => !r.startsWith("jogo/") && r !== "comparacao.ts");   // comparacao.ts: teste de arte, fora do build
  assert.deepEqual(fora, []);
});

for (const puro of PUROS) {
  test(`núcleo puro: ${puro} não usa Phaser, DOM nem módulo impuro`, () => {
    const codigo = semComentarios(ler(puro));
    assert.doesNotMatch(codigo, /\b(document|window|sessionStorage|localStorage|fetch|Phaser)\b/, "toca DOM/rede/Phaser");
    const impuros = importsDe(puro).filter((alvo) => !PUROS.includes(alvo));
    assert.deepEqual(impuros, [], `importa fora do núcleo puro: ${impuros.join(", ")}`);
  });
}
