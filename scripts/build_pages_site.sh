#!/usr/bin/env bash
# Assemble the static site into a self-contained Cloudflare Pages output directory.
set -euo pipefail

: "${CHAT_API_URL:?Set CHAT_API_URL to the HTTPS API base URL before building.}"

case "$CHAT_API_URL" in
  https://*) ;;
  *)
    echo "CHAT_API_URL must use HTTPS." >&2
    exit 1
    ;;
esac

OUTPUT_DIR="${PAGES_OUTPUT_DIR:-public}"

rm -rf -- "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/widget"

# Move the website pages and their assets to the Pages document root.
cp -R website/. "$OUTPUT_DIR/"

# The website loads the widget from /widget/, so include the shared widget files.
cp widget/widget.js widget/widget.css "$OUTPUT_DIR/widget/"

# Replace the marker on every page with the API URL supplied by the Pages environment.
for page in "$OUTPUT_DIR"/*.html; do
  sed "s|__CHAT_API_URL__|$CHAT_API_URL|g" "$page" > "$page.tmp"
  mv "$page.tmp" "$page"
done

if grep -R "__CHAT_API_URL__" "$OUTPUT_DIR" --include="*.html" >/dev/null; then
  echo "A Pages HTML file still contains the API URL marker." >&2
  exit 1
fi

echo "Cloudflare Pages site assembled in: $OUTPUT_DIR"
