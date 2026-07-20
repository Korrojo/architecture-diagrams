# Controlled Manual Emergency Changes and Reconciliation

## Purpose

Define how an urgent MongoDB production change may be performed manually when the standard CI/CD process cannot meet the required response time.

The procedure allows only the minimum action needed to stabilize or restore service. The emergency change is not complete until MongoDB, GitLab, the change ticket, and operational documentation agree.

## When It May Be Used

Use this process only when:

- Production availability, data integrity, security, or severe performance is at immediate risk.
- Waiting for the normal CI/CD workflow would materially increase impact.
- An authorized approver accepts the emergency action.
- A tested or clearly defined rollback action exists whenever technically possible.

Routine work, convenience changes, and undocumented troubleshooting do not qualify.

## Emergency Procedure

1. Open an emergency Jira or ServiceNow change record.
2. Record the incident, reason, target, expected result, risk, approver, validation, and rollback commands.
3. Capture the relevant database state before the change.
4. Obtain the required emergency approval.
5. Execute only the approved minimum change using an individually attributable administrative identity.
6. Capture the command, timestamp, target, result, and executing identity.
7. Validate database health and confirm that the original problem is resolved.
8. Roll back or escalate immediately if validation fails.
9. Add the final database definition or script to GitLab.
10. Submit a merge request referencing the emergency ticket.
11. Run the standard pipeline validations without redeploying an already-applied non-idempotent operation.
12. Compare the repository's expected state with the actual MongoDB state.
13. Attach evidence, update the runbook or documentation, and close the change only after no unexplained drift remains.

## Reconciliation

Reconciliation restores agreement between:

```text
GitLab declared state = Actual MongoDB state
```

It requires:

- Adding the manual change to the appropriate GitLab-managed definition or deployment script.
- Recording who changed what, when, why, where, and under whose approval.
- Running inventory or drift-detection scripts.
- Comparing object names, definitions, options, privileges, and configuration values.
- Correcting unintended differences.
- Recording validation output and final state in the change ticket.
- Updating operational documentation when the emergency exposed a missing procedure.
- Reviewing why the standard pipeline could not be used and improving it where appropriate.

## Example: Emergency Index Creation

### Manual emergency execution

```javascript
db.orders.createIndex(
  { customerId: 1, orderDate: -1 },
  { name: "idx_customer_order_date" }
)
```

### GitLab-managed definition

```javascript
db.orders.createIndex(
  { customerId: 1, orderDate: -1 },
  { name: "idx_customer_order_date" }
)
```

### Reconciliation validation

Confirm that the actual index matches the repository definition:

- Database and collection
- Index name
- Key fields and order
- Unique, partial, sparse, collation, and expiration options
- Build result
- Query-plan usage
- Absence of unintended indexes

## Completion Criteria

The emergency change may be closed only when:

- Service stability is confirmed.
- Post-change validation passes.
- The change and rollback definitions are committed to GitLab.
- The merge request and change ticket reference each other.
- Drift detection reports no unexplained difference.
- Execution and approval evidence is retained.
- Documentation and follow-up actions are assigned.

## Control Principle

Manual execution is the emergency action. Reconciliation is the controlled process that prevents the manual action from becoming undocumented configuration drift.
