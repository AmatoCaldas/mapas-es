# ADR-0008 — Arquitetura e qualidade verificadas no CI

**Status:** aceito (trabalho de Eng. de Software, 11/2026) · **Relacionados:** 0002–0005

## Contexto
As decisões 0002–0005 estavam escritas, mas nada impedia um PR de violá-las. O levantamento achou exatamente
isso: duas telas do cliente (`ui/progresso.ts` e `jogo/pvpve/lobby.ts`) tinham o próprio `fetch`, duplicando o
`api.ts` (erosão arquitetural).

## Decisão
O CI de todo PR passa a recusar o que viola a arquitetura ou baixa a qualidade:
- **Fitness functions**: `servidor/testes/test_arquitetura.py` e `cliente/src/arquitetura.teste.mjs`.
- **Análise estática**: Ruff (E9, F, B) no servidor; `tsc` estrito no cliente.
- **Cobertura com catraca**: o cliente não pode cair abaixo do patamar medido (linhas 78%, ramos 90%,
  funções 79%); o servidor publica a cobertura no resumo do CI e ganha patamar depois da primeira medição.
- **Complexidade** (radon) publicada no resumo, sem bloquear.

## Consequências
- (+) A regra de arquitetura vale em todo PR, não só na memória de quem escreveu.
- (+) A catraca impede regressão sem exigir uma meta arbitrária de uma vez.
- (−) Uma regra nova pode precisar de exceção justificada (`noqa` com motivo, lista explícita de módulos puros).
