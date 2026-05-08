#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f "$ROOT_DIR/docs/cv.html" ]]; then
  echo "docs/cv.html not found. Run 'quarto render' first." >&2
  exit 1
fi

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --disable-gpu \
  --allow-file-access-from-files \
  --print-to-pdf="docs/cv.pdf" \
  --no-pdf-header-footer \
  "file://$ROOT_DIR/docs/cv.html"

echo "Styled PDF created at docs/cv.pdf"
