#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEACHER_SOURCE="${ROOT_DIR}/assets/wallpapers/teacher-mode"
CASUAL_SOURCE="${ROOT_DIR}/assets/wallpapers/casual-mode"
TEACHER_DEST="${HOME}/Pictures/Teacher OS Wallpapers/Teacher Mode"
CASUAL_DEST="${HOME}/Pictures/Teacher OS Wallpapers/Casual Anime Mode"

echo "Preparing Teacher OS wallpaper folders..."
mkdir -p "${TEACHER_DEST}" "${CASUAL_DEST}"

copy_readme_if_no_images() {
  local source_dir="$1"
  local dest_dir="$2"
  local name="$3"
  if ! find "${dest_dir}" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.heic' \) | read -r _; then
    cp "${source_dir}/README.md" "${dest_dir}/README.md"
    echo "No ${name} wallpaper images found yet. Copied a placeholder README so you know where to add images later."
  fi
}

copy_readme_if_no_images "${TEACHER_SOURCE}" "${TEACHER_DEST}" "Teacher Mode"
copy_readme_if_no_images "${CASUAL_SOURCE}" "${CASUAL_DEST}" "Casual Anime Mode"

teacher_wallpaper="$(find "${TEACHER_SOURCE}" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.heic' \) | head -n 1 || true)"
if [[ -n "${teacher_wallpaper}" ]]; then
  echo "Setting Teacher Mode wallpaper from ${teacher_wallpaper}..."
  if osascript -e "tell application \"System Events\" to tell every desktop to set picture to \"${teacher_wallpaper}\""; then
    echo "PASS: Teacher Mode wallpaper was applied."
  else
    echo "WARN: Could not set wallpaper automatically. You can set it manually in System Settings."
  fi
else
  echo "WARN: No Teacher Mode wallpaper image exists yet in assets/wallpapers/teacher-mode. Add images later when ready."
fi

echo "PASS: Wallpaper folders are ready."
