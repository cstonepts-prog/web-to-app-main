#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
npm install
CAP="$ROOT/node_modules/.bin/cap"
[[ -x "$CAP" ]] || { echo "Capacitor CLI missing after npm install" >&2; exit 1; }
if [[ ! -d android ]]; then "$CAP" add android; fi
"$CAP" sync android
python "$ROOT/scripts/patch-android.py"
printf '\nCapacitor Android project ready.\nBuild debug APK: cd android && ./gradlew assembleDebug\n'
