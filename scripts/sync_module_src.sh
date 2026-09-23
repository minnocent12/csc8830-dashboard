#!/usr/bin/env bash
# Refresh a module's vendored copy (src/, data/, results/, docs/) from its own GitHub
# repository's main branch. Only files that module already committed to its own repo are
# pulled in, so nothing gitignored (raw personal photos, generated reports) is exposed here.
#
# Usage: scripts/sync_module_src.sh Module_2
set -euo pipefail

MODULE="${1:?usage: sync_module_src.sh <Module_2|Module_3|Module_4>}"

case "$MODULE" in
  Module_2) URL="https://github.com/minnocent12/csc8830-module-2.git" ;;
  Module_3) URL="https://github.com/minnocent12/csc8830-module-3.git" ;;
  Module_4) URL="https://github.com/minnocent12/csc8830-module-4.git" ;;
  *) echo "unknown module: $MODULE" >&2; exit 1 ;;
esac
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --depth 1 "$URL" "$TMP/checkout"
for dir in src data results docs; do
  rm -rf "$ROOT/$MODULE/$dir"
  if [ -d "$TMP/checkout/$dir" ]; then
    cp -r "$TMP/checkout/$dir" "$ROOT/$MODULE/$dir"
  fi
done

echo "Synced $MODULE (src, data, results, docs) from $URL"
