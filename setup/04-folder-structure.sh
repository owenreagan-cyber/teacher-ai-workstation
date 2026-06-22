#!/usr/bin/env bash
set -euo pipefail

echo "Creating workstation folders..."

# 3D printing notes:
# Business is for original or properly licensed commercial product work.
# Classroom is for teaching tools, fidgets, prizes, manipulatives, and classroom organization.
# Personal is for private/non-commercial projects.
# Reference-Only is for inspiration, downloaded examples, personal-use references,
# screenshots, photos, or items that should not automatically become commercial products.
#
# WARNING: Files in Reference-Only are NOT assumed commercial-safe. Do not copy
# them into Business/ or use them for sale without human IP/license review. This
# warning is advisory and does not block printing.

mkdir -p \
  "${HOME}/Projects" \
  "${HOME}/Projects/teacher-ai-workstation" \
  "${HOME}/Teaching" \
  "${HOME}/Teaching/Curriculum" \
  "${HOME}/Teaching/Canvas" \
  "${HOME}/Teaching/Worksheets" \
  "${HOME}/Teaching/Presentations" \
  "${HOME}/Teaching/Review-Games" \
  "${HOME}/Teaching/Print-Certified" \
  "${HOME}/Teaching/Artifacts" \
  "${HOME}/Teaching/Templates" \
  "${HOME}/AI" \
  "${HOME}/AI/Models" \
  "${HOME}/AI/Prompts" \
  "${HOME}/AI/Exports" \
  "${HOME}/Notes" \
  "${HOME}/Screenshots" \
  "${HOME}/Media" \
  "${HOME}/Archive" \
  "${HOME}/3D-Printing" \
  "${HOME}/3D-Printing/Business" \
  "${HOME}/3D-Printing/Classroom" \
  "${HOME}/3D-Printing/Personal" \
  "${HOME}/3D-Printing/Intake" \
  "${HOME}/3D-Printing/Designs" \
  "${HOME}/3D-Printing/Designs/OpenSCAD" \
  "${HOME}/3D-Printing/Designs/STL" \
  "${HOME}/3D-Printing/Designs/3MF" \
  "${HOME}/3D-Printing/Print-Profiles" \
  "${HOME}/3D-Printing/Prototype-Logs" \
  "${HOME}/3D-Printing/Product-Catalog" \
  "${HOME}/3D-Printing/Photos" \
  "${HOME}/3D-Printing/Licenses" \
  "${HOME}/3D-Printing/Reference-Only"

echo "PASS: Workstation folders created."
