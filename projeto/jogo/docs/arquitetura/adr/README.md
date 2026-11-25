# Registros de decisão de arquitetura (ADRs)

Cada arquivo registra **uma** decisão que molda o MAPAS: o contexto, o que foi decidido, as alternativas
descartadas e as consequências (boas e ruins). Formato curto inspirado no de Michael Nygard (2011).

Regras: ADR aceito não se reescreve; mudou de ideia, escreva um ADR novo que **substitui** o antigo e marque
o antigo como "Substituído por ADR-NNNN". Toda decisão que vira regra automática aponta o teste que a vigia.

| ADR | Decisão | Vigiada por |
|---|---|---|
| [0001](0001-banco-como-arbitro.md) | O PostgreSQL é o árbitro das regras do jogo | `test_toda_recusa_do_banco_tem_codigo_de_regra` + testes de regra |
| [0002](0002-adaptador-unico-do-banco.md) | Um adaptador só para o banco (`motor/banco.py`) | `test_so_o_motor_banco_fala_com_o_postgres` |
| [0003](0003-servidor-autoritativo-websocket.md) | Servidor autoritativo; o cliente manda intenção por WebSocket | `test_so_a_camada_de_transporte_conhece_o_fastapi`, `arquitetura.teste.mjs` |
| [0004](0004-nucleo-puro-espelhado.md) | Núcleo de domínio puro, espelhado em TypeScript com vetores compartilhados | `test_dominio_puro_*`, `núcleo puro: *`, `vetores_padroes.json` |
| [0005](0005-migracoes-imutaveis.md) | Migrações numeradas e imutáveis depois de publicadas | `test_migracao_publicada_nao_muda` + `migrar.py` |
| [0006](0006-imagem-unica-mesma-origem.md) | Uma imagem só: página, API e WebSocket na mesma origem | build do Docker no deploy |
| [0007](0007-pacotes-paralelos-com-contrato.md) | Desenvolvimento em pacotes paralelos com contrato e dono de arquivo | revisão de PR (CODEOWNERS) |
| [0008](0008-qualidade-verificada-no-ci.md) | Arquitetura e qualidade verificadas no CI (fitness functions e catraca) | `.github/workflows/ci.yml` |
