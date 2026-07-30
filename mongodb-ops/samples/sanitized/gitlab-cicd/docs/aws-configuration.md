# AWS Configuration

Use an EC2 instance profile for the deployment Runner. Do not configure static
AWS access keys in GitLab variables or on disk.

## Parameter Store

Create these parameters for each environment:

| Sample path | Value |
|---|---|
| `/mongodb-cicd/dev/mongodb/connection-uri` | MongoDB URI without username/password |
| `/mongodb-cicd/dev/ops-manager/base-url` | Ops Manager HTTPS base URL |
| `/mongodb-cicd/dev/ops-manager/project-id` | Ops Manager project/group ID |

Repeat with `sat` and `prod`. A connection URI can contain hosts, replica-set
name, TLS options, and connection options, but credentials belong in Secrets
Manager.

Example nonsecret MongoDB URI shape:

```text
mongodb://db1.example.invalid:27017,db2.example.invalid:27017/?replicaSet=sample-rs&tls=true
```

## Secrets Manager

Create the following JSON secrets for each environment. Enter the values
through the approved AWS console/automation path; do not put passwords directly
on a shell command line.

Deployment MongoDB user:

```json
{
  "username": "gitlab_deployer",
  "password": "REPLACE_OUTSIDE_GIT",
  "authenticationDatabase": "admin"
}
```

Ops Manager programmatic API key:

```json
{
  "publicKey": "REPLACE_OUTSIDE_GIT",
  "privateKey": "REPLACE_OUTSIDE_GIT"
}
```

Assign this key `Project Automation Admin` only in the intended Ops Manager
project. If Ops Manager programmatic API access lists are enabled, permit the
Runner's approved source address/range.

New MongoDB collection-reader identity:

```json
{
  "username": "orders_reader",
  "password": "REPLACE_OUTSIDE_GIT"
}
```

The sample secret IDs are:

```text
mongodb-cicd/<environment>/mongodb/deployment-user
mongodb-cicd/<environment>/ops-manager/api-key
mongodb-cicd/<environment>/mongodb/orders-reader
```

Use environment-specific credentials. Do not reuse a DEV secret in SAT or PROD.

## Instance Profile

Replace `REGION`, `ACCOUNT_ID`, and `KMS_KEY_ID` in
`infrastructure/iam/runner-policy.json`. Attach the resulting policy to the EC2
Runner instance profile.

The policy permits:

- `ssm:GetParameter` below `/mongodb-cicd/`
- `secretsmanager:GetSecretValue` below `mongodb-cicd/`
- `kms:Decrypt` only for the selected customer-managed KMS key and only through
  Systems Manager or Secrets Manager

Narrow the ARNs further when DEV, SAT, and PROD use separate Runner roles.

## Network and TLS

Prefer VPC endpoints for Systems Manager, Secrets Manager, KMS, and STS when
required by the environment. Install organization CA certificates in the OS
trust store.

If Ops Manager uses a private CA that is not in the OS trust store, set this
protected GitLab variable to a root-readable/Runner-readable CA bundle already
installed on the host:

```text
OPS_MANAGER_CA_FILE=/etc/pki/ca-trust/source/anchors/organization-chain.pem
```

The sample never disables TLS verification.

## Validation

From an approved troubleshooting session as the Runner user:

```bash
aws sts get-caller-identity
aws ssm get-parameter \
  --name /mongodb-cicd/dev/ops-manager/project-id \
  --with-decryption \
  --query Parameter.Value \
  --output text
```

Do not print Secrets Manager values during validation. Confirm access by
examining the command's exit code or CloudTrail instead.
