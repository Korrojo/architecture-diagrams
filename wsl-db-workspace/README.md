# WSL Database Engineering Workspace

This directory contains an idempotent setup script for a WSL-based database engineering workspace.

It creates two independent project directories under `~/work/repos`:

- `oracle-to-mongodb-glue` — AWS Glue Python/PySpark migration code, Oracle migration SQL, MongoDB target design, validation, and reconciliation.
- `mongodb-enterprise-ops` — day-to-day administration for MongoDB Enterprise on AWS EC2, managed through Ops Manager.

It also creates local working directories outside the repositories:

- `~/work/scratch`
- `~/work/data`
- `~/work/logs`

## Copy and run in WSL

1. Open [`create-workspace.sh`](create-workspace.sh) on GitHub.
2. Copy its complete contents.
3. In WSL, create a file and paste the copied contents:

```bash
nano create-workspace.sh
```

4. Save the file, then run:

```bash
chmod +x create-workspace.sh
./create-workspace.sh
```

The script does not initialize Git repositories, configure remotes, install packages, or create credentials. Existing `README.md` and `.gitignore` files are preserved.

## Credentials

Do not put credentials under `~/work/repos`. Use AWS IAM roles or SSO where available, AWS Secrets Manager for Glue runtime secrets, and protected files under `~/.config/db-work` only when local credentials are required.
