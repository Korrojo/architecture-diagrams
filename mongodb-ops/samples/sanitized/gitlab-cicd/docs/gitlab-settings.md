# GitLab Project and Runner Settings

## Runner Separation

Use two trust levels:

| Runner tag | Purpose | AWS/MongoDB access |
|---|---|---|
| `general-linux` | Lint, tests, and dry-runs for merge requests | None |
| `mongodb-deploy` | Protected default-branch deployments | EC2 instance profile and target network |

This separation matters with the shell executor: every job scheduled on the
deployment Runner can use its EC2 instance profile. Do not run untrusted merge
request code there.

Configure `mongodb-deploy` as:

- Project-scoped and locked to this project
- Protected
- `Run untagged jobs` disabled
- Tag `mongodb-deploy`
- One concurrent job

## Protected Source

- Protect the default branch.
- Require merge requests and reviews.
- Require a successful `validate` job before merge.
- Restrict who may merge.
- Use CODEOWNERS for `.gitlab-ci.yml`, `config/`, `scripts/`,
  `infrastructure/`, and `runner/`.

## Environments

Create GitLab environments named exactly:

```text
dev
sat
prod
```

Protect `prod` and configure allowed deployers/approval rules. If policy
requires it, protect `sat` as well. DEV is automatic after a protected
default-branch merge; SAT and PROD remain manual jobs.

## CI/CD Variables

Set these nonsecret variables at group/project scope:

| Variable | Example | Protection |
|---|---|---|
| `AWS_REGION` | `us-east-1` | Protected |
| `OPS_MANAGER_CA_FILE` | Approved CA bundle path | Protected |

Credentials are intentionally absent. The EC2 instance profile obtains
short-lived AWS credentials; the scripts then retrieve target credentials from
AWS Secrets Manager.

Do not enable CI debug tracing for deployments. Do not echo environment
variables, connection strings, API responses, or Automation configuration.

## Package Repository

The jobs install Python dependencies. Configure the Runner user's `pip.conf` to
use the approved internal Python repository, or supply an appropriately masked
and protected package-registry configuration. Do not commit registry
credentials.

For a fully isolated Runner, pre-download approved wheels into an internal
artifact repository and install with hashes.

## Job Serialization

The `.gitlab-ci.yml` uses:

```yaml
resource_group: "mongodb-${DEPLOY_ENV}"
```

This prevents two jobs from this project from changing the same environment at
the same time. It does not coordinate separate projects or administrators
writing directly to Ops Manager, so an operational change window is still
required for production.
