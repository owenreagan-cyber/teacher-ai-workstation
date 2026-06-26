#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/create-developer-project.sh TEMPLATE_NAME PROJECT_SLUG

Allowed TEMPLATE_NAME values:
  local-script-tool
  lesson-helper
  checklist-generator
  rubric-helper
  mini-app-plan

PROJECT_SLUG must use lowercase letters, numbers, and hyphens only.
EOF
}

template_name="${1:-}"
project_slug="${2:-}"

if [[ -z "${template_name}" || -z "${project_slug}" ]]; then
  usage
  exit 1
fi

case "${template_name}" in
  local-script-tool|lesson-helper|checklist-generator|rubric-helper|mini-app-plan) ;;
  *)
    printf 'ERROR: unknown template: %s\n' "${template_name}" >&2
    usage
    exit 1
    ;;
esac

if [[ ! "${project_slug}" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  printf 'ERROR: unsafe project slug: %s\n' "${project_slug}" >&2
  printf 'Use lowercase letters, numbers, and hyphens only. No spaces, slashes, or path traversal.\n' >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  printf 'ERROR: could not resolve Git repo root.\n' >&2
  exit 1
fi

cd "${repo_root}"

template_dir="developer-mode/templates/${template_name}"
projects_dir="developer-mode/projects"
destination="${projects_dir}/${project_slug}"

if [[ ! -d "${template_dir}" ]]; then
  printf 'ERROR: template directory missing: %s\n' "${template_dir}" >&2
  exit 1
fi

if [[ -e "${destination}" ]]; then
  printf 'ERROR: destination already exists: %s\n' "${destination}" >&2
  exit 1
fi

mkdir -p "${projects_dir}"
mkdir "${destination}"
cp -R "${template_dir}/." "${destination}/"

cat <<EOF
Created Developer Mode project:
  ${destination}

Template:
  ${template_name}

Next steps:
  1. Review the copied README/template files.
  2. Keep the project local.
  3. Do not add secrets or student-sensitive data.
  4. Run any included tests manually when ready.

No generated code was run.
Project queue was not updated.
EOF
