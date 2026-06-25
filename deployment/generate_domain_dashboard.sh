#!/usr/bin/env bash
set -euo pipefail

PROFILE_NAME="${1:-kaoyan}"
WEB_ROOT="${2:-/var/www/study-planner/${PROFILE_NAME}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

mkdir -p "${WEB_ROOT}"

python "${REPO_ROOT}/scripts/study_dashboard.py" \
  --profile "${PROFILE_NAME}" \
  --out-dir "${WEB_ROOT}"

echo "Dashboard generated for profile '${PROFILE_NAME}':"
echo "  ${WEB_ROOT}/index.html"
