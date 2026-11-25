#!/usr/bin/env bash
# Demonstração da apresentação: a mesma regra de arquitetura ("só o api.ts faz HTTP") rodada
# ANTES da correção (main em 9ab1263, a v3 publicada) e DEPOIS (o código deste trabalho).
# Uso, na raiz do repositório:  bash engsoft/demo/erosao.sh
# Não altera a sua pasta de trabalho: o "antes" é montado numa pasta temporária (git worktree).
set -euo pipefail

RAIZ="$(git rev-parse --show-toplevel)"
ANTES="9ab1263"
TESTE="projeto/jogo/cliente/src/arquitetura.teste.mjs"
TMP="$(mktemp -d)"
trap 'git -C "$RAIZ" worktree remove --force "$TMP/antes" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT

rodar() {   # $1 = pasta do repositório; mostra só o resultado de cada regra e o diff da que falhar
  (cd "$1/projeto/jogo/cliente" && node --experimental-strip-types --no-warnings \
     --import ./src/mochila/testes/resolver.mjs --test src/arquitetura.teste.mjs 2>&1 \
   | grep -E "^(not )?ok|^\s+[+-] +'|^# (pass|fail)" | grep -v "núcleo puro") || true
}

echo "=== ANTES ($ANTES, v3 publicada): a regra existia só no documento ==="
git -C "$RAIZ" worktree add -q --detach "$TMP/antes" "$ANTES"
cp "$RAIZ/$TESTE" "$TMP/antes/$TESTE"
rodar "$TMP/antes"
echo
echo "=== Quem fazia HTTP por conta própria ==="
grep -n "fetch(" "$TMP/antes/projeto/jogo/cliente/src/jogo/pvpve/lobby.ts" "$TMP/antes/projeto/jogo/cliente/src/ui/progresso.ts" \
  | sed "s|$TMP/antes/projeto/jogo/cliente/src/||"
echo
echo "=== DEPOIS (este trabalho): a regra vira teste no CI ==="
rodar "$RAIZ"
