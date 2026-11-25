# ADR-0004 — Núcleo de domínio puro, espelhado em TypeScript com vetores compartilhados

**Status:** aceito (v3, pacote N, 04/10/2026) · **Relacionados:** 0003

## Contexto
Na v3 as armas ganharam **formato de golpe** (cone, linha, empurrão…) e a mochila ganhou **formas de Tetris** com
rotação. O jogador precisa ver na hora quais tiles o golpe pega (prévia), mas quem decide é o servidor. Duas
implementações da mesma regra tendem a divergir em silêncio.

## Decisão
1. A regra geométrica fica em módulos **puros** (sem banco, rede, FastAPI, DOM ou Phaser): no servidor
   `motor/padroes.py`, `formas.py`, `grade.py`…; no cliente `jogo/padroes.ts`, `mochila/forma.ts`…
2. O espelho TypeScript é testado contra o **mesmo arquivo de casos** que o Python: `testes/vetores_padroes.json`
   é gerado pelo Python e lido pelos dois lados (`test_padroes.py` e `padroes.teste.mjs`).

## Consequências
- (+) Divergência entre cliente e servidor vira teste vermelho, não bug em produção.
- (+) Módulos puros rodam em milissegundos, sem banco: a base larga da pirâmide de testes.
- (−) Toda mudança de regra exige regenerar os vetores e conferir o diff.
- A pureza é vigiada pelos dois testes de arquitetura (servidor e cliente).
