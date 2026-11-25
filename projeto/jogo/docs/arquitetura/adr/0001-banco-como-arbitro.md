# ADR-0001 — O PostgreSQL é o árbitro das regras do jogo

**Status:** aceito (v1, 02/10/2026) · **Relacionados:** 0002, 0005

## Contexto
O MAPAS nasceu como trabalho de Banco de Dados: o esquema, as 14 primeiras regras de negócio (RN01–RN14) e os
gatilhos já existiam antes do jogo. Com até 4 jogadores agindo **ao mesmo tempo** na fase dos jogadores, duas
jogadas podem disputar o mesmo loot, o mesmo tile ou o mesmo inimigo.

## Decisão
Regra de **integridade** (posse do item, alcance, ações por rodada, mochila, quem leva o loot…) mora no banco, em
constraint ou gatilho, e toda recusa sai com mensagem `RNxx: …`. O servidor Python **não reimplementa** essas
regras: ele tenta a operação numa transação e repassa ao jogador a recusa do banco. Efeitos, IA dos inimigos e
geração de andares (regras de *simulação*, não de integridade) ficam no motor Python.

## Alternativas descartadas
- **Regras só no Python**: mais fácil de depurar, mas a concorrência (dois jogadores no mesmo loot) exigiria
  travas próprias e duplicaria o que o banco já garantia.
- **Regras no cliente**: o cliente é do jogador; qualquer regra lá pode ser burlada.

## Consequências
- (+) Uma fonte de verdade; a atomicidade e o isolamento do PostgreSQL resolvem a disputa (RN09: só um leva o loot).
- (+) A mensagem `RNxx` liga a recusa ao requisito, o que facilita teste e rastreabilidade.
- (−) Lógica em PL/pgSQL é mais difícil de testar isoladamente; por isso os testes do servidor rodam contra um
  PostgreSQL de verdade (no CI, um serviço `postgres:14`).
- (−) Mudança de regra = migração nova (ADR-0005).
