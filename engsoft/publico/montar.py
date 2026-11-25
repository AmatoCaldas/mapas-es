"""Monta o recorte público do MAPAS para a entrega da DCC061 (repositório mapas-es).

Copia só o que está em PERMITIDOS (lista explícita: o que não está aqui não sai), gera os anexos (PDFs,
trecho da regra RN13, diff da correção, saída da demonstração), marca os links para arquivos retirados e
varre tudo atrás de dado sensível. Se a varredura achar algo, o script falha e não há o que publicar.

Uso, na raiz do repositório completo (o destino é recriado; a pasta .git dele é preservada):
    .venv/bin/python engsoft/publico/montar.py [destino]       # padrão: ../mapas-es
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DESTINO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "..", "mapas-es"))

PERMITIDOS = [
    "engsoft",
    "projeto/jogo/docs/arquitetura",
    "projeto/jogo/docs/qualidade",
    "projeto/jogo/servidor/motor/banco.py",
    "projeto/jogo/servidor/testes/test_arquitetura.py",
    "projeto/jogo/servidor/ruff.toml",
    "projeto/jogo/servidor/.coveragerc",
    "projeto/jogo/servidor/sql/PUBLICADAS.sha256",
    "projeto/jogo/cliente/src/api.ts",
    "projeto/jogo/cliente/src/arquitetura.teste.mjs",
    "projeto/jogo/cliente/package.json",
    "projeto/jogo/cliente/public/assets/ui/fundo_menu.png",   # capa dos slides
    "projeto/jogo/cliente/public/assets/ui/logo.png",
]
IGNORAR = {"saida", "__pycache__", ".DS_Store"}
RENOMEAR = {".github/workflows/ci.yml": ".github/ci-do-repositorio-completo.yml"}  # fora de workflows: não roda

ANTES = "9ab1263"   # v3 publicada, antes da correção da erosão
CORRIGIDOS = ["projeto/jogo/cliente/src/jogo/pvpve/lobby.ts", "projeto/jogo/cliente/src/ui/progresso.ts"]
MIGRACAO = "projeto/jogo/servidor/sql/21_golpes.sql"
TRECHO = "projeto/jogo/servidor/sql/TRECHO_21_golpes_RN13.sql"

SENSIVEIS = {
    "empresa/infra": r"(?i)tremed|nck\.ia|publicar\.sh|DEPLOY\.md|\bssh\b",
    "senha de teste": r"mapas2026",
    "e-mail pessoal": r"(?i)@(gmail|hotmail|outlook|yahoo)\.",
    "caminho local": r"/Users/|C:[\\/]Users|joaovitor|MacBook",
    "chave/token": r"BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}",
    "endereço IP": r"\b(?!127\.0\.0\.1\b|0\.0\.0\.0\b)(?:\d{1,3}\.){3}\d{1,3}\b",
}


def limpar_destino() -> None:
    os.makedirs(DESTINO, exist_ok=True)
    for nome in os.listdir(DESTINO):
        if nome == ".git":
            continue
        caminho = os.path.join(DESTINO, nome)
        shutil.rmtree(caminho) if os.path.isdir(caminho) else os.remove(caminho)


def copiar(relativo: str, destino_rel: str | None = None) -> None:
    origem = os.path.join(RAIZ, relativo)
    alvo = os.path.join(DESTINO, destino_rel or relativo)
    if not os.path.exists(origem):
        sys.exit(f"falta na lista permitida: {relativo}")
    if os.path.isdir(origem):
        shutil.copytree(origem, alvo, ignore=shutil.ignore_patterns(*IGNORAR))
    else:
        os.makedirs(os.path.dirname(alvo), exist_ok=True)
        shutil.copy2(origem, alvo)


def escrever(relativo: str, texto: str) -> None:
    alvo = os.path.join(DESTINO, relativo)
    os.makedirs(os.path.dirname(alvo), exist_ok=True)
    with open(alvo, "w", encoding="utf-8") as f:
        f.write(texto)


def rodar(*comando: str) -> str:
    return subprocess.run(comando, cwd=RAIZ, check=True, capture_output=True, text=True).stdout


def trecho_rn13() -> str:
    """Da função fn_processar_jogada até a checagem de alcance (RN13), com cabeçalho dizendo de onde veio."""
    with open(os.path.join(RAIZ, MIGRACAO), encoding="utf-8") as f:
        linhas = f.read().splitlines()
    inicio = next(i for i, ln in enumerate(linhas) if ln.startswith("-- RN12, RN13"))
    alcance = next(i for i, ln in enumerate(linhas) if "RN13: o alvo está a" in ln)
    fim = next(i for i in range(alcance, len(linhas)) if linhas[i].strip() == "END IF;")
    cabecalho = (f"-- TRECHO de {MIGRACAO}, linhas {inicio + 1}–{fim + 1} (recorte público da DCC061).\n"
                 "-- Mostra a Decisão 1: a jogada é validada num gatilho do PostgreSQL, com travas de linha\n"
                 "-- (FOR UPDATE) contra jogadas simultâneas e recusa identificada pelo código da regra (RNxx).\n"
                 "-- O restante da função (aplicação do efeito) e as demais migrações ficam no repositório completo.\n\n")
    return cabecalho + "\n".join(linhas[inicio:fim + 1]) + "\n    -- … (continua no repositório completo)\n"


def marcar_links_quebrados() -> None:
    """Link markdown para arquivo que não veio no recorte vira texto com a marca *(repositório completo)*."""
    link = re.compile(r"\[([^\]]+)\]\(([^)#\s]+)(#[^)]*)?\)")
    for pasta, _, arquivos in os.walk(DESTINO):
        if ".git" in pasta.split(os.sep):
            continue
        for nome in (a for a in arquivos if a.endswith(".md")):
            caminho = os.path.join(pasta, nome)
            with open(caminho, encoding="utf-8") as f:
                texto = f.read()

            def trocar(m: re.Match, pasta: str = pasta) -> str:
                alvo = m.group(2)
                if re.match(r"[a-z]+:", alvo):
                    return m.group(0)
                for velho, novo in RENOMEAR.items():
                    if alvo.endswith(velho):
                        alvo = alvo[: -len(velho)] + novo
                if os.path.exists(os.path.normpath(os.path.join(pasta, alvo))):
                    return f"[{m.group(1)}]({alvo}{m.group(3) or ''})"
                return f"{m.group(1)} *(repositório completo)*"

            with open(caminho, "w", encoding="utf-8") as f:
                f.write(link.sub(trocar, texto))


def textos_para_varrer():
    for pasta, _, arquivos in os.walk(DESTINO):
        if ".git" in pasta.split(os.sep):
            continue
        for nome in arquivos:
            caminho = os.path.join(pasta, nome)
            if nome.endswith(".pdf"):
                yield caminho, texto_do_pdf(caminho)
                continue
            try:
                with open(caminho, encoding="utf-8") as f:
                    yield caminho, f.read()
            except UnicodeDecodeError:
                continue   # imagem: não tem texto


def texto_do_pdf(caminho: str) -> str:
    import pypdfium2   # vem com o .venv do engsoft
    pdf = pypdfium2.PdfDocument(caminho)
    return "\n".join(pagina.get_textpage().get_text_range() for pagina in pdf)


def varrer() -> list[str]:
    achados = []
    for caminho, texto in textos_para_varrer():
        if os.path.basename(caminho) == "montar.py":
            continue   # este arquivo contém os próprios padrões
        for rotulo, padrao in SENSIVEIS.items():
            for m in re.finditer(padrao, texto):
                linha = texto.count("\n", 0, m.start()) + 1
                achados.append(f"{os.path.relpath(caminho, DESTINO)}:{linha}: {rotulo} → {m.group(0)!r}")
    return achados


def main() -> None:
    print("PDFs…");                    rodar(sys.executable, "engsoft/gerar.py")
    limpar_destino()
    for item in PERMITIDOS:
        copiar(item)
    for velho, novo in RENOMEAR.items():
        copiar(velho, novo)
    shutil.copy2(os.path.join(AQUI, "LEIAME.md"), os.path.join(DESTINO, "README.md"))
    os.remove(os.path.join(DESTINO, "engsoft", "publico", "LEIAME.md"))   # já virou o README
    os.makedirs(os.path.join(DESTINO, "entrega"))
    for pdf in sorted(os.listdir(os.path.join(RAIZ, "engsoft", "saida"))):
        if pdf.endswith(".pdf"):
            shutil.copy2(os.path.join(RAIZ, "engsoft", "saida", pdf), os.path.join(DESTINO, "entrega", pdf))
    escrever(TRECHO, trecho_rn13())
    escrever("engsoft/demo/correcao.diff", rodar("git", "diff", ANTES, "--", *CORRIGIDOS))
    print("demonstração…");            escrever("engsoft/demo/saida_erosao.txt", rodar("bash", "engsoft/demo/erosao.sh"))
    escrever(".gitignore", "engsoft/saida/\n__pycache__/\n.DS_Store\n")
    marcar_links_quebrados()

    achados = varrer()
    if achados:
        print("\n".join(achados))
        sys.exit(f"\n{len(achados)} possível(is) dado(s) sensível(is): nada a publicar até resolver.")
    total = sum(1 for _ in textos_para_varrer())
    print(f"→ {DESTINO}: {total} arquivos de texto/PDF, varredura limpa")


if __name__ == "__main__":
    main()
