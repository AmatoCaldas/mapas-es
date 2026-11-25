# Qualidade no MAPAS

Como o projeto garante e mede qualidade: o modelo de referência (ISO/IEC 25010), o que roda em todo PR, os
números de hoje e as dívidas conhecidas. Decisão de fundo: [ADR-0008](../arquitetura/adr/0008-qualidade-verificada-no-ci.md).

## 1. Garantia × controle

| | O que é | No MAPAS |
|---|---|---|
| **Garantia** (processo, previne) | Fazer do jeito que evita o defeito | `main` protegida, PR obrigatório com template e checklist, `CODEOWNERS`, commits convencionais, contrato antes do código (ADR-0007), regra no banco (ADR-0001), migrações imutáveis (ADR-0005) |
| **Controle** (produto, detecta) | Encontrar o defeito antes do usuário | `tsc` estrito, Ruff, 795 funções/casos de teste, testes de arquitetura, cobertura com catraca, playtests registrados nas notas de cada onda |

## 2. Portões do CI (todo PR e todo push na `main`)

| Job | Passo | Falha o PR quando… |
|---|---|---|
| `cliente` | `npm run checar` (TypeScript estrito) | há erro de tipo |
| `cliente` | `npm run cobertura` | algum teste falha, uma regra de arquitetura é violada ou a cobertura cai abaixo de **78% linhas / 90% ramos / 79% funções** |
| `cliente` | `npm run build` | o Vite não consegue gerar o pacote de produção |
| `servidor` | `ruff check` | aparece erro de sintaxe, nome indefinido, import/variável sem uso ou armadilha do bugbear |
| `servidor` | `pytest testes/test_arquitetura.py` | uma camada importa o que não pode, uma migração publicada muda ou um `RAISE` sai sem `RNxx` |
| `servidor` | banco do zero + `pytest --cov` | algum dos testes falha contra um PostgreSQL 14 recém-criado com as 23 migrações |
| `servidor` | resumo | (informativo) tabela de cobertura e complexidade no resumo da execução |

**Catraca de cobertura:** o patamar é o valor medido hoje, arredondado para baixo. Ele só sobe — PR que aumenta a
cobertura pode subir o número no `package.json`; PR que baixa é recusado. Assim a qualidade não regride sem exigir
uma meta arbitrária de uma vez.

## 3. Pirâmide de testes (funções de teste declaradas)

| Nível | Onde | Quantos | O que cobre |
|---|---|---:|---|
| Unidade (sem I/O) | `test_padroes`, `test_chefes`, `test_masmorra`, `test_nucleo`, `test_arquitetura` + cliente `*.teste.mjs` | 104 + 243 | geometria dos golpes, formas da mochila, geração de andares, IA dos chefes, prévia, dicas, regras de arquitetura |
| Integração (PostgreSQL real) | `test_mochila`, `test_golpes`, `test_inimigos`, `test_magias_*`, `test_formas`, `test_expedicao`… | 239 | casos de uso do motor contra os gatilhos de verdade |
| Sistema (API/WebSocket + banco) | `test_partida`, `test_turno`, `test_sessao`, `test_pvpve`, `test_progressao`, `test_correcoes*`… | 209 | rotas REST e partidas pelo WebSocket, de ponta a ponta no servidor |
| Contrato cliente↔servidor | `vetores_padroes.json` lido por `test_padroes.py` e `padroes.teste.mjs` | — | Python e TypeScript dão o mesmo resultado (ADR-0004) |
| Simulação | `testes/sim_masmorra.py` | — | partidas simuladas para balanceamento (ex.: Tundra vencível com 2 jogadores) |

## 4. Números de hoje

| Métrica | Valor | Leitura |
|---|---|---|
| Cobertura do cliente (o que os testes carregam) | 78,4% linhas · 90,7% ramos · 80,0% funções | núcleo puro bem coberto; telas com DOM/Phaser (`mochila/visual.ts`, `mochila/dica.ts`) quase sem teste |
| Cobertura do servidor | publicada no resumo do CI | patamar entra depois da primeira medição no CI |
| Complexidade ciclomática média (radon, 757 blocos) | 3,8 (nota A) | média saudável |
| Funções com complexidade > 10 | 42 | concentração em `pvpve.py`, `expedicao.py`, `ia.py` — candidatas a refatoração |
| Pior função | `pvpve._acao_vista` (CC 36, nota E) | maior risco de manutenção do servidor |
| Índice de manutenibilidade médio | 46,1 | `pvpve.py` e `chefes.py` puxam para baixo (arquivos longos e ramificados) |
| Achados do Ruff | 0 (eram 9 com as mesmas regras na v3) | imports e variável sem uso corrigidos; falsos positivos documentados com `noqa` + motivo |

## 5. Dívidas conhecidas

1. **`pvpve.py`** concentra as funções mais complexas (CC 36, 30, 24). Refatorar quebrando `_acao_vista` e
   `_filtrar_jogada` por tipo de ação, protegido pelos 28 testes de `test_pvpve.py`.
2. **Cobertura do cliente não enxerga a cena Phaser**: arquivos que nenhum teste importa nem entram na conta.
   Próximo passo: teste de ponta a ponta no navegador (Playwright) para o fluxo login → lobby → jogada.
3. **Dois `pytest.raises(Exception)`** genéricos (WebSocket fechado) — trocar pela exceção exata da versão fixada.
4. **Servidor ainda em Python 3.9 localmente**: impede `zip(strict=True)` (B905 desligado).

## 6. Rodando localmente

| Para quê | Comando |
|---|---|
| Tipos + testes + arquitetura + cobertura do cliente | `cd projeto/jogo/cliente && npm run checar && npm run cobertura` |
| Análise estática do servidor | `cd projeto/jogo/servidor && ruff check .` |
| Regras de arquitetura do servidor (sem banco) | `python -m pytest testes/test_arquitetura.py -q` |
| Testes do servidor com cobertura (banco de dev no ar) | `python -m pytest testes -q --cov --cov-report=term` |
| Complexidade | `radon cc -a -s -nc motor main.py` · `radon mi -s motor` |
| Registrar migração nova como publicada | `python -m testes.test_arquitetura publicar` |
| Evolução v1 → v3 | `.venv/bin/python engsoft/evolucao/medir.py` (na raiz) |
