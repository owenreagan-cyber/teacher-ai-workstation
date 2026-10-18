#!/usr/bin/env bash
# Build and sign ChiefOfStaffEventKitReader.app (the cos M1 EventKit helper).
#
#   scripts/cos-build-eventkit-helper.sh                    # ad-hoc signature (development only)
#   scripts/cos-build-eventkit-helper.sh "Apple Development: Name (TEAMID)"
#
# Why an .app: macOS (TCC) attributes Calendar/Reminders permission to the
# responsible process. cos launches this bundle through LaunchServices (open),
# so the bundle owns the grant instead of Terminal or Raycast.
#
# Why a stable identity: TCC ties the grant to the code signature. An ad-hoc
# signature changes on every rebuild, which can orphan or reset the grant.
# Signing with an Apple Development certificate gives a designated requirement
# (bundle identifier + team) that stays the same across rebuilds.
#
# This script never reads the keychain itself. codesign does, only when a named
# identity is passed.
set -euo pipefail

identity="${1:--}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
pkg="${root}/cos/helpers/eventkit-reader"
app="${pkg}/build/ChiefOfStaffEventKitReader.app"
bundle_id="local.chief-of-staff.eventkit-reader"

swift build -c release --package-path "${pkg}"

rm -rf "${app}"
mkdir -p "${app}/Contents/MacOS"
cp "${pkg}/.build/release/eventkit-reader" "${app}/Contents/MacOS/eventkit-reader"
cp "${pkg}/App/Info.plist" "${app}/Contents/Info.plist"
plutil -lint "${app}/Contents/Info.plist" >/dev/null

codesign --force --sign "${identity}" --identifier "${bundle_id}" "${app}"
codesign --verify --strict --verbose=1 "${app}"

echo "Built: ${app}"
codesign --display --verbose=2 "${app}" 2>&1 | grep -E '^(Identifier|Authority|TeamIdentifier|Signature|CDHash)=' || true
codesign --display --requirements - "${app}" 2>&1 | grep -E 'designated' || true
if [[ "${identity}" == "-" ]]; then
  echo "NOTE: ad-hoc signature. A Calendar/Reminders grant may reset on every rebuild."
  echo "      For daily use, rebuild with your Apple Development identity:"
  echo "      security find-identity -v -p codesigning   # lists identity names"
  echo "      scripts/cos-build-eventkit-helper.sh \"Apple Development: <Name> (<TEAMID>)\""
fi
