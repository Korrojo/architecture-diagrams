# Architecture Diagrams

Sanitized reference architecture diagrams intended for documentation, discussion, and editing.

## MongoDB

### Ops Manager–managed three-node replica set

This example shows:

- A DBA/operations role administering MongoDB Ops Manager
- Ops Manager managing and monitoring a three-node replica set
- One primary replicating to two secondary members

Files:

- [Editable SVG](ops-manager-3-node-replica-set.svg)

## Editing in Microsoft PowerPoint

1. Download the SVG using **Raw** or **Download raw file**.
2. In PowerPoint, select **Insert > Pictures > This Device**.
3. Insert the SVG.
4. Right-click the graphic and select **Convert to Shape**.
5. Ungroup or select individual shapes to edit labels, colors, and layout.

## WSL Database Engineering Workspace

Sanitized setup for separate Oracle-to-MongoDB Glue migration and MongoDB Enterprise operations repositories:

- [Setup instructions](wsl-db-workspace/README.md)
- [Workspace creation script](wsl-db-workspace/create-workspace.sh)
- [APT and pip network guide](wsl-db-workspace/APT_AND_PIP.md)
- [MongoDB user and role inventory script](wsl-db-workspace/export_users_roles.py)
- [MongoDB operations workspace guide](mongodb-ops/README.md)
- [MongoDB scripts folder guide](mongodb-ops/scripts/README.md)

## MongoDB Operations

- [MongoDB Enterprise operational improvement plan](mongodb-operations/operational-improvement-plan.md)
- [Controlled manual emergency changes and reconciliation](mongodb-operations/emergency-change-reconciliation.md)
- [MongoDB collection inventory and cleanup-candidate reporting](mongodb-collection-inventory/README.md)

## MongoDB Cluster Sizing

- [Application-team questionnaire and sizing package](mongodb-cluster-sizing/README.md)

## Sanitization

All diagrams and scripts in this repository must use generic labels. Do not include:

- Organization, customer, project, or application names
- Usernames or email addresses
- Hostnames, IP addresses, DNS names, or environment-specific ports
- Cloud account IDs, resource IDs, ARNs, subscription IDs, or tenant IDs
- Database or collection names from real systems
- Credentials, secrets, tokens, or internal URLs

## Disclaimer

These diagrams and scripts are generic examples and are not production deployment specifications.
