#!/usr/bin/env bash
# تشغيل Souq Academy عبر خادم محلي بسيط (اختياري).
# التطبيق يعمل أيضًا بفتح index.html مباشرة، لكن الخادم المحلي يمنحك
# سلوك متصفح أقرب للإنتاج (وتجنّب أي قيود file:// في بعض المتصفحات).
set -euo pipefail

cd "$(dirname "$0")"
PORT="${PORT:-8080}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 غير مثبّت. افتح index.html مباشرة أو استخدم أي خادم ملفات ثابتة."
  exit 1
fi

echo "Souq Academy → http://localhost:${PORT}"
echo "اضغط Ctrl+C للإيقاف."

if command -v xdg-open >/dev/null 2>&1; then
  (sleep 1 && xdg-open "http://localhost:${PORT}" >/dev/null 2>&1 || true) &
fi

python3 -m http.server "${PORT}" --bind 127.0.0.1
