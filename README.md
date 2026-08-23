# Code Dump Tool Android Build Host

This repository is the dedicated GitHub Actions build host for **Code Dump Tool PWA v1.1.0 ADV R7 — Capacitor Android Conversion R1**.

Authoritative source package:
`CODE_DUMP_TOOL_PWA_V1_1_0_ADV_R7_CAPACITOR_ANDROID_CONVERSION_R1_SOURCE_23082026042411.zip`

Expected source SHA-256:
`b1f0de04eab6c02ea6adc35ec74c7520dcff63b3d4c16d1ffe668fa0c71e136b`

The CI workflow verifies this SHA before extraction, runs the source verification floor, prepares the Capacitor 8.5.0 Android project, executes Gradle unit/lint/debug APK/release AAB tasks, and uploads the resulting Android artefacts.
