#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
required_files=(
  "src/mongodb_local_cicd/database_changes.py"
  "src/mongodb_local_cicd/migrations.py"
  "src/mongodb_local_cicd/ops_manager.py"
)

missing=()
for relative_path in "${required_files[@]}"; do
  if [[ ! -s "${project_root}/${relative_path}" ]]; then
    missing+=("${relative_path}")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "Copy these required source files into the generated project:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

echo "All separately copied source files are present."
