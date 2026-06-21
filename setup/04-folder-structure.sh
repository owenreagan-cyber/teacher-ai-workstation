#!/usr/bin/env bash
set -euo pipefail

echo "Creating workstation folders..."

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
  "${HOME}/Archive"

echo "PASS: Workstation folders created."
