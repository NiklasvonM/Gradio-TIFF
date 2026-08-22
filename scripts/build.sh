#!/usr/bin/env bash
#
# Build a release wheel of gradio_tiff.
#
# ---------------------------------------------------------------------------
# Setup
#
#   uv venv
#   source .venv/bin/activate
#   uv pip install -e . --group dev
#   ( cd frontend && npm install )
#   playwright install chromium         # only needed for the smoke test
#   bash scripts/build.sh && python demo/app.py

set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# `ruff` must be on PATH: `gradio cc docs` shells out to it and silently emits a
# degraded DOCS.md without it. The `build` dependency group provides it.
if ! command -v ruff >/dev/null; then
  echo "error: ruff not found on PATH; run: uv pip install -e . --group dev" >&2
  exit 1
fi

echo "==> gradio cc build --no-generate-docs"
gradio cc build --no-generate-docs

echo "==> gradio cc docs --readme-path DOCS.md"
gradio cc docs --readme-path DOCS.md

echo "==> done. Artifacts in dist/"
ls -1 dist/ | tail -n 4
