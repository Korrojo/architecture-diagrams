# WSL Database Engineering Workspace

This directory contains sanitized WSL setup resources for database engineering work.

## Workspace

The setup script creates two independent project directories under `~/work/repos`:

- `oracle-to-mongodb-glue` — AWS Glue Python/PySpark migration code, Oracle migration SQL, MongoDB target design, validation, and reconciliation.
- `mongodb-enterprise-ops` — day-to-day administration for MongoDB Enterprise on AWS EC2, managed through Ops Manager.

It also creates local working directories outside the repositories:

- `~/work/scratch`
- `~/work/data`
- `~/work/logs`

## Files

- [`create-workspace.sh`](create-workspace.sh) — creates the WSL workspace and project structures.
- [`APT_AND_PIP.md`](APT_AND_PIP.md) — generic APT, virtual-environment, pip, proxy, and certificate guidance.
- [`export_users_roles.py`](export_users_roles.py) — exports MongoDB users, assigned roles, and inherited privileges to CSV.

## Copy and run the workspace setup

1. Open [`create-workspace.sh`](create-workspace.sh) on GitHub.
2. Copy its complete contents.
3. In WSL, create a file and paste the copied contents:

```bash
nano ~/create-workspace.sh
```

4. Save the file, then run:

```bash
chmod +x ~/create-workspace.sh
~/create-workspace.sh
```

The script does not initialize Git repositories, configure remotes, install packages, or create credentials. Existing `README.md` and `.gitignore` files are preserved.

## MongoDB inventory script

Copy `export_users_roles.py` to your MongoDB operations repository. For example:

```text
~/work/repos/mongodb-ops/scripts/users_and_roles/export_users_roles.py
```

Create the cluster environment file outside Git:

```text
~/.config/work/mongodb/DEV/example-cluster.env
```

Example content:

```bash
MONGODB_URI='mongodb://username:password@host1,host2,host3/?authSource=admin&replicaSet=exampleReplicaSet'
```

Secure the file:

```bash
chmod 600 ~/.config/work/mongodb/DEV/example-cluster.env
```

Run from the MongoDB operations repository:

```bash
source .venv/bin/activate
python scripts/users_and_roles/export_users_roles.py \
  --environment DEV \
  --cluster example-cluster
```

The CSV is written outside Git under:

```text
~/work/data/mongodb/DEV/example-cluster/
```

## Credentials

Do not put credentials under `~/work/repos`. Use approved identity services or secrets management where available. When local files are required, keep them under `~/.config/work`, restrict them to mode `600`, and never commit them.
