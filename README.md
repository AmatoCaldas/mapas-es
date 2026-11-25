# MAPAS — Arquitetura e Qualidade de Software (recorte público)

> **Este repositório é um recorte, não o jogo.** Foi montado para a entrega do trabalho prático da
> disciplina **DCC061 – Engenharia de Software** (UFJF, Prof. Fabrício Martins Mendonça), com os temas
> **Arquitetura de Software** e **Qualidade de Software**. Contém só o necessário para avaliar o trabalho:
> o documento, os slides, as decisões de arquitetura e o código que as verifica. O jogo completo (motor,
> regras, conteúdo, arte e infraestrutura) fica num repositório privado.

## O que está aqui

| Pasta / arquivo | O que é |
|---|---|
| [`entrega/`](entrega/) | **Os PDFs entregues**: documento-texto e slides |
| [`engsoft/`](engsoft/LEIAME.md) | Fontes do documento e dos slides, figuras, gerador de PDF, script de medição e demonstração |
| [`projeto/jogo/docs/arquitetura/`](projeto/jogo/docs/arquitetura/ARQUITETURA.md) | Visão de arquitetura (modelo C4) e as 8 decisões registradas como ADRs |
| [`projeto/jogo/docs/qualidade/`](projeto/jogo/docs/qualidade/QUALIDADE.md) | Plano de qualidade: o que é verificado, onde e com qual ferramenta |
| [`projeto/jogo/servidor/motor/banco.py`](projeto/jogo/servidor/motor/banco.py) | **Decisão 2**: o adaptador único de acesso ao PostgreSQL |
| [`projeto/jogo/servidor/sql/TRECHO_21_golpes_RN13.sql`](projeto/jogo/servidor/sql/TRECHO_21_golpes_RN13.sql) | **Decisão 1**: trecho de uma regra do jogo validada no banco (gatilho com mensagem `RNxx`) |
| [`projeto/jogo/servidor/testes/test_arquitetura.py`](projeto/jogo/servidor/testes/test_arquitetura.py) | Regras de arquitetura do servidor escritas como teste (grafo de importações, migrações imutáveis) |
| [`projeto/jogo/cliente/src/api.ts`](projeto/jogo/cliente/src/api.ts) | O único ponto do cliente que faz HTTP |
| [`projeto/jogo/cliente/src/arquitetura.teste.mjs`](projeto/jogo/cliente/src/arquitetura.teste.mjs) | Regras de arquitetura do cliente escritas como teste (**a evidência principal**) |
| [`engsoft/demo/correcao.diff`](engsoft/demo/correcao.diff) | A correção da erosão: os dois arquivos que faziam HTTP por conta própria |
| [`engsoft/demo/saida_erosao.txt`](engsoft/demo/saida_erosao.txt) | Saída real da regra rodada antes (falha) e depois (passa) da correção |
| [`.github/ci-do-repositorio-completo.yml`](.github/ci-do-repositorio-completo.yml) | O pipeline de integração contínua do repositório completo (aqui só para leitura) |
| `ruff.toml`, `.coveragerc`, `package.json`, `PUBLICADAS.sha256` | Configuração da análise estática, da cobertura e o manifesto das migrações publicadas |

## O que foi retirado, e por quê

| Retirado | Motivo |
|---|---|
| Motor do jogo (IA dos inimigos, geração de andares, chefes, magias, progressão) | É o conteúdo do jogo, não o objeto do trabalho |
| Migrações do banco com as regras completas (há só o trecho acima) | Idem: balanceamento e regras do jogo |
| Arte, sprites, sons e catálogos de itens | Conteúdo autoral do jogo |
| Telas e cena do cliente | Idem |
| Infraestrutura de publicação (servidor, domínio, imagem Docker, scripts de implantação) | Informação sensível de operação |
| Histórico do Git e as versões v1, v2 e v3 | Expõe o jogo inteiro; os números medidos estão em [`engsoft/evolucao/evolucao.md`](engsoft/evolucao/evolucao.md) |

Por isso **os testes e scripts daqui são para leitura**: eles rodam sobre o jogo completo, no CI do
repositório privado. As saídas que o documento cita foram registradas nos arquivos acima. Links que apontam
para arquivos retirados aparecem marcados como *(repositório completo)*. O acesso ao repositório completo
pode ser concedido ao professor para avaliação, se solicitado.

Este recorte é gerado automaticamente por [`engsoft/publico/montar.py`](engsoft/publico/montar.py), a partir de uma
lista explícita de arquivos permitidos, e passa por uma varredura de dados sensíveis antes de cada publicação.
