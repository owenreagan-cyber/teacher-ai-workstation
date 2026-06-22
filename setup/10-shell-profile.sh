#!/usr/bin/env bash
set -euo pipefail

ZSHRC="${HOME}/.zshrc"
START_MARKER="# >>> teacher-ai-workstation >>>"
END_MARKER="# <<< teacher-ai-workstation <<<"

echo "Configuring safe zsh terminal enhancements..."

mkdir -p "$(dirname "${ZSHRC}")"
touch "${ZSHRC}"

managed_block="$(cat <<'EOF'
# >>> teacher-ai-workstation >>>
# Managed by the Teacher AI Workstation Phase 0 setup.
# Safe to rerun: setup/10-shell-profile.sh replaces only this block.

if [[ ":$PATH:" != *":/opt/homebrew/bin:"* ]]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

if command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
fi

if command -v zoxide >/dev/null 2>&1; then
  eval "$(zoxide init zsh)"
fi

if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh)"
fi

if command -v eza >/dev/null 2>&1; then
  alias ls='eza --icons --group-directories-first'
  alias ll='eza -la --icons --group-directories-first'
fi

if command -v bat >/dev/null 2>&1; then
  alias cat='bat'
fi

alias aistatus='ps aux | grep -E "ollama|LM Studio" | grep -v grep || true'
alias aiflush='osascript -e "quit app \"LM Studio\"" 2>/dev/null || true; brew services stop ollama 2>/dev/null || true; pkill ollama 2>/dev/null || true'

# <<< teacher-ai-workstation <<<
EOF
)"

if grep -qF "${START_MARKER}" "${ZSHRC}" && grep -qF "${END_MARKER}" "${ZSHRC}"; then
  tmp_file="$(mktemp)"
  in_block=0
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" == "${START_MARKER}" ]]; then
      printf '%s\n' "${managed_block}" >> "${tmp_file}"
      in_block=1
      continue
    fi

    if [[ "${line}" == "${END_MARKER}" ]]; then
      in_block=0
      continue
    fi

    if (( in_block == 0 )); then
      printf '%s\n' "${line}" >> "${tmp_file}"
    fi
  done < "${ZSHRC}"
  mv "${tmp_file}" "${ZSHRC}"
else
  {
    printf '\n'
    printf '%s\n' "${managed_block}"
  } >> "${ZSHRC}"
fi

echo "PASS: Teacher AI Workstation managed zsh block is present in ~/.zshrc."
echo "Open a new Terminal window or run:"
echo "source ~/.zshrc"
