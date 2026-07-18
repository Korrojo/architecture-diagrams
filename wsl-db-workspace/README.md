# WSL Database Engineering Workspace

This directory contains an idempotent setup script for a WSL-based database engineering workspace.

It creates two independent project directories under `~/work/repos`:

- `oracle-to-mongodb-glue` — AWS Glue Python/PySpark migration code, Oracle migration SQL, MongoDB target design, validation, and reconciliation.
- `mongodb-enterprise-ops` — day-to-day administration for MongoDB Enterprise on AWS EC2, managed through Ops Manager.

It also creates local working directories outside the repositories:

- `~/work/scratch`
- `~/work/data`
- `~/work/logs`

## Download and run in WSL

```bash
curl -fsSLO https://raw.githubusercontent.com/Korrojo/architecture-diagrams/main/wsl-db-workspace/create-workspace.sh
chmod +x create-workspace.sh
./create-workspace.sh
```

The script does not initialize Git repositories, configure remotes, install packages, or create credentials. Existing `README.md` and `.gitignore` files are preserved.

## Credentials

Do not put credentials under `~/work/repos`. Use AWS IAM roles or SSO where available, AWS Secrets Manager for Glue runtime secrets, and protected files under `~/.config/db-work` only when local credentials are required.
