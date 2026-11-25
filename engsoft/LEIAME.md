# DCC061 – Engenharia de Software: Arquitetura e Qualidade de Software

Trabalho prático da disciplina DCC061 (UFJF, Prof. Fabrício Martins Mendonça). Temas: **Arquitetura de Software**
e **Qualidade de Software**, com o MAPAS (v1 → v2 → v3) como estudo de caso.

## Os três artefatos

| Artefato | Onde está | Como gerar |
|---|---|---|
| 1. Documento-texto (PDF) | fontes em `documento/secoes/*.html` | `python3 engsoft/gerar.py documento` → `engsoft/saida/DCC061_Arquitetura_Qualidade_MAPAS.pdf` |
| 2. Código-fonte | o próprio repositório (versões nas tags `v1`, `v2`, `v3`); para entregar, o recorte público `mapas-es` | `python3 engsoft/publico/montar.py` |
| 3. Slides (PDF) | `slides/slides.html` | `python3 engsoft/gerar.py slides` → `engsoft/saida/DCC061_Slides_MAPAS.pdf` |

Os PDFs ficam fora do git (`engsoft/saida/`). O gerador usa o Google Chrome/Chromium para imprimir; se ele
estiver noutro lugar, defina `CHROME=/caminho/do/chrome`. Os nomes do grupo vão na capa a partir de
`engsoft/grupo.txt` (uma linha por pessoa: `Nome completo — matrícula`).

## O que a parte prática acrescentou ao código

| Tema | No repositório |
|---|---|
| Arquitetura | Modelo C4 e 8 ADRs em [`projeto/jogo/docs/arquitetura`](../projeto/jogo/docs/arquitetura/ARQUITETURA.md) |
| Arquitetura × Qualidade | Regras de arquitetura como testes: [`servidor/testes/test_arquitetura.py`](../projeto/jogo/servidor/testes/test_arquitetura.py) e [`cliente/src/arquitetura.teste.mjs`](../projeto/jogo/cliente/src/arquitetura.teste.mjs); manifesto de migrações publicadas (`servidor/sql/PUBLICADAS.sha256`) |
| Qualidade | Ruff no servidor (`servidor/ruff.toml`), cobertura nos dois lados com catraca no cliente, complexidade (radon) no resumo do CI: [`.github/workflows/ci.yml`](../.github/ci-do-repositorio-completo.yml) e [`QUALIDADE.md`](../projeto/jogo/docs/qualidade/QUALIDADE.md) |
| Erosão corrigida | `ui/progresso.ts` e `jogo/pvpve/lobby.ts` deixaram de ter `fetch` próprio; tudo passa pelo `api.ts` |
| Evolução | [`evolucao/medir.py`](evolucao/medir.py) mede v1, v2, v3 e a versão atual com a mesma régua → `evolucao/evolucao.md` |
| Demonstração | [`demo/erosao.sh`](demo/erosao.sh) roda a regra "só o api.ts faz HTTP" na v3 publicada (falha) e no código atual (passa) |

## Refazer as medições (todo número do documento sai daqui)

```bash
python3 -m venv .venv && .venv/bin/pip install radon==6.0.1 ruff==0.17.6
.venv/bin/python engsoft/evolucao/medir.py     # Tabela 1: escala e as duas fronteiras por versão
bash engsoft/demo/erosao.sh                     # o teste falhando na v3 e passando depois da correção
(cd projeto/jogo/cliente && npm ci && npm run cobertura)   # 486 casos e a cobertura do cliente
python3 engsoft/gerar.py                        # PDFs; lista as referências fora do texto
```

Antes de entregar, gere os PDFs **a partir do mesmo commit** que vai para o ClassRoom/Git, para PDF e código
dizerem a mesma coisa.

## Roteiro da apresentação (14 slides, ≈ 18 min)

| Slides | Bloco | Tempo | O que precisa ficar claro |
|---|---|---|---|
| 1–2 | Problema e escolha dos temas | 1 min | A pergunta do trabalho e o que é o MAPAS |
| 3–5 | Fundamentos de Arquitetura e Qualidade | 4 min | Definição, importância, histórico curto; ferramentas, normas, mercado e IA numa tela só |
| 6–8 | Arquitetura do MAPAS | 4 min | O diagrama, o percurso de uma jogada, as duas decisões **e o custo de cada uma** |
| 9–11 | Código e qualidade (com demo ao vivo) | 6 min | A regra, o teste, a falha na v3, a correção e por que ela não volta |
| 12–14 | Resultados, limites e conclusão | 3 min | As duas medidas explicadas, o que falta testar, a resposta à pergunta |

### Preparar a demo (slide 10) antes da aula

Deixe abertos, nesta ordem, e teste uma vez no computador da apresentação:

1. No editor: `projeto/jogo/cliente/src/arquitetura.teste.mjs`, no teste `só o api.ts faz HTTP`.
2. No terminal, na raiz do repositório: `bash engsoft/demo/erosao.sh` (cerca de 5 s; precisa de Node 22 e git).
3. A correção: `git diff 9ab1263 -- projeto/jogo/cliente/src/jogo/pvpve/lobby.ts projeto/jogo/cliente/src/ui/progresso.ts`.
4. O lado do servidor: `cd projeto/jogo/servidor && python -m pytest testes/test_arquitetura.py -q` (não precisa de banco).

Se algo falhar na hora, o slide 11 mostra a mesma saída capturada.

A captura da partida no slide 2 (`figuras/partida.jpg`) sai da cena de teste do cliente, sem servidor:
com o Vite no ar, `.venv/bin/python engsoft/demo/capturar_partida.py`.
