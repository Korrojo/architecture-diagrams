#!/usr/bin/env bash
set -euo pipefail
set +x

case "${DEPLOY_ENV:-}" in
  dev|sat|prod) ;;
  *)
    echo "DEPLOY_ENV must be dev, sat, or prod" >&2
    exit 2
    ;;
esac

: "${AWS_REGION:?AWS_REGION must be set}"

python scripts/database/create_index.py --environment "${DEPLOY_ENV}" --apply
python scripts/ops_manager/create_collection_reader.py --environment "${DEPLOY_ENV}" --apply
