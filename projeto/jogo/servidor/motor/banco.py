"""Conexões com o PostgreSQL (pool) e erro de regra de negócio."""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.pool

MAX_CONEXOES = int(os.environ.get("MAPAS_PG_CONEXOES", "10"))
_pool: psycopg2.pool.ThreadedConnectionPool | None = None
# o pool do psycopg2 dá erro quando esgota; o semáforo faz a thread esperar a vez
_vagas = threading.BoundedSemaphore(MAX_CONEXOES)
_criando_pool = threading.Lock()
# nenhuma consulta do jogo leva mais que isso; protege o PostgreSQL compartilhado
OPCOES_SESSAO = "-c statement_timeout=5000 -c idle_in_transaction_session_timeout=10000"


class RegraErro(Exception):
    """Ação recusada por uma regra do jogo (do banco ou do servidor). A mensagem vai para o jogador.
    `restricao`: nome da constraint violada, quando veio de uma (para quem quiser traduzir/testar)."""

    def __init__(self, mensagem: str = "", restricao: str | None = None):
        super().__init__(mensagem)
        self.restricao = restricao


# Violação de constraint sem regra do jogo na mensagem: o texto cru do PostgreSQL ("duplicate key
# value violates unique constraint ...", "insert or update on table ...") mapearia o esquema do banco
# compartilhado. Vai uma frase do jogo; o nome da constraint fica em RegraErro.restricao.
MENSAGEM_RESTRICAO = {
    "pk_participacao": "Você já está nesta partida.",
    "fk_partida_regiao": "Região inexistente.",
    "fk_participacao_classe": "Classe inexistente.",
    "uq_participacao_classe_rn17": "RN17: essa classe já está ocupada nesta partida.",
    "pk_abertura_bau_rn23": "RN23: esse baú já foi aberto",
}
MENSAGEM_GENERICA = "Ação inválida."


def _mensagem(erro: psycopg2.IntegrityError) -> str:
    """Texto que vai para o jogador: as regras do jogo (RAISE 'RNxx: ...' dos gatilhos) passam como
    estão; o resto vira uma frase conhecida ou a genérica."""
    texto = erro.diag.message_primary or ""
    if texto[:2] == "RN" and texto[2:3].isdigit():
        return texto
    return MENSAGEM_RESTRICAO.get(erro.diag.constraint_name or "", MENSAGEM_GENERICA)


def _pool_conexoes() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    with _criando_pool:
        if _pool is None:
            _pool = _novo_pool()
    return _pool


def _novo_pool() -> psycopg2.pool.ThreadedConnectionPool:
    return psycopg2.pool.ThreadedConnectionPool(
        1, MAX_CONEXOES,
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5499")),
        dbname=os.environ.get("PGDATABASE", "mapas_jogo"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=5,
        options=OPCOES_SESSAO,
    )


@contextmanager
def transacao():
    """Cursor numa transação: commit no fim, rollback em erro. Violações de regra do banco
    (SQLSTATE classe 23, inclusive as dos gatilhos) viram RegraErro com a mensagem original."""
    pool = _pool_conexoes()
    with _vagas:
        conn = pool.getconn()
        quebrada = False
        try:
            with conn:
                with conn.cursor() as cur:
                    yield cur
        except psycopg2.IntegrityError as erro:
            raise RegraErro(_mensagem(erro), erro.diag.constraint_name) from erro
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            quebrada = True          # banco reiniciou ou a conexão caiu: descarta, a próxima abre outra
            raise
        finally:
            pool.putconn(conn, close=quebrada or bool(conn.closed))


def consultar(sql: str, parametros=()) -> list[dict]:
    with transacao() as cur:
        cur.execute(sql, parametros)
        return [dict(linha) for linha in cur.fetchall()]
