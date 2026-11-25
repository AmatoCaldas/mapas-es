# ADR-0005 — Migrações numeradas e imutáveis depois de publicadas

**Status:** aceito (v1, com o deploy em 03/10/2026; manifesto no CI desde o trabalho de Eng. de Software) · **Relacionados:** 0001

## Contexto
O esquema evolui a cada versão (1 migração do jogo na v1, 9 na v2, 16 na v3). Produção, CI e a máquina de cada
desenvolvedor precisam chegar **ao mesmo banco**.

## Decisão
Mudança de banco é um arquivo novo `servidor/sql/NN_assunto.sql`, idempotente (`IF NOT EXISTS`,
`CREATE OR REPLACE`). `migrar.py` aplica só o que falta, registra o sha256 de cada arquivo e usa trava consultiva
(dois containers subindo juntos não migram ao mesmo tempo). Arquivo publicado **não se edita**: o manifesto
`sql/PUBLICADAS.sha256` guarda o hash de cada migração publicada e o CI recusa o PR que alterar uma delas.

## Consequências
- (+) Qualquer banco é reconstruível do zero (`banco_dev.py recriar`, e o CI faz isso em todo PR).
- (+) O erro aparece no PR (CI), não no deploy.
- (−) Corrigir um erro antigo exige migração nova com `CREATE OR REPLACE` preservando todos os ramos da função.
