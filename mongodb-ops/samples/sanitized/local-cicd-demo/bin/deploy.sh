#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <dev|sat|prod> <plan|apply|rollback> [database|ops-manager|all] [--confirm PROD]" >&2
  exit 2
fi

environment="$1"
operation="$2"
scope="${3:-all}"
shift "$(( $# >= 3 ? 3 : 2 ))"

case "${environment}" in dev|sat|prod) ;; *) echo "Invalid environment: ${environment}" >&2; exit 2 ;; esac
case "${operation}" in plan|apply|rollback) ;; *) echo "Invalid operation: ${operation}" >&2; exit 2 ;; esac
case "${scope}" in database|ops-manager|all) ;; *) echo "Invalid scope: ${scope}" >&2; exit 2 ;; esac

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"
if [[ -x "${project_root}/.venv/bin/python" ]]; then
  python_command="${project_root}/.venv/bin/python"
else
  python_command="python3"
  export PYTHONPATH="${project_root}/src${PYTHONPATH:+:${PYTHONPATH}}"
fi

execution_args=(--environment "${environment}")
if [[ "${operation}" != "plan" ]]; then
  execution_args+=(--apply)
fi
execution_args+=("$@")

database_apply=(
  scripts/database/001_create_customers_collection.py
  scripts/database/002_create_customers_email_index.py
)
database_rollback=(
  scripts/database/002_rollback_customers_email_index.py
  scripts/database/001_rollback_customers_collection.py
)
ops_apply=(
  scripts/ops_manager/003_create_customer_reader_role.py
  scripts/ops_manager/004_create_demo_application_user.py
  scripts/ops_manager/005_create_host_down_alert.py
)
ops_rollback=(
  scripts/ops_manager/005_rollback_host_down_alert.py
  scripts/ops_manager/004_rollback_demo_application_user.py
  scripts/ops_manager/003_rollback_customer_reader_role.py
)

run_scripts() {
  local script
  for script in "$@"; do
    echo "==> ${script}"
    "${python_command}" "${script}" "${execution_args[@]}"
  done
}

if [[ "${operation}" == "rollback" ]]; then
  if [[ "${scope}" == "ops-manager" || "${scope}" == "all" ]]; then
    run_scripts "${ops_rollback[@]}"
  fi
  if [[ "${scope}" == "database" || "${scope}" == "all" ]]; then
    run_scripts "${database_rollback[@]}"
  fi
else
  if [[ "${scope}" == "database" || "${scope}" == "all" ]]; then
    run_scripts "${database_apply[@]}"
  fi
  if [[ "${scope}" == "ops-manager" || "${scope}" == "all" ]]; then
    run_scripts "${ops_apply[@]}"
  fi
fi
