# MongoDB Sizing Assessment

## Document Control

| Field | Value |
|---|---|
| Assessment status | Draft / Reviewed / Approved |
| Application or workload identifier |  |
| Environment |  |
| Prepared by |  |
| Reviewed by |  |
| Assessment date |  |
| Target launch date |  |
| Questionnaire version |  |
| Calculator version |  |

## Executive Recommendation

| Decision area | Recommendation | Evidence or rationale |
|---|---|---|
| Deployment model |  |  |
| Starting topology |  |  |
| Compute per data-bearing node |  |  |
| Storage per data-bearing node |  |  |
| EBS performance |  |  |
| Availability-zone placement |  |  |
| Backup and recovery |  |  |
| Sharding position | Not required / Future consideration / Required |  |
| Validation status | Not tested / Partially tested / Validated |  |

## Application Requirements

| Requirement | Normal | Peak or target | Evidence quality | Notes |
|---|---:|---:|---|---|
| Logical data at launch |  |  |  |  |
| Logical data after 3 years |  |  |  |  |
| Document count at launch |  |  |  |  |
| Average document size |  |  |  |  |
| Reads per second |  |  |  |  |
| Writes per second |  |  |  |  |
| Concurrent operations |  |  |  |  |
| Required response time |  |  |  |  |
| RTO |  |  |  |  |
| RPO |  |  |  |  |

## Data and Index Projection

| Capacity component | Launch | 1 year | 3 years | 5 years | Method or evidence |
|---|---:|---:|---:|---:|---|
| Logical collection data |  |  |  |  |  |
| Stored collection data |  |  |  |  |  |
| Indexes |  |  |  |  |  |
| Oplog |  |  |  |  |  |
| Operational and maintenance reserve |  |  |  |  |  |
| Required disk per node |  |  |  |  |  |

## Workload Characterization

| Workload | Frequency | Peak duration | Collections | Index support | Risk or observation |
|---|---:|---|---|---|---|
| Online reads |  |  |  |  |  |
| Online writes |  |  |  |  |  |
| Aggregations and reporting |  |  |  |  |  |
| Batch processing |  |  |  |  |  |
| Initial load or migration |  |  |  |  |  |
| Change streams or CDC |  |  |  |  |  |

## Proposed Index Strategy

| Collection | Query shape or business action | Proposed index | Index type | Estimated size | Write impact | Validation result |
|---|---|---|---|---:|---|---|
|  |  |  |  |  |  |  |

## Compute and Memory Assessment

| Item | Estimate or observation | Evidence | Decision |
|---|---|---|---|
| Hot collection working set |  |  |  |
| Hot index working set |  |  |  |
| Operating-system and agent reserve |  |  |  |
| Proposed RAM per node |  |  |  |
| CPU-sensitive workload features |  |  |  |
| Proposed vCPU per node |  |  |  |

## AWS EC2 Candidate Evaluation

| EC2 candidate | vCPU | RAM GiB | Baseline/max network | Baseline/max EBS IOPS | Baseline/max EBS throughput | Sustained fit | Burst fit | Approved/available | Decision |
|---|---:|---:|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |

Record the AWS documentation retrieval date and verify region, architecture, operating-system, MongoDB Enterprise, Ops Manager, monitoring, security-agent, and backup-agent compatibility.

## AWS EBS Candidate Evaluation

| EBS candidate | Size GiB | Provisioned IOPS | Provisioned throughput MiB/s | Expected latency | Capacity fit | IOPS fit | Throughput fit | EC2 limit fit | Decision |
|---|---:|---:|---:|---|---|---|---|---|---|
| gp3 |  |  |  |  |  |  |  |  |  |
| io2 Block Express |  |  |  |  |  |  |  |  |  |

Effective performance is the lower of the provisioned EBS performance and the selected EC2 instance's EBS limit.

## Storage Performance Assessment

| Metric | Normal | Sustained peak | Burst | Proposed capacity | Validation evidence |
|---|---:|---:|---:|---:|---|
| Read IOPS |  |  |  |  |  |
| Write IOPS |  |  |  |  |  |
| Read throughput |  |  |  |  |  |
| Write throughput |  |  |  |  |  |
| Read latency |  |  |  |  |  |
| Write latency |  |  |  |  |  |

## Availability, Recovery, and Oplog

| Item | Requirement | Proposed design | Validation evidence |
|---|---|---|---|
| Replica-set member placement |  |  |  |
| Read concern |  |  |  |
| Write concern |  |  |  |
| Read preference |  |  |  |
| Required oplog window |  |  |  |
| Backup frequency and retention |  |  |  |
| Restore time |  |  |  |
| Disaster recovery |  |  |  |

## Sharding Decision

| Evaluation | Result | Evidence |
|---|---|---|
| Replica-set capacity limit encountered |  |  |
| Candidate shard key |  |  |
| Cardinality |  |  |
| Frequency distribution |  |  |
| Monotonicity |  |  |
| Targeted-query percentage |  |  |
| `analyzeShardKey` result |  |  |
| Decision |  |  |

## Test Plan and Results

| Scenario | Data scale | Duration | Success criteria | Result | Evidence location |
|---|---:|---:|---|---|---|
| Normal workload |  |  |  |  |  |
| Sustained peak |  |  |  |  |  |
| Burst workload |  |  |  |  |  |
| Batch overlap |  |  |  |  |  |
| Node failure and election |  |  |  |  |  |
| Backup and restore |  |  |  |  |  |

## Assumptions, Risks, and Follow-Up

| ID | Type | Description | Impact | Owner | Due date | Status |
|---|---|---|---|---|---|---|
|  | Assumption / Risk / Unknown |  |  |  |  |  |

## Approval

| Role | Name | Decision | Date | Comments |
|---|---|---|---|---|
| Application owner |  |  |  |  |
| MongoDB DBA |  |  |  |  |
| Infrastructure or cloud architect |  |  |  |  |
| Security or compliance reviewer |  |  |  |  |
