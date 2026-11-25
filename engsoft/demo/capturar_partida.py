"""Captura a tela da partida usada nos slides (engsoft/figuras/partida.jpg), sem servidor nem banco.

Usa a cena de teste do cliente (src/jogo/cena-teste.html, com servidor simulado), esconde o painel de
teste e a dica, e tira o print em 2560×1440 pelo protocolo de depuração do Chrome.

Uso, com o Vite no ar (cd projeto/jogo/cliente && npm run dev) e na raiz do repositório:
    .venv/bin/python engsoft/demo/capturar_partida.py
Precisa do pacote websockets (já vem com as dependências do servidor) e do Pillow.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import time
import urllib.request
from io import BytesIO

from PIL import Image
from websockets.sync.client import connect

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(os.path.dirname(AQUI), "figuras", "partida.jpg")
URL = os.environ.get("MAPAS_CENA", "http://localhost:5173/src/jogo/cena-teste.html")
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
PORTA = 9339
ESPERA_CENA_S = 9                     # a cena carrega sprites e toca a entrada da câmera

LIMPAR = """
  if (!document.getElementById('limpo')) { const st = document.createElement('style'); st.id = 'limpo';
    st.textContent = '#painel-teste{display:none!important}'; document.head.appendChild(st); }
  for (const b of document.querySelectorAll('button')) if (/^Teste/.test(b.textContent.trim())) b.style.display = 'none';
  const link = [...document.querySelectorAll('button,a,span')].find(e => e.textContent.trim() === 'Não mostrar mais dicas');
  let el = link; while (el && el.parentElement && !el.textContent.includes('pulsando')) el = el.parentElement;
  if (el && el !== document.body) el.style.display = 'none';"""


class Cdp:
    """Cliente mínimo do Chrome DevTools Protocol: um comando por vez, espera a resposta."""

    def __init__(self, ws):
        self.ws, self.n = ws, 0

    def __call__(self, metodo: str, **params) -> dict:
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": metodo, "params": params}))
        while True:
            resposta = json.loads(self.ws.recv())
            if resposta.get("id") == self.n:
                if "error" in resposta:
                    raise RuntimeError(f"{metodo}: {resposta['error']}")
                return resposta.get("result", {})


def pagina_do_chrome() -> str:
    for _ in range(50):
        try:
            alvos = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/json/list"))
            return next(a["webSocketDebuggerUrl"] for a in alvos if a["type"] == "page")
        except (OSError, StopIteration):
            time.sleep(0.2)
    raise SystemExit("o Chrome não abriu a porta de depuração")


def main() -> None:
    with tempfile.TemporaryDirectory() as perfil:
        chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORTA}", "--no-first-run",
                                   f"--user-data-dir={perfil}", "about:blank"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            with connect(pagina_do_chrome(), max_size=50_000_000) as ws:
                cdp = Cdp(ws)
                cdp("Emulation.setDeviceMetricsOverride", width=1280, height=720, deviceScaleFactor=2, mobile=False)
                cdp("Page.navigate", url=URL)
                time.sleep(ESPERA_CENA_S)
                for _ in range(4):                       # a interface recria o painel e a dica: insiste
                    cdp("Runtime.evaluate", expression=LIMPAR)
                    time.sleep(0.7)
                png = base64.b64decode(cdp("Page.captureScreenshot", format="png")["data"])
        finally:
            chrome.terminate()
    imagem = Image.open(BytesIO(png)).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    imagem.save(SAIDA, quality=86, optimize=True, progressive=True)
    print(f"→ {os.path.relpath(SAIDA)}")


if __name__ == "__main__":
    main()
