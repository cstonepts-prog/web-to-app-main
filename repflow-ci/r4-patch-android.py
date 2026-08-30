#!/usr/bin/env python3
from pathlib import Path
import re
import json

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "android/app/src/main"
MANIFEST = MAIN / "AndroidManifest.xml"

if not MANIFEST.exists():
    raise SystemExit("android project missing; run ./scripts/bootstrap-capacitor.sh first")

text = MANIFEST.read_text()

# Exact least-privilege permission allowlist used by the RepFlow native client.
permissions = [
    "android.permission.INTERNET",
    "android.permission.ACCESS_NETWORK_STATE",
    "android.permission.VIBRATE",
    "android.permission.WAKE_LOCK",
]
# Remove every existing permission declaration first, including duplicates or
# unexpected permissions introduced by generated templates/plugins.
text = re.sub(r"[ \t]*<uses-permission\b[^>]*?/?>[ \t]*", "", text)
tags = "".join(f'    <uses-permission android:name="{p}" />\n' for p in permissions)
text, count = re.subn(r"(<application\b)", tags + r"\1", text, count=1)
if count != 1:
    raise SystemExit("could not normalize Android permissions")

# Lock native application identity, launcher resources and data-backup policy.
app_match = re.search(r"<application\b[^>]*>", text, re.S)
if not app_match:
    raise SystemExit("could not locate <application> in AndroidManifest.xml")
app = app_match.group(0)
attrs = {
    "networkSecurityConfig": "@xml/network_security_config",
    "label": "@string/app_name",
    "icon": "@mipmap/ic_launcher",
    "roundIcon": "@mipmap/ic_launcher_round",
    "allowBackup": "false",
    "fullBackupContent": "false",
    "supportsRtl": "true",
}
for key, value in attrs.items():
    pattern = rf'android:{re.escape(key)}="[^"]*"'
    replacement = f'android:{key}="{value}"'
    if re.search(pattern, app):
        app = re.sub(pattern, replacement, app, count=1)
    else:
        app = app[:-1] + " " + replacement + ">"
text = text[: app_match.start()] + app + text[app_match.end() :]
MANIFEST.write_text(text)

# Lock Android release identity and SDK policy from the package release.
pkg = json.loads((ROOT / "package.json").read_text())
version_name = str(pkg.get("version") or "").strip()
m = re.fullmatch(r"\d+\.\d+\.\d+-capacitor\.(\d+)", version_name)
if not m:
    raise SystemExit(f"unsupported RepFlow Android package version: {version_name!r}")
version_code = int(m.group(1))
if version_code < 1:
    raise SystemExit("Android versionCode must be positive")

variables = ROOT / "android/variables.gradle"
if not variables.exists():
    raise SystemExit("android/variables.gradle missing")
vt = variables.read_text()
for key, value in (("minSdkVersion", 24), ("compileSdkVersion", 36), ("targetSdkVersion", 36)):
    pat = rf"({key}\s*=\s*)\d+"
    vt, count = re.subn(pat, rf"\g<1>{value}", vt, count=1)
    if count != 1:
        raise SystemExit(f"could not lock {key}")
variables.write_text(vt)

build = ROOT / "android/app/build.gradle"
if not build.exists():
    raise SystemExit("android/app/build.gradle missing")
bt = build.read_text()
bt, c1 = re.subn(r"versionCode\s+\d+", f"versionCode {version_code}", bt, count=1)
bt, c2 = re.subn(r'versionName\s+["\'][^"\']+["\']', f'versionName "{version_name}"', bt, count=1)
if c1 != 1 or c2 != 1:
    raise SystemExit("could not lock Android versionCode/versionName")
build.write_text(bt)

# Loopback-only cleartext for the Flask API; all other cleartext is denied.
network_xml = MAIN / "res/xml/network_security_config.xml"
network_xml.parent.mkdir(parents=True, exist_ok=True)
network_xml.write_text(
    """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
  <base-config cleartextTrafficPermitted="false"/>
  <domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="false">127.0.0.1</domain>
    <domain includeSubdomains="false">localhost</domain>
  </domain-config>
</network-security-config>
"""
)

# Lock visible Android app name.
strings = MAIN / "res/values/strings.xml"
st = strings.read_text()
for key in ("app_name", "title_activity_main"):
    pat = rf'(<string\s+name="{key}">).*?(</string>)'
    if re.search(pat, st, re.S):
        st = re.sub(pat, rf"\1RepFlow\2", st, count=1, flags=re.S)
strings.write_text(st)

res = MAIN / "res"
drawable = res / "drawable"
drawable.mkdir(parents=True, exist_ok=True)

# RepFlow native launcher foreground: neon waveform plus cyan ring.
foreground = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="512" android:viewportHeight="512">
    <path android:pathData="M58,276 L141,276 L166,211 L208,366 L255,131 L296,292 L325,212 L350,276 L454,276"
        android:fillColor="@android:color/transparent"
        android:strokeColor="#CAFF00" android:strokeWidth="17"
        android:strokeLineCap="round" android:strokeLineJoin="round"/>
    <path android:pathData="M256,216 A40,40 0,1 0,256,296 A40,40 0,1 0,256,216"
        android:fillColor="@android:color/transparent"
        android:strokeColor="#05C7F2" android:strokeWidth="12"
        android:strokeLineCap="round"/>
</vector>
"""
(drawable / "ic_launcher_foreground.xml").write_text(foreground)
(drawable / "ic_launcher_monochrome.xml").write_text(
    foreground.replace("#CAFF00", "#FFFFFFFF").replace("#05C7F2", "#FFFFFFFF")
)

# Legacy vector launcher for pre-adaptive-icon devices.
legacy = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="512" android:viewportHeight="512">
    <path android:pathData="M0,0 L512,0 L512,512 L0,512 Z" android:fillColor="#030914"/>
    <path android:pathData="M58,276 L141,276 L166,211 L208,366 L255,131 L296,292 L325,212 L350,276 L454,276"
        android:fillColor="@android:color/transparent"
        android:strokeColor="#CAFF00" android:strokeWidth="17"
        android:strokeLineCap="round" android:strokeLineJoin="round"/>
    <path android:pathData="M256,216 A40,40 0,1 0,256,296 A40,40 0,1 0,256,216"
        android:fillColor="@android:color/transparent"
        android:strokeColor="#05C7F2" android:strokeWidth="12"
        android:strokeLineCap="round"/>
</vector>
"""

# Remove Capacitor stock launcher resources so they cannot win resource selection.
for path in res.rglob("ic_launcher*"):
    if path.is_file() and path.parent != drawable:
        path.unlink()

base = res / "mipmap-anydpi"
base.mkdir(parents=True, exist_ok=True)
(base / "ic_launcher.xml").write_text(legacy)
(base / "ic_launcher_round.xml").write_text(legacy)

bg = res / "values/ic_launcher_background.xml"
bg.write_text(
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<resources><color name="ic_launcher_background">#030914</color></resources>\n'
)

adaptive26 = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"""
adaptive33 = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
    <monochrome android:drawable="@drawable/ic_launcher_monochrome"/>
</adaptive-icon>
"""
for qualifier, xml in (("mipmap-anydpi-v26", adaptive26), ("mipmap-anydpi-v33", adaptive33)):
    d = res / qualifier
    d.mkdir(parents=True, exist_ok=True)
    (d / "ic_launcher.xml").write_text(xml)
    (d / "ic_launcher_round.xml").write_text(xml)

print(f"configured RepFlow Android {version_name} ({version_code}), SDK 24/36, launcher icons, loopback security and exact permission allowlist")
