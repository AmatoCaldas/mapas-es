"""Regras de arquitetura do servidor como testes (fitness functions). Não precisam do banco.

A arquitetura do MAPAS só vale enquanto o código respeita as fronteiras combinadas no
ARQUITETURA_V3.md e nos ADRs (projeto/jogo/docs/arquitetura/adr). Documento ninguém relê a cada
PR; teste roda em todo PR. Cada regra aqui tem o porquê e o ADR de onde ela vem.

Camadas do servidor (de fora para dentro):
    transporte   main.py (HTTP/REST) e motor/salas.py (WebSocket)  — só elas falam FastAPI
    aplicação    motor/partidas.py, turno.py, mochila.py, ...       — casos de uso, falam com o banco
    domínio puro motor/padroes.py, formas.py, grade.py, ...         — regra sem I/O, testável sem banco
    infra        motor/banco.py                                     — único módulo que fala psycopg2
    árbitro      PostgreSQL (sql/*.sql): constraints e gatilhos com mensagem RNxx

Migrações: `python -m testes.test_arquitetura publicar` registra no manifesto as migrações novas
(nunca altera as linhas que já estão lá).
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import sys

import pytest

SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTOR = os.path.join(SERVIDOR, "motor")
SQL = os.path.join(SERVIDOR, "sql")
MANIFESTO = os.path.join(SQL, "PUBLICADAS.sha256")

# Núcleo de domínio: regra pura, sem banco, sem rede, sem FastAPI (ADR-0004). É o que o cliente
# espelha em TypeScript e o que dá para testar em milissegundos.
DOMINIO_PURO = {"chao", "chefes", "efeitos", "formas", "grade", "ia", "masmorra", "padroes", "spawn"}
TRANSPORTE = {"main", "salas"}                     # as portas de entrada (REST e WebSocket)
INFRA_BANCO = {"banco"}                            # o único adaptador do PostgreSQL (ADR-0002)
BIBLIOTECAS_DE_IO = {"psycopg2", "fastapi", "starlette", "uvicorn", "websockets", "httpx", "socket", "subprocess"}


# ------------------------------------------------------------------ grafo de dependências
def _arquivos_do_motor() -> dict[str, str]:
    mods = {n[:-3]: os.path.join(MOTOR, n) for n in os.listdir(MOTOR) if n.endswith(".py") and n != "__init__.py"}
    mods["main"] = os.path.join(SERVIDOR, "main.py")
    return mods


def _importa(caminho: str) -> set[str]:
    """Nomes de primeiro nível importados: 'psycopg2', 'fastapi', e os módulos internos ('banco', 'grade'…)."""
    with open(caminho, encoding="utf-8") as f:
        arvore = ast.parse(f.read(), filename=caminho)
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes |= {a.name.split(".")[0] for a in no.names}
            nomes |= {a.name.split(".")[1] for a in no.names if a.name.startswith("motor.")}
        elif isinstance(no, ast.ImportFrom):
            modulo = no.module or ""
            if no.level == 0 and modulo.startswith("motor"):
                partes = modulo.split(".")
                nomes |= {partes[1]} if len(partes) > 1 else {a.name for a in no.names}
            elif no.level == 0:
                nomes.add(modulo.split(".")[0])
            elif modulo:                            # from .banco import x
                nomes.add(modulo.split(".")[0])
            else:                                   # from . import grade, banco
                nomes |= {a.name for a in no.names}
    return nomes


GRAFO = {nome: _importa(caminho) for nome, caminho in _arquivos_do_motor().items()}
INTERNOS = set(GRAFO)


def _quem_importa(alvo: str) -> set[str]:
    return {m for m, deps in GRAFO.items() if alvo in deps}


# ------------------------------------------------------------------ regras de camada
def test_grafo_enxerga_os_modulos_do_motor():
    # sanidade: se o parser parar de ver as importações, as regras abaixo passariam "de graça"
    assert {"partidas", "banco", "padroes", "salas", "main"} <= INTERNOS
    assert "banco" in GRAFO["partidas"] and "fastapi" in GRAFO["main"]


def test_so_o_motor_banco_fala_com_o_postgres():
    """ADR-0002: o acesso ao banco passa por um adaptador só (pool, transação, tradução do RNxx)."""
    assert _quem_importa("psycopg2") == INFRA_BANCO


def test_so_a_camada_de_transporte_conhece_o_fastapi():
    """Casos de uso não dependem do framework web: trocar REST/WebSocket não mexe na regra."""
    assert _quem_importa("fastapi") | _quem_importa("starlette") <= TRANSPORTE


@pytest.mark.parametrize("modulo", sorted(DOMINIO_PURO))
def test_dominio_puro_nao_faz_io_nem_depende_de_camada_de_fora(modulo):
    """ADR-0004: o núcleo de regra só importa outros módulos puros e a biblioteca padrão."""
    deps = GRAFO[modulo]
    assert not deps & BIBLIOTECAS_DE_IO, f"{modulo} importa biblioteca de I/O: {deps & BIBLIOTECAS_DE_IO}"
    internos = deps & INTERNOS
    assert internos <= DOMINIO_PURO, f"{modulo} depende de camada de fora: {internos - DOMINIO_PURO}"


def test_ninguem_no_motor_depende_do_main():
    """A dependência aponta para dentro: main → motor, nunca motor → main (sem ciclo de camadas)."""
    assert _quem_importa("main") == set()


def test_salas_nao_e_usada_pela_regra_de_jogo():
    """O WebSocket chama a regra; a regra não chama o WebSocket."""
    assert _quem_importa("salas") <= TRANSPORTE


# ------------------------------------------------------------------ o banco como árbitro (ADR-0001)
def _migracoes() -> list[str]:
    return sorted(n for n in os.listdir(SQL) if n.endswith(".sql"))


def test_migracoes_tem_nome_numerado_e_unico():
    nomes = _migracoes()
    assert nomes, "nenhuma migração encontrada"
    numeros = []
    for n in nomes:
        m = re.fullmatch(r"(\d{2})_[a-z0-9_]+\.sql", n)
        assert m, f"{n}: use NN_assunto.sql (minúsculas, sem espaço)"
        numeros.append(int(m.group(1)))
    assert len(numeros) == len(set(numeros)), "dois arquivos com o mesmo número"


def test_toda_recusa_do_banco_tem_codigo_de_regra():
    """O cliente mostra a mensagem do gatilho; o prefixo RNxx liga a recusa ao requisito."""
    sem_codigo = []
    for n in _migracoes():
        with open(os.path.join(SQL, n), encoding="utf-8") as f:
            for i, linha in enumerate(f, 1):
                m = re.search(r"RAISE\s+EXCEPTION\s+'([^']*)", linha, re.IGNORECASE)
                if m and not re.match(r"(RN\d+:|%)", m.group(1)):
                    sem_codigo.append(f"{n}:{i}: {m.group(1)[:40]}")
    assert not sem_codigo, "RAISE EXCEPTION sem 'RNxx:':\n" + "\n".join(sem_codigo)


def _hash(caminho: str) -> str:
    with open(caminho, "rb") as f:                  # CRLF→LF: o mesmo arquivo no Windows e no Linux
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def _manifesto() -> dict[str, str]:
    with open(MANIFESTO, encoding="utf-8") as f:
        pares = (linha.split() for linha in f if linha.strip() and not linha.startswith("#"))
        return {nome: h for h, nome in pares}


def test_migracao_publicada_nao_muda():
    """ADR-0005: produção não reaplica arquivo já aplicado. Mudar um publicado = banco divergente."""
    alteradas = [n for n, h in _manifesto().items() if _hash(os.path.join(SQL, n)) != h]
    assert not alteradas, (f"migração já publicada foi editada: {alteradas}. "
                           "Desfaça e crie um arquivo novo NN_assunto.sql com o próximo número.")


def test_migracao_publicada_nao_some():
    faltando = [n for n in _manifesto() if not os.path.exists(os.path.join(SQL, n))]
    assert not faltando, f"migração publicada apagada: {faltando}"


def publicar() -> None:
    """Acrescenta ao manifesto as migrações que ainda não estão nele."""
    conhecidas = _manifesto() if os.path.exists(MANIFESTO) else {}
    novas = [n for n in _migracoes() if n not in conhecidas]
    with open(MANIFESTO, "a", encoding="utf-8", newline="\n") as f:
        if not conhecidas:
            f.write("# Migrações já publicadas em produção (sha256 com fim de linha LF). Não edite as linhas;\n"
                    "# para registrar uma nova: python -m testes.test_arquitetura publicar\n")
        for n in novas:
            f.write(f"{_hash(os.path.join(SQL, n))}  {n}\n")
    print(f"{len(novas)} migração(ões) registrada(s): {', '.join(novas) or '—'}")


if __name__ == "__main__" and sys.argv[1:] == ["publicar"]:
    publicar()
