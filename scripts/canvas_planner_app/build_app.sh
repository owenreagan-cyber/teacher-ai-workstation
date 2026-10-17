#!/usr/bin/env bash
# Build the Canvas Planner macOS .app bundle and install it to ~/Applications.
#
# Idempotent: rebuilds the managed bundle and replaces only that app. Does not
# touch unrelated apps/files. Does not commit the built bundle (it is generated).
#
# Usage:
#   scripts/canvas_planner_app/build_app.sh [--install] [--dry-run]
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_DIR="${REPO_ROOT}/scripts/canvas_planner_app"

APP_DIR_NAME="Teacher Workstation - Canvas Planner.app"
APP_NAME="Teacher Workstation - Canvas Planner"
BUNDLE_ID="com.owenreagan.teacherworkstation.canvasplanner"
VERSION="1.0.0"
EXECUTABLE="CanvasPlannerLauncher"

TARGET="${HOME}/Applications/${APP_DIR_NAME}"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/canvas-planner-build.XXXXXX")"
trap 'rm -rf "${BUILD_DIR}"' EXIT

install_flag=0
dry_flag=0
for a in "$@"; do
  case "${a}" in
    --install) install_flag=1 ;;
    --dry-run) dry_flag=1 ;;
  esac
done

APP="${BUILD_DIR}/${APP_DIR_NAME}"
mkdir -p "${APP}/Contents/MacOS" "${APP}/Contents/Resources"

# ---- 1. Generate icon PNGs + .icns ---------------------------------------
ICON_SET="${BUILD_DIR}/Icon.iconset"
mkdir -p "${ICON_SET}"
python3 "${SCRIPT_DIR}/generate_icon.py" "${ICON_SET}/png" >/dev/null

icon() { cp "${ICON_SET}/png/icon_${1}x${1}.png" "${ICON_SET}/icon_${2}"; }
icon 16 "16x16.png"
icon 32 "16x16@2x.png"
icon 32 "32x32.png"
icon 64 "32x32@2x.png"
icon 128 "128x128.png"
icon 256 "128x128@2x.png"
icon 256 "256x256.png"
icon 512 "256x256@2x.png"
icon 512 "512x512.png"
icon 1024 "512x512@2x.png"

iconutil -c icns "${ICON_SET}" -o "${APP}/Contents/Resources/CanvasPlanner.icns"

# ---- 2. Info.plist --------------------------------------------------------
cat > "${APP}/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>Canvas Planner</string>
  <key>CFBundleDisplayName</key>
  <string>Teacher Workstation — Canvas Planner</string>
  <key>CFBundleIdentifier</key>
  <string>${BUNDLE_ID}</string>
  <key>CFBundleVersion</key>
  <string>${VERSION}</string>
  <key>CFBundleShortVersionString</key>
  <string>${VERSION}</string>
  <key>CFBundleExecutable</key>
  <string>${EXECUTABLE}</string>
  <key>CFBundleIconFile</key>
  <string>CanvasPlanner.icns</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>LSApplicationCategoryType</key>
  <string>public.app-category.education</string>
</dict>
</plist>
PLIST

# ---- 3. Executable --------------------------------------------------------
cp "${SCRIPT_DIR}/launcher.sh" "${APP}/Contents/MacOS/${EXECUTABLE}"
chmod +x "${APP}/Contents/MacOS/${EXECUTABLE}"

# ---- 4. Ad-hoc signing (local personal use; no cert/secrets) --------------
codesign --force --deep --sign - "${APP}" >/dev/null 2>&1 || true

# ---- 5. Validate ----------------------------------------------------------
plutil -lint "${APP}/Contents/Info.plist" >/dev/null
[ -f "${APP}/Contents/Resources/CanvasPlanner.icns" ]
[ -x "${APP}/Contents/MacOS/${EXECUTABLE}" ]

if [ "${dry_flag}" = "1" ]; then
  echo "Built (dry-run, not installed): ${APP}"
  echo "  bundle id: ${BUNDLE_ID}"
  echo "  version: ${VERSION}"
  echo "  executable: ${EXECUTABLE}"
  echo "  icon: CanvasPlanner.icns (present)"
  exit 0
fi

if [ "${install_flag}" = "1" ]; then
  mkdir -p "${HOME}/Applications"
  # Replace only this managed app; never delete unrelated files.
  rm -rf "${TARGET}"
  cp -R "${APP}" "${TARGET}"
  # Re-sign the installed copy (the cp may strip the extended-attribute signature).
  codesign --force --deep --sign - "${TARGET}" >/dev/null 2>&1 || true
  echo "Installed: ${TARGET}"
  echo "  Bundle id: ${BUNDLE_ID}"
  echo "  Version: ${VERSION}"
  echo "  Open with: open \"${TARGET}\""
else
  echo "Built (not installed): ${APP}"
  echo "  Re-run with --install to place in ~/Applications."
fi
