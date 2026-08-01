#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${project_root}/.local/state"

copy_if_missing() {
  local source_file="$1"
  local destination_file="$2"
  if [[ ! -f "${destination_file}" ]]; then
    cp "${source_file}" "${destination_file}"
    chmod 600 "${destination_file}"
    echo "Created ${destination_file}"
  else
    echo "Kept existing ${destination_file}"
  fi
}

copy_if_missing \
  "${project_root}/config/local/docker.env.example" \
  "${project_root}/.local/docker.env"
copy_if_missing \
  "${project_root}/config/local/parameter-store.example.json" \
  "${project_root}/.local/parameter-store.json"
copy_if_missing \
  "${project_root}/config/local/secrets-manager.example.json" \
  "${project_root}/.local/secrets-manager.json"

echo "Local configuration initialized under ${project_root}/.local"

