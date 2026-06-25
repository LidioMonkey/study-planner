#!/usr/bin/env bash
set -euo pipefail

PROFILE_NAME="${1:-kaoyan}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/deployment/profiles/${PROFILE_NAME}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
TARGET_DIR="${CODEX_HOME_DIR}/study-planner/profiles/${PROFILE_NAME}"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Missing bundled profile: ${SOURCE_DIR}" >&2
  exit 1
fi

mkdir -p "$(dirname "${TARGET_DIR}")"
rm -rf "${TARGET_DIR}"
cp -R "${SOURCE_DIR}" "${TARGET_DIR}"

echo "Restored profile '${PROFILE_NAME}' to:"
echo "  ${TARGET_DIR}"
echo
echo "Next steps:"
echo "1. Inspect ${TARGET_DIR}/obsidian.json and replace any invalid local path."
echo "2. Run: python ${REPO_ROOT}/scripts/study_dashboard.py --profile ${PROFILE_NAME}"
echo "3. Run: python ${REPO_ROOT}/scripts/study_dashboard_server.py --profile ${PROFILE_NAME}"
