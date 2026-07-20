# MongoDB Enterprise Operational Improvement Plan

## Scope

Self-managed MongoDB Enterprise deployments on AWS EC2, administered through MongoDB Ops Manager.

## Objective

Establish secure, reliable, traceable, and repeatable MongoDB operations by:

- Standardizing administrative processes.
- Automating routine work and approved database changes.
- Improving availability, recovery, performance, and alert quality.
- Maintaining current inventories, runbooks, and audit evidence.
- Reducing undocumented manual changes and configuration drift.

## Workstreams

| Workstream | Key activities | Deliverables |
|---|---|---|
| **1. Governance and CI/CD** | GitLab structure, branching, merge-request approval, Jira integration, Jenkins pipeline, validation, rollback, emergency-change control, and evidence retention | Repository standard, change templates, deployment pipeline, rollback procedure |
| **2. Asset and Configuration Management** | Inventory clusters, hosts, databases, collections, indexes, versions, agents, and configurations; enforce naming, lifecycle, cleanup, provisioning, decommissioning, and drift controls | Authoritative inventory, naming standard, lifecycle policy, provisioning runbook |
| **3. Security and Access** | Inventory users and roles; enforce least privilege; manage OIDC, service accounts, TLS certificates, credential rotation, auditing, and access recertification | RBAC inventory, access standard, certificate procedure, audit-review process |
| **4. Availability, Backup, and Recovery** | Review replica-set design, member placement, replication lag, elections, and oplog capacity; define backup, restore, failover, RPO, and RTO requirements | HA standard, backup policy, tested restore and failover runbooks |
| **5. Performance and Capacity** | Establish baselines; analyze slow queries, collection scans, query plans, indexes, WiredTiger cache, CPU, memory, connections, disk, EC2/EBS, OS settings, and growth | Performance baseline, index-review process, tuning reports, capacity forecast |
| **6. Monitoring and Alerts** | Inventory alerts; define required conditions, severity, thresholds, ownership, notification, escalation, maintenance windows, testing, triage, and noise reduction | Alert catalog, severity matrix, routing policy, tested alert runbooks |
| **7. Platform Lifecycle and Operations** | Manage MongoDB, Ops Manager, agent, OS, and dependency patching; control Feature Compatibility Version; perform compatibility reviews and routine health checks | Upgrade runbook, maintenance calendar, health-check checklist, support procedures |

## Change-Management Model

### Standard changes

```text
Jira/ServiceNow → GitLab merge request → review and approval →
Jenkins validation → controlled deployment → post-validation →
inventory comparison → audit evidence → documentation
```

Repeatable changes should use CI/CD. Cluster configuration should remain aligned with the approved Ops Manager automation configuration.

### Emergency changes

An authorized DBA may perform the minimum manual action required to restore service when the normal workflow cannot meet the response time. The change must then be reconciled with GitLab, the change record, inventory, and documentation.

See [Controlled Manual Emergency Changes and Reconciliation](emergency-change-reconciliation.md).

## Delivery Phases

### Phase 1 — Assess

- Build infrastructure, cluster, database, index, access, backup, and alert inventories.
- Identify ownership, risks, unsupported versions, missing controls, and undocumented procedures.
- Establish performance, capacity, availability, and alert baselines.

### Phase 2 — Design

- Approve naming, lifecycle, access, backup, alert, and change-management standards.
- Design the GitLab–Jira–Jenkins workflow.
- Define RPO, RTO, severity, escalation, maintenance, and review requirements.

### Phase 3 — Implement

- Automate inventory and health checks.
- Implement pipeline validation, approval, deployment, rollback, and evidence collection.
- Configure prioritized alerts and create operational runbooks.
- Remediate high-risk availability, security, recovery, and performance gaps.

### Phase 4 — Validate and Operate

- Test deployments, rollbacks, notifications, restores, and replica-set failovers.
- Establish recurring access, performance, capacity, backup, and alert reviews.
- Publish approved procedures and assign owners.

## Success Measures

- MongoDB assets, access, indexes, alerts, versions, and backups are inventoried and owned.
- Standard changes are traceable from request through deployment and evidence.
- Manual emergency changes are reconciled without unexplained drift.
- Critical alerts have an owner, severity, escalation path, and tested runbook.
- Restore and failover tests meet approved RPO and RTO targets.
- Performance and capacity risks are reviewed and tracked regularly.
- MongoDB, Ops Manager, agents, certificates, and operating systems follow defined lifecycle procedures.

## References

- [MongoDB Operations Checklist for Self-Managed Deployments](https://www.mongodb.com/docs/manual/administration/production-checklist-operations/)
- [Ops Manager Alert Configuration](https://www.mongodb.com/docs/ops-manager/current/tutorial/manage-alert-configurations/)
- [Ops Manager Backup and Restore](https://www.mongodb.com/docs/ops-manager/current/tutorial/nav/backup-use/)
