# MongoDB GitLab CI/CD Sample

This sanitized project demonstrates an end-to-end GitLab workflow for:

1. Creating an index directly in MongoDB with PyMongo.
2. Creating a collection-scoped read role and MongoDB database user through the Ops Manager Automation Configuration API.
3. Routing the same deployment code to `dev`, `sat`, or `prod` through `DEPLOY_ENV`.
4. Retrieving MongoDB connection strings and Ops Manager configuration from AWS Systems Manager Parameter Store.
5. Retrieving MongoDB credentials and Ops Manager programmatic API keys from AWS Secrets Manager.

No Java or Maven is required.

## Repository Layout

```text
mongodb-gitlab-cicd-sample/
├── .gitlab-ci.yml
├── .editorconfig
├── .gitignore
├── .gitlab/
│   └── CODEOWNERS
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── bin/
│   └── deploy.sh
├── config/
│   └── environments/
│       ├── dev.yml
│       ├── sat.yml
│       └── prod.yml
├── docs/
│   ├── aws-configuration.md
│   ├── gitlab-settings.md
│   └── workflow.md
├── infrastructure/
│   └── iam/
│       └── runner-policy.json
├── runner/
│   ├── INSTALL.md
│   ├── config.toml.example
│   └── gitlab-runner.service-override.conf.example
├── scripts/
│   ├── database/
│   │   └── create_index.py
│   └── ops_manager/
│       └── create_collection_reader.py
├── src/
│   └── mongodb_cicd/
│       ├── __init__.py
│       ├── aws_config.py
│       ├── config.py
│       ├── database_change.py
│       └── ops_manager_change.py
└── tests/
    ├── test_config.py
    ├── test_database_change.py
    └── test_ops_manager_change.py
```

## Environment Routing

The pipeline sets one value:

```text
DEPLOY_ENV=dev
DEPLOY_ENV=sat
DEPLOY_ENV=prod
```

The application accepts only those three values and loads:

```text
config/environments/<DEPLOY_ENV>.yml
```

Environment files contain resource names and nonsecret deployment intent. They never contain host credentials or passwords.

## Local Validation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e .

ruff check .
pytest

python scripts/database/create_index.py --environment dev
python scripts/ops_manager/create_collection_reader.py --environment dev
```

The two commands above are dry-runs. They display the intended change without contacting AWS, MongoDB, or Ops Manager.

## Apply Locally

The EC2 identity must have the IAM permissions documented in `docs/aws-configuration.md`.

```bash
export AWS_REGION=us-east-1

python scripts/database/create_index.py \
  --environment dev \
  --apply

python scripts/ops_manager/create_collection_reader.py \
  --environment dev \
  --apply
```

Do not use `--apply` from an unprotected branch.

## Important Ops Manager Distinction

An Ops Manager application user and a MongoDB database user are different identities.

- Ops Manager application roles grant access to the Ops Manager interface and API.
- MongoDB roles grant access to databases and collections.

This sample creates a MongoDB database user managed by Ops Manager Automation. To provide collection-only read access, it adds a custom MongoDB role whose resource is one collection, then assigns that role to the managed MongoDB user.

Ops Manager replaces the entire project automation configuration with a `PUT`. The sample:

- Defaults to dry-run.
- Requires the API key to have `Project Automation Admin`.
- Fails if authentication is not already enabled and authoritative.
- Refuses to overwrite an existing role or user with conflicting settings.
- Checks the automation configuration version immediately before applying.
- Serializes GitLab deployment jobs with `resource_group`.

Review this operation with the Ops Manager administration team before production use.

## Deployment Behavior

- Merge request: lint and unit tests only.
- Merge to the protected default branch: automatic DEV deployment.
- SAT: manual deployment from the protected default branch.
- PROD: manual deployment from the protected default branch and protected environment approval.
- The same Git commit is promoted through all environments.
- No environment-specific Git branches are required.

## Start Here

1. Review `docs/workflow.md`.
2. Replace the sample environment resource names in `config/environments/`.
3. Have the AWS team provision the parameters, secrets, KMS permissions, and
   EC2 instance profile described in `docs/aws-configuration.md`.
4. Have the Linux/GitLab team follow `runner/INSTALL.md`.
5. Apply the GitLab protections in `docs/gitlab-settings.md`.
6. Replace the example groups in `.gitlab/CODEOWNERS`.
7. Open a merge request and confirm `validate` passes.
8. Merge to deploy DEV, then manually promote the same commit to SAT and PROD.

This is a teaching sample. Review permissions, package versions, Ops Manager
version compatibility, backup/change-window requirements, and organizational
security controls before production use.
