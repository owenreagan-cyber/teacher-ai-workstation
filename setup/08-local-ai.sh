#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:${PATH}"

ask_yes_no() {
  local prompt="$1"
  local answer=""
  if [[ -t 0 ]]; then
    read -r -p "${prompt} [y/N] " answer
    [[ "${answer}" =~ ^[Yy]$ ]]
  else
    return 1
  fi
}

pull_model() {
  local model="$1"
  if ollama pull "${model}"; then
    echo "PASS: Pulled ${model}."
  else
    echo "WARN: Could not pull ${model}. You can retry later with: ollama pull ${model}"
  fi
}

echo "Checking local AI setup with Ollama..."

if ! command -v ollama >/dev/null 2>&1; then
  echo "WARN: Ollama CLI is not installed yet. Local AI setup skipped."
  exit 0
fi

echo "PASS: Ollama CLI is installed."

if ! curl -fsS http://localhost:11434 >/dev/null 2>&1; then
  echo "Ollama is not reachable yet. Trying to start it..."
  if command -v brew >/dev/null 2>&1; then
    brew services start ollama >/dev/null 2>&1 || true
  fi
  open -a Ollama >/dev/null 2>&1 || true
  sleep 3
fi

if curl -fsS http://localhost:11434 >/dev/null 2>&1; then
  echo "PASS: Ollama service is reachable at http://localhost:11434."
else
  echo "WARN: Ollama service is not reachable yet. Open Ollama manually and rerun this script later."
fi

echo "Starter model suggestions: a current small Gemma model and a current small Qwen model."
if ask_yes_no "Do you want to pull lightweight starter models now?"; then
  pull_model "gemma3:1b"
  pull_model "qwen2.5:0.5b"
else
  echo "WARN: Starter model pulls skipped. You can install models later with Ollama."
fi

echo "Large models can use significant disk space and memory. Always review size before pulling them."
