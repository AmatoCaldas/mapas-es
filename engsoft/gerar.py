"""Gera os PDFs do trabalho de DCC061 (Engenharia de Software): documento-texto e slides.

Uso (na raiz do repositório):
    python3 engsoft/gerar.py              # documento e slides
    python3 engsoft/gerar.py documento    # só o documento
    python3 engsoft/gerar.py slides       # só os slides

Saída em engsoft/saida/ (fora do git). Precisa do Google Chrome ou Chromium (impressão em PDF
sem cabeçalho); se ele estiver noutro lugar, aponte com a variável CHROME. Os números da evolução
vêm de engsoft/evolucao/evolucao.json (gerado por engsoft/evolucao/medir.py).

Marcadores aceitos nas seções (documento/secoes/*.html) e nos slides:
    {{FIG:arquivo.svg|legenda}}   figura de engsoft/figuras, numerada
    {{IMG:caminho/da/imagem}}     (slides) imagem embutida, caminho a partir da raiz do repositório
    {{TABELA_EVOLUCAO}}           tabela das 3 medidas por versão (escala e as duas fronteiras)
"""
from __future__ import annotations

import base64
import html
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SECOES = os.path.join(AQUI, "documento", "secoes")
FIGURAS = os.path.join(AQUI, "figuras")
SAIDA = os.path.join(AQUI, "saida")
EVOLUCAO = os.path.join(AQUI, "evolucao", "evolucao.json")
GRUPO = os.path.join(AQUI, "grupo.txt")

CHROMES = [
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("chromium-browser") or "",
]
TEORIA = ("20_", "30_")                 # capítulos teóricos: fonte "a partir das referências citadas"


# ------------------------------------------------------------------ utilidades
def ler(caminho: str) -> str:
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def chrome() -> str:
    for c in CHROMES:
        if c and os.path.exists(c):
            return c
    sys.exit("Chrome/Chromium não encontrado. Defina a variável CHROME com o caminho do executável.")


def imprimir_pdf(html_caminho: str, pdf_caminho: str) -> None:
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=5000",
                    f"--print-to-pdf={pdf_caminho}", "file://" + html_caminho],
                   check=True, capture_output=True)
    print(f"  → {os.path.relpath(pdf_caminho)}")


def evolucao() -> list[dict]:
    if not os.path.exists(EVOLUCAO):
        sys.exit("Falta engsoft/evolucao/evolucao.json: rode antes .venv/bin/python engsoft/evolucao/medir.py")
    return json.loads(ler(EVOLUCAO))


def svg_inline(nome: str) -> str:
    svg = ler(os.path.join(FIGURAS, nome))
    return re.sub(r"<svg ", '<svg role="img" ', svg, count=1)


def img_inline(caminho: str) -> str:
    """Imagem (caminho relativo à raiz do repositório) embutida como data URI: o PDF não depende de pasta."""
    tipo = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}[caminho.rsplit(".", 1)[-1].lower()]
    with open(os.path.join(RAIZ, caminho), "rb") as f:
        return f"data:{tipo};base64,{base64.b64encode(f.read()).decode()}"


def fmt(n) -> str:
    if isinstance(n, float):
        return f"{n:.1f}".replace(".", ",") if n >= 10 else f"{n:.2f}".replace(".", ",")
    if isinstance(n, bool):
        return "sim" if n else "não"
    if isinstance(n, int):
        return f"{n:,}".replace(",", ".")
    return html.escape(str(n))


# ------------------------------------------------------------------ evolução: 3 medidas, uma conclusão
# Linhas de código dão a escala; as outras duas dizem se as fronteiras sobreviveram ao crescimento
# (ADR-0002 no servidor, ADR-0003 no cliente). Crescimento sozinho não diz nada sobre qualidade.
LINHAS_TABELA = [
    ("Linhas de código (servidor + cliente)", "loc_total"),
    ("Módulos do servidor que acessam o banco direto (esperado: 1)", "modulos_banco"),
    ("Arquivos do cliente que fazem HTTP (esperado: 1)", "arquivos_http"),
]


def _valor(m: dict, chave: str):
    for parte in chave.split("."):
        m = m.get(parte) if isinstance(m, dict) else None
    return len(m) if isinstance(m, list) else m


def tabela_evolucao(com_legenda: bool = True) -> str:
    dados = evolucao()
    cab = "".join(f"<th>{html.escape(v['nome'])}</th>" for v in dados)
    corpo = "".join(
        f"<tr><td>{html.escape(rotulo)}</td>" + "".join(f"<td class='num'>{fmt(_valor(v['medidas'], ch))}</td>" for v in dados) + "</tr>"
        for rotulo, ch in LINHAS_TABELA)
    legenda = ("<caption class='tabela'>Escala do sistema e respeito às duas fronteiras, por versão</caption>"
               if com_legenda else "")
    return f"<table class='evolucao'>{legenda}<thead><tr><th>Medida</th>{cab}</tr></thead><tbody>{corpo}</tbody></table>"


# ------------------------------------------------------------------ documento
def numerar(secoes: list[tuple[str, str]]) -> tuple[str, list[tuple[int, str, str]]]:
    """Numera capítulos/seções, figuras, quadros e tabelas; devolve o HTML e o sumário."""
    sumario, saida = [], []
    cap = sec = sub = fig = quadro = tab = 0
    for nome, fragmento in secoes:
        fonte = ("Fonte: elaborado pelos autores a partir das referências citadas." if nome.startswith(TEORIA)
                 else "Fonte: elaborado pelos autores.")

        def titulo(m: re.Match) -> str:
            nonlocal cap, sec, sub
            nivel, texto = int(m.group(1)), m.group(2)
            if nivel == 2:
                cap, sec, sub = cap + 1, 0, 0
                num = f"{cap}"
            elif nivel == 3:
                sec, sub = sec + 1, 0
                num = f"{cap}.{sec}"
            else:
                sub += 1
                num = f"{cap}.{sec}.{sub}"
            ancora = f"s{num.replace('.', '-')}"
            if nivel < 4:
                sumario.append((nivel, num, re.sub("<[^>]+>", "", texto)))
            return f'<h{nivel} id="{ancora}"><span class="num">{num}</span> {texto}</h{nivel}>'

        fragmento = re.sub(r"<h([234])>(.*?)</h\1>", titulo, fragmento)

        def figura(m: re.Match, fonte: str = fonte) -> str:
            nonlocal fig
            fig += 1
            arquivo, legenda = m.group(1).split("|", 1)
            return (f'<figure><figcaption>Figura {fig} – {legenda}</figcaption>{svg_inline(arquivo)}'
                    f'<p class="fonte">{fonte}</p></figure>')

        fragmento = re.sub(r"\{\{FIG:([^}]+)\}\}", figura, fragmento)
        fragmento = fragmento.replace("{{TABELA_EVOLUCAO}}", tabela_evolucao())

        def legenda_tabela(m: re.Match) -> str:
            nonlocal quadro, tab
            classe, texto = m.group(1) or "", re.sub(r"^\s*Quadro:\s*", "", m.group(2))
            if "tabela" in classe:
                tab += 1
                rotulo = f"Tabela {tab}"
            else:
                quadro += 1
                rotulo = f"Quadro {quadro}"
            return f"<caption>{rotulo} – {texto}</caption>"

        fragmento = re.sub(r"<caption( class='[^']*')?>(.*?)</caption>", legenda_tabela, fragmento)
        fragmento = re.sub(r"(</table>)", rf'\1<p class="fonte">{fonte}</p>', fragmento)
        saida.append(f'<section class="capitulo">{fragmento}</section>')
    return "\n".join(saida), sumario


def _sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()


def _autor_e_ano(chave: str, texto: str) -> tuple[str, str]:
    """Primeiro autor (como aparece na citação) e ano com letra, a partir da chave (bass2021, iso2023a)."""
    autor = re.split(r"[.,;]", texto, maxsplit=1)[0]
    ano = re.search(r"(\d{4}[a-z]?|20xx)$", chave).group(1).replace("20xx", "[20--]")
    return _sem_acento(autor).strip(), ano.upper()          # o corpo também é comparado em maiúsculas


def _citada(autor: str, ano: str, corpo: str) -> bool:
    """A obra é citada se o sobrenome aparece e o ano vem logo depois, na mesma citação."""
    return any(ano in corpo[m.end():m.end() + 160] for m in re.finditer(re.escape(autor), corpo))


def referencias(texto_do_corpo: str) -> str:
    """Só as obras citadas no texto (NBR 6023), em ordem alfabética. Avisa o que ficou de fora e as
    citações sem referência, para conferir à mão."""
    entradas = {}
    for arquivo in ("referencias_teoria.txt", "referencias_caso.txt"):
        caminho = os.path.join(SECOES, arquivo)
        if os.path.exists(caminho):
            for linha in ler(caminho).splitlines():
                if "|" in linha:
                    chave, texto = linha.split("|", 1)
                    entradas[chave.strip()] = texto.strip()
    corpo = _sem_acento(html.unescape(re.sub(r"<[^>]+>", " ", texto_do_corpo)))
    corpo = re.sub(r"\s+", " ", corpo)
    citadas = {c: t for c, t in entradas.items() if _citada(*_autor_e_ano(c, t), corpo)}
    fora = sorted(set(entradas) - set(citadas))
    if fora:
        print(f"  referências não citadas (fora da lista): {', '.join(fora)}")
    autores = {_autor_e_ano(c, t)[0].split()[0] for c, t in entradas.items()}
    # cada "AUTOR; COAUTOR, ANO" dentro de parênteses; confere só o primeiro autor
    grupos = [g.group(1).split(";")[0].strip() for m in re.finditer(r"\(([A-Z][^()]*?(?:\d{4}[A-Z]?|\[20--\]))\)", corpo)
              for g in re.finditer(r"([A-Z][A-Z .;'-]*?)(?: ET AL\.)?,\s*(?:\d{4}[A-Z]?|\[20--\])", m.group(1))]
    sem_ref = sorted({g for g in grupos if g.split()[0] not in autores})
    if sem_ref:
        print(f"  ATENÇÃO, citação sem referência? {', '.join(sem_ref)}")
    itens = "".join(f"<p class='ref'>{html.escape(t)}</p>" for t in sorted(citadas.values(), key=_sem_acento))
    print(f"  {len(citadas)} referências citadas")
    return f'<section class="capitulo"><h2 class="sem-numero">Referências</h2>{itens}</section>'


def integrantes_do_grupo() -> list[str]:
    """Linhas de engsoft/grupo.txt (`Nome completo — matrícula`), sem comentários; vazio se não houver."""
    if not os.path.exists(GRUPO):
        return []
    return [linha.strip() for linha in ler(GRUPO).splitlines() if linha.strip() and not linha.startswith("#")]


def capa() -> str:
    nomes = integrantes_do_grupo() or ["[Nome completo — matrícula]"] * 3
    integrantes = "".join(f"<div>{html.escape(n)}</div>" for n in nomes)
    return f"""
<section class="capa">
  <div class="topo">UNIVERSIDADE FEDERAL DE JUIZ DE FORA<br>INSTITUTO DE CIÊNCIAS EXATAS<br>DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO<br>
  DCC061 – ENGENHARIA DE SOFTWARE</div>
  <div class="integrantes">{integrantes}</div>
  <div class="titulo">ARQUITETURA DE SOFTWARE E QUALIDADE DE SOFTWARE:<br>
  <span>um estudo de caso com o MAPAS, jogo cooperativo em que o banco de dados é o árbitro</span></div>
  <div class="prof">Trabalho prático apresentado à disciplina DCC061 – Engenharia de Software,
  ministrada pelo Prof. Fabrício Martins Mendonça.</div>
  <div class="rodape">JUIZ DE FORA<br>2026</div>
</section>"""


def montar_documento() -> None:
    nomes = sorted(n for n in os.listdir(SECOES) if n.endswith(".html"))
    corpo, sumario = numerar([(n, ler(os.path.join(SECOES, n))) for n in nomes])
    itens = "".join(
        f'<li class="n{nivel}"><a href="#s{num.replace(".", "-")}"><span>{num}</span> {html.escape(t.upper() if nivel == 2 else t)}</a></li>'
        for nivel, num, t in sumario)
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>DCC061 – Arquitetura e Qualidade de Software – MAPAS</title>
<style>{ler(os.path.join(AQUI, "documento", "base.css"))}</style></head><body>
{capa()}
<section class="sumario"><h2 class="sem-numero">Sumário</h2><ol>{itens}<li class="n2"><a href="#ref"><span></span> REFERÊNCIAS</a></li></ol></section>
{corpo}
{referencias(corpo).replace('<h2 class="sem-numero">', '<h2 class="sem-numero" id="ref">', 1)}
</body></html>"""
    os.makedirs(SAIDA, exist_ok=True)
    destino = os.path.join(SAIDA, "documento.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(pagina)
    imprimir_pdf(destino, os.path.join(SAIDA, "DCC061_Arquitetura_Qualidade_MAPAS.pdf"))


# ------------------------------------------------------------------ slides
def montar_slides() -> None:
    fonte = ler(os.path.join(AQUI, "slides", "slides.html"))
    fonte = re.sub(r"\{\{FIG:([^}|]+)(\|[^}]*)?\}\}", lambda m: svg_inline(m.group(1)), fonte)
    fonte = re.sub(r"\{\{IMG:([^}]+)\}\}", lambda m: img_inline(m.group(1)), fonte)
    fonte = fonte.replace("{{TABELA_EVOLUCAO}}", tabela_evolucao(com_legenda=False))
    nomes = [re.split(r"\s+[—–-]\s+", n)[0] for n in integrantes_do_grupo()]   # nos slides, sem matrícula
    fonte = fonte.replace("{{INTEGRANTES}}", " · ".join(map(html.escape, nomes)) or "[Integrantes do grupo]")
    os.makedirs(SAIDA, exist_ok=True)
    destino = os.path.join(SAIDA, "slides.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(fonte)
    imprimir_pdf(destino, os.path.join(SAIDA, "DCC061_Slides_MAPAS.pdf"))


if __name__ == "__main__":
    alvos = sys.argv[1:] or ["documento", "slides"]
    if "documento" in alvos:
        print("documento-texto")
        montar_documento()
    if "slides" in alvos:
        print("slides")
        montar_slides()
