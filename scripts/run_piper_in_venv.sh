#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-piper"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  "${ROOT_DIR}/scripts/setup_piper_venv.sh"
fi

source "${VENV_DIR}/bin/activate"
python "${ROOT_DIR}/scripts/generate_piper_audio.py" "$@"