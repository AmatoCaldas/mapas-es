# ADR-0003 — Servidor autoritativo; o cliente manda intenção por WebSocket

**Status:** aceito (v1) · **Relacionados:** 0001, 0004, 0006

## Contexto
Jogo cooperativo por turnos para até 4 pessoas no navegador, com fase dos jogadores simultânea e fase dos
inimigos animada para todos ao mesmo tempo.

## Decisão
Estilo **cliente-servidor com servidor autoritativo**. O cliente (Phaser 3 + TypeScript) só desenha e captura a
**intenção** (`{acao: "lancar", item, x, y}`); o servidor (FastAPI) mantém uma **sala por partida**, executa a
ação na regra/banco e transmite o resultado e o estado novo a todos. REST para o que é pedido/resposta (login,
lobby, mochila, perfil); **WebSocket** para a partida (eventos do servidor para o cliente sem *polling*).

## Consequências
- (+) Trapaça no cliente não muda o resultado; todos veem o mesmo estado.
- (+) Fronteira clara: o contrato de mensagens está em `ARQUITETURA_V3.md`.
- (−) Latência: toda jogada faz ida e volta. Mitigado com a **prévia** local (ADR-0004), que mostra o efeito antes
  da confirmação do servidor.
- No cliente, só `api.ts` faz HTTP e só `jogo/partida.ts` abre WebSocket (`src/arquitetura.teste.mjs`). No
  servidor, só `main.py` e `motor/salas.py` conhecem o FastAPI.
