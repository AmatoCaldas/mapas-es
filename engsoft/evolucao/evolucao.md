# Evolução do MAPAS (gerado por medir.py)

- **v1** (`d69a129`): primeira fatia jogável em co-op + deploy
- **v2** (`1cc359b`): masmorra, chefes, mochila, progressão e PvPvE (3 ondas de agentes)
- **v3** (`e4c97eb`): celular, golpes com formato, magias e mochila de formas
- **v3 + ES** (`TRABALHO`): CI, PRs, regras de arquitetura e cobertura (este trabalho)

| Métrica | v1 | v2 | v3 | v3 + ES |
|---|---:|---:|---:|---:|
| Data | 2026-10-03 | 2026-10-04 | 2026-10-04 | hoje |
| Linhas de código (servidor + cliente) | 1662 | 15622 | 23458 | 23676 |
| Módulos do servidor que acessam o banco direto | 1 | 1 | 1 | 1 |
| Arquivos do cliente que fazem HTTP | 1 | 3 | 3 | 1 |
| Commits acumulados | 8 | 68 | 101 | 106 |
| Linhas de código — servidor (Python) | 909 | 5681 | 7745 | 7745 |
| Linhas de código — cliente (TypeScript) | 753 | 9941 | 15713 | 15931 |
| Módulos do motor | 8 | 19 | 27 | 27 |
| Arquivos TypeScript | 10 | 68 | 93 | 96 |
| Migrações do jogo | 1 | 9 | 16 | 16 |
| Regras de negócio RNxx no banco | 18 | 35 | 46 | 46 |
| Gatilhos (CREATE TRIGGER) | 4 | 44 | 69 | 69 |
| Funções de teste declaradas — servidor | 26 | 337 | 542 | 552 |
| Casos de teste declarados — cliente | 0 | 82 | 207 | 243 |
| Arquivos de teste | 2 | 20 | 35 | 40 |
| Complexidade ciclomática média | 3.37 | 3.8 | 3.83 | 3.83 |
| Funções com complexidade > 10 | 6 | 33 | 42 | 42 |
| Índice de manutenibilidade médio | 60.1 | 44.8 | 46.1 | 46.1 |
| Achados do Ruff (regras de hoje) | 1 | 5 | 9 | 0 |
| Integração contínua | não | não | não | sim |
| Testes de arquitetura | não | não | não | sim |
| Documentos de arquitetura/plano | 1 | 3 | 5 | 16 |
