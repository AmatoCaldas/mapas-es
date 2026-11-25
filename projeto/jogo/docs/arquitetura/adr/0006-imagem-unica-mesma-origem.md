# ADR-0006 — Uma imagem só: página, API e WebSocket na mesma origem

**Status:** aceito (v1, 03/10/2026)

## Contexto
Um servidor pequeno, com proxy reverso (Traefik) e um PostgreSQL já existente; time pequeno.

## Decisão
O `Dockerfile` tem dois estágios: o primeiro faz `tsc` + `vite build` do cliente; o segundo é a imagem Python
que serve os arquivos estáticos, a API REST e o WebSocket no mesmo processo. Na subida, `migrar.py` roda antes
do servidor. O banco é um banco isolado, com role própria sem superusuário.

## Consequências
- (+) Sem CORS, `wss://` automático, um artefato só para versionar e reverter.
- (+) O build do cliente roda a checagem de tipos: imagem com erro de tipo nem é gerada.
- (−) Escala horizontal exigiria tirar o estado das salas da memória do processo (hoje não é necessário).
