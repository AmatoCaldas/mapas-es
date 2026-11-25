"""Mede a evolução do MAPAS de versão em versão, direto do histórico do git (sem rodar o jogo).

Uso (na raiz do repositório, com o .venv que tem radon e ruff):
    .venv/bin/python engsoft/evolucao/medir.py            # gera evolucao.json e evolucao.md aqui ao lado

Cada versão é extraída com `git archive` numa pasta temporária e medida com as mesmas réguas:
tamanho (linhas de código sem brancos), módulos, migrações, regras RNxx, testes, complexidade (radon)
e achados da análise estática (ruff, com o ruff.toml de hoje aplicado a todas as versões).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
BIN = os.path.dirname(sys.executable)
RUFF_TOML = os.path.join(RAIZ, "projeto", "jogo", "servidor", "ruff.toml")

VERSOES = [
    {"nome": "v1", "rev": "d69a129", "resumo": "primeira fatia jogável em co-op + deploy"},
    {"nome": "v2", "rev": "1cc359b", "resumo": "masmorra, chefes, mochila, progressão e PvPvE (3 ondas de agentes)"},
    {"nome": "v3", "rev": "e4c97eb", "resumo": "celular, golpes com formato, magias e mochila de formas"},
    {"nome": "v3 + ES", "rev": "TRABALHO", "resumo": "CI, PRs, regras de arquitetura e cobertura (este trabalho)"},
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout


def extrair(rev: str, destino: str) -> None:
    if rev == "TRABALHO":            # a pasta de trabalho como está (versionado + novo, sem o ignorado)
        for rel in git("ls-files", "-co", "--exclude-standard").splitlines():
            origem = os.path.join(RAIZ, rel)
            if os.path.isfile(origem):
                os.makedirs(os.path.dirname(os.path.join(destino, rel)), exist_ok=True)
                with open(origem, "rb") as a, open(os.path.join(destino, rel), "wb") as b:
                    b.write(a.read())
        return
    dados = subprocess.run(["git", "archive", rev], cwd=RAIZ, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=BytesIO(dados)) as tar:
        tar.extractall(destino)  # noqa: S202 — o próprio repositório


def linhas_de_codigo(arquivos: list[str]) -> int:
    total = 0
    for a in arquivos:
        with open(a, encoding="utf-8", errors="replace") as f:
            total += sum(1 for linha in f if linha.strip())
    return total


def listar(pasta: str, extensao: str, excluir: tuple[str, ...] = ()) -> list[str]:
    achados = []
    for raiz, dirs, nomes in os.walk(pasta):
        dirs[:] = [d for d in dirs if d not in {"node_modules", "dist", "__pycache__"}]
        achados += [os.path.join(raiz, n) for n in nomes if n.endswith(extensao) and not n.endswith(excluir)]
    return sorted(achados)


def ler_tudo(arquivos: list[str]) -> str:
    return "\n".join(open(a, encoding="utf-8", errors="replace").read() for a in arquivos)


def radon_medias(alvos: list[str]) -> dict:
    """Complexidade ciclomática média e índice de manutenibilidade médio (radon)."""
    radon = os.path.join(BIN, "radon")
    if not os.path.exists(radon) or not alvos:
        return {}
    cc = json.loads(subprocess.run([radon, "cc", "-j", *alvos], capture_output=True, text=True).stdout or "{}")
    blocos = [b for lista in cc.values() if isinstance(lista, list) for b in lista]
    mi = json.loads(subprocess.run([radon, "mi", "-j", *alvos], capture_output=True, text=True).stdout or "{}")
    indices = [v["mi"] for v in mi.values() if isinstance(v, dict) and "mi" in v]
    return {
        "funcoes": len(blocos),
        "cc_media": round(sum(b["complexity"] for b in blocos) / len(blocos), 2) if blocos else None,
        "cc_acima_de_10": sum(1 for b in blocos if b["complexity"] > 10),
        "mi_media": round(sum(indices) / len(indices), 1) if indices else None,
    }


def ruff_achados(pasta: str) -> int | None:
    ruff = os.path.join(BIN, "ruff")
    if not os.path.exists(ruff):
        return None
    # cwd = pasta do servidor: os caminhos do per-file-ignores ("testes/*") valem a partir dela
    r = subprocess.run([ruff, "check", "--config", RUFF_TOML, "--output-format", "json", "--exit-zero", "."],
                       cwd=pasta, capture_output=True, text=True)
    # mesmas regras de hoje para todas as versões; o que o código atual silencia com noqa explicado
    # também conta como resolvido
    return len(json.loads(r.stdout or "[]"))


def quem_usa(arquivos: list[str], padrao: str, base: str) -> list[str]:
    """Arquivos (relativos a base) cujo código casa com o padrão — ex.: quem importa psycopg2."""
    regex = re.compile(padrao, re.MULTILINE)
    return sorted(os.path.relpath(a, base).replace(os.sep, "/") for a in arquivos
                  if regex.search(open(a, encoding="utf-8", errors="replace").read()))


def medir(raiz: str, rev: str) -> dict:
    jogo = os.path.join(raiz, "projeto", "jogo")
    servidor, cliente = os.path.join(jogo, "servidor"), os.path.join(jogo, "cliente", "src")
    motor = listar(os.path.join(servidor, "motor"), ".py")
    codigo_py = motor + [p for p in [os.path.join(servidor, "main.py")] if os.path.exists(p)]
    testes_py = listar(os.path.join(servidor, "testes"), ".py")
    ts = listar(cliente, ".ts", excluir=(".d.ts",))
    testes_ts = listar(cliente, ".teste.mjs")
    sqls = listar(os.path.join(servidor, "sql"), ".sql") + listar(os.path.join(raiz, "projeto", "sql"), ".sql")
    texto_sql = ler_tudo(sqls)
    base = "HEAD" if rev == "TRABALHO" else rev
    return {
        "data": git("log", "-1", "--format=%ad", "--date=short", base).strip() if rev != "TRABALHO" else "hoje",
        "commits": int(git("rev-list", "--count", base).strip()),
        "loc_total": linhas_de_codigo(codigo_py) + linhas_de_codigo(ts),
        "loc_servidor": linhas_de_codigo(codigo_py),
        # ADR-0002: quantos módulos do servidor falam direto com o PostgreSQL (o esperado é 1: banco.py)
        "modulos_banco": quem_usa(codigo_py, r"^\s*(import|from)\s+psycopg2", servidor),
        # ADR-0003: quantos arquivos do cliente fazem HTTP por conta própria (o esperado é 1: api.ts)
        "arquivos_http": quem_usa(ts, r"\bfetch\s*\(", cliente),
        "loc_cliente": linhas_de_codigo(ts),
        "modulos_motor": len([m for m in motor if not m.endswith("__init__.py")]),
        "arquivos_ts": len(ts),
        "migracoes_jogo": len(listar(os.path.join(servidor, "sql"), ".sql")),
        "regras_rn": len(set(re.findall(r"\bRN(\d+)\b", texto_sql))),
        "gatilhos": len(re.findall(r"CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER", texto_sql, re.IGNORECASE)),
        "testes_servidor": len(re.findall(r"^\s*(?:async\s+)?def test_", ler_tudo(testes_py), re.MULTILINE)),
        "testes_cliente": len(re.findall(r"^\s*(?:test|it)\(", ler_tudo(testes_ts), re.MULTILINE)),
        "arquivos_teste": len([t for t in testes_py if os.path.basename(t).startswith("test_")]) + len(testes_ts),
        "testes_arquitetura": os.path.exists(os.path.join(servidor, "testes", "test_arquitetura.py")),
        "ci": os.path.exists(os.path.join(raiz, ".github", "workflows", "ci.yml")),
        "docs_arquitetura": len([n for n in os.listdir(jogo) if n.startswith(("ARQUITETURA", "PLANO"))])
        + len(listar(os.path.join(jogo, "docs"), ".md")),
        "radon": radon_medias(codigo_py),
        "ruff_achados": ruff_achados(servidor) if os.path.isdir(servidor) else None,
    }


def tabela_md(resultado: list[dict]) -> str:
    linhas = [
        ("Data", "data"), ("Linhas de código (servidor + cliente)", "loc_total"),
        ("Módulos do servidor que acessam o banco direto", "modulos_banco"),
        ("Arquivos do cliente que fazem HTTP", "arquivos_http"), ("Commits acumulados", "commits"), ("Linhas de código — servidor (Python)", "loc_servidor"),
        ("Linhas de código — cliente (TypeScript)", "loc_cliente"), ("Módulos do motor", "modulos_motor"),
        ("Arquivos TypeScript", "arquivos_ts"), ("Migrações do jogo", "migracoes_jogo"),
        ("Regras de negócio RNxx no banco", "regras_rn"), ("Gatilhos (CREATE TRIGGER)", "gatilhos"),
        ("Funções de teste declaradas — servidor", "testes_servidor"), ("Casos de teste declarados — cliente", "testes_cliente"),
        ("Arquivos de teste", "arquivos_teste"), ("Complexidade ciclomática média", "radon.cc_media"),
        ("Funções com complexidade > 10", "radon.cc_acima_de_10"), ("Índice de manutenibilidade médio", "radon.mi_media"),
        ("Achados do Ruff (regras de hoje)", "ruff_achados"), ("Integração contínua", "ci"),
        ("Testes de arquitetura", "testes_arquitetura"), ("Documentos de arquitetura/plano", "docs_arquitetura"),
    ]

    def valor(m: dict, chave: str):
        for parte in chave.split("."):
            m = m.get(parte, {}) if isinstance(m, dict) else {}
        if isinstance(m, bool):
            return "sim" if m else "não"
        if isinstance(m, list):
            return str(len(m))
        return "—" if m in ({}, None) else str(m)

    cab = "| Métrica | " + " | ".join(v["nome"] for v in resultado) + " |"
    sep = "|---|" + "---:|" * len(resultado)
    corpo = [f"| {rotulo} | " + " | ".join(valor(v["medidas"], ch) for v in resultado) + " |" for rotulo, ch in linhas]
    return "\n".join([cab, sep, *corpo])


def main() -> None:
    resultado = []
    for v in VERSOES:
        with tempfile.TemporaryDirectory() as tmp:
            extrair(v["rev"], tmp)
            resultado.append({**v, "medidas": medir(tmp, v["rev"])})
            print(f"{v['nome']:8} medido ({v['rev']})")
    with open(os.path.join(AQUI, "evolucao.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    with open(os.path.join(AQUI, "evolucao.md"), "w", encoding="utf-8") as f:
        f.write("# Evolução do MAPAS (gerado por medir.py)\n\n")
        f.write("\n".join(f"- **{v['nome']}** (`{v['rev']}`): {v['resumo']}" for v in VERSOES) + "\n\n")
        f.write(tabela_md(resultado) + "\n")
    print(tabela_md(resultado))


if __name__ == "__main__":
    main()
