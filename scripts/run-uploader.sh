#!/usr/bin/env bash
# Launch the PP1 telemetry uploader with the correct environment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load AWS credentials if an env file is present.
if [[ -f "${PROJECT_ROOT}/env" ]]; then
  # shellcheck disable=SC1090
  source "${PROJECT_ROOT}/env"
fi

cd "${PROJECT_ROOT}"
exec /usr/bin/env python3 "${PROJECT_ROOT}/uploader.py"
