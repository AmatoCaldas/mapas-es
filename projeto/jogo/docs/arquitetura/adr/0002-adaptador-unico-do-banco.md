# ADR-0002 — Um adaptador só para o banco

**Status:** aceito (v1; tradução por nome de constraint na revisão da v2, 04/10/2026) · **Relacionados:** 0001

## Contexto
Com o banco como árbitro, todo caso de uso abre transação, pode receber `IntegrityError` de um gatilho e precisa
devolver ao jogador uma frase do jogo — nunca o texto cru do PostgreSQL, que exporia o esquema.

## Decisão
`motor/banco.py` é o **único** módulo que importa `psycopg2`. Ele mantém o pool de conexões (com semáforo e
`statement_timeout`), oferece `transacao()` e `consultar()` e traduz `IntegrityError` em `RegraErro` (mensagem do
`RNxx`, ou frase do jogo pelo nome da constraint).

## Consequências
- (+) Pool, tempo-limite e tradução de erro num lugar só; os casos de uso só conhecem `RegraErro`.
- (+) Trocar o driver (ex.: psycopg 3) toca um arquivo.
- (−) Quem precisa de algo novo do driver tem de passar por este módulo.
- Vigiado por `testes/test_arquitetura.py::test_so_o_motor_banco_fala_com_o_postgres`.
