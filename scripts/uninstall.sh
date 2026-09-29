#!/usr/bin/env bash
# DD Flash - Uninstaller (wrapper)
# Delegates to install.sh --uninstall

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec bash "${SCRIPT_DIR}/install.sh" --uninstall
