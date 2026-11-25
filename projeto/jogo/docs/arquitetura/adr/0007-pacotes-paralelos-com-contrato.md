# ADR-0007 — Desenvolvimento em pacotes paralelos com contrato e dono de arquivo

**Status:** aceito (v2, 03/10/2026)

## Contexto
Da v1 para a v2 o escopo cresceu de ~1,7 mil para ~15,6 mil linhas em dois dias, desenvolvido por vários agentes
de IA trabalhando **ao mesmo tempo**, cada um no seu branch.

## Decisão
Cada onda começa com um **contrato** (`ARQUITETURA_V2.md`, `ARQUITETURA_V3.md`): os formatos das mensagens e das
rotas, os tipos compartilhados (`cliente/src/tipos.ts`, congelado durante a onda), e uma tabela de **pacotes**
com banco, portas e **arquivos de que cada pacote é dono**. Ninguém edita arquivo de outro pacote; a integração
é um merge revisado. Depois da v3, a mesma ideia virou processo do repositório: `main` protegida, PR obrigatório
com CI e revisão (`CODEOWNERS`).

## Consequências
- (+) Trabalho paralelo sem conflito; o contrato é a arquitetura escrita *antes* do código (Lei de Conway usada
  a favor: a divisão do time segue a divisão dos módulos).
- (−) Contrato desatualizado engana; por isso a regra "mudou o contrato, atualize o documento".
