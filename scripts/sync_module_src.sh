#!/usr/bin/env bash
# Refresh a module's vendored src/ copy from its own GitHub repository's main branch.
#
# Usage: scripts/sync_module_src.sh Module_2
set -euo pipefail

MODULE="${1:?usage: sync_module_src.sh <Module_2|Module_3|Module_4>}"

declare -A REPO_URLS=(
  [Module_2]="https://github.com/minnocent12/csc8830-module-2.git"
  [Module_3]="https://github.com/minnocent12/csc8830-module-3.git"
  [Module_4]="https://github.com/minnocent12/csc8830-module-4.git"
)

URL="${REPO_URLS[$MODULE]:?unknown module: $MODULE}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --depth 1 "$URL" "$TMP/checkout"
rm -rf "$ROOT/$MODULE/src"
cp -r "$TMP/checkout/src" "$ROOT/$MODULE/src"

echo "Synced $MODULE/src from $URL"
