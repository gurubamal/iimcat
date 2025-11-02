#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./script.sh <model>
  ./script.sh <path/to/file.csv>

Examples:
  ./script.sh codex    # opens latest realtime_ai_results_*codex-shell.csv (excluding rejects)
  ./script.sh claude   # opens latest realtime_ai_results_*claude-shell.csv (excluding rejects)
  ./script.sh some.csv # opens the given CSV file

Notes:
  - Uses: csvlook <file> | less -S
  - Excludes any files containing "reject" in the filename.
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if ! command -v csvlook >/dev/null 2>&1; then
  echo "Error: csvlook not found. Install csvkit (e.g., 'pipx install csvkit' or 'pip install csvkit')." >&2
  exit 1
fi

arg="$1"
file=""

if [[ -f "$arg" ]]; then
  file="$arg"
else
  # Treat argument as a model key, e.g., 'codex' or 'claude'
  model="$arg"
  shopt -s nullglob nocaseglob
  matches=(realtime_ai_results_*"${model}"-shell.csv)
  # Filter out any files containing 'reject' (case-insensitive)
  filtered=()
  for f in "${matches[@]}"; do
    fname_lower=${f,,}
    if [[ "$fname_lower" == *reject* ]]; then
      continue
    fi
    filtered+=("$f")
  done
  if (( ${#filtered[@]} == 0 )); then
    echo "No matching CSV found for model '$model' (pattern: realtime_ai_results_*${model}-shell.csv, excluding rejects)." >&2
    exit 1
  fi
  # Pick most recent by modification time
  # shellcheck disable=SC2012
  file=$(ls -t -- "${filtered[@]}" 2>/dev/null | head -n1)
fi

if [[ -z "${file}" || ! -f "${file}" ]]; then
  echo "File not found: ${file:-<empty>}" >&2
  exit 1
fi

echo "Viewing: $file" >&2
exec bash -c 'csvlook "$1" | less -S' _ "$file"

