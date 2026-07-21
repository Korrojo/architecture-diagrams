# MongoDB DBA Sizing Methodology

## Purpose

This guide converts application-team workload information into an initial MongoDB Enterprise sizing estimate. It applies to planning and architecture review; representative performance testing remains the final validation step.

## Evidence Classification

Every material input or sizing rule must be classified as one of the following:

| Classification | Meaning |
|---|---|
| Measured | Collected from source data, logs, monitoring, or a representative test |
| Business target | Required service level or future capacity target |
| Estimated | Application-team or DBA estimate without direct measurement |
| Heuristic | Planning rule from a documented source or field practice |
| Unknown | Required information not yet available |

Do not present a heuristic or estimate as a MongoDB product requirement.

## 1. Normalize and Aggregate Inputs

1. Confirm that all volumes have consistent units.
2. Separate logical/uncompressed data from MongoDB `storageSize` and `totalIndexSize`.
3. Separate average load from sustained peak and short burst load.
4. Record the measurement window and source for each measured value.
5. Aggregate workloads that will share the same replica set or sharded cluster.
6. Keep production, nonproduction, analytics, migration, and batch workloads distinct until architecture decisions are made.

## 2. AWS Sizing Exercise

The application questionnaire supplies workload demand. The DBA completes the AWS exercise with measurements, platform standards, and current AWS specifications.

### Step 1: Establish the target design point

Select the projection year and workload condition to size for. Normally this is the sustained peak at the approved planning horizon, not a short-lived maximum with no expected recurrence.

Record:

- Target projection year
- Normal, sustained-peak, and burst workload
- Peak duration
- Required unused capacity or safety factor
- Standard or exception RTO/RPO tier
- Replica-set member count and AZ/region placement

RTO and RPO affect topology, DR, restore performance, backup/PITR, and oplog requirements. They do not directly determine CPU or RAM for one data-bearing node.

### Step 2: Calculate storage capacity per node

For each target year, calculate:

```text
Required disk per node =
  (Stored collection data
   + Indexes
   + Oplog
   + Operational reserve)
  / (1 - Unused headroom percentage)
```

Capacity must be sufficient for a single data-bearing member. Multiply by the number of data-bearing members only for total infrastructure and cost estimates.

### Step 3: Determine RAM demand

Estimate hot collection data and hot index pages. Use the workbook's host-RAM result only as a planning floor. Validate it with representative load tests and WiredTiger cache metrics.

### Step 4: Determine CPU demand

Use a representative test configuration:

```text
Required vCPU = Tested vCPU × Observed peak CPU utilization / Target CPU utilization
```

Round upward and apply architecture standards. This calculation is valid only when the test dataset, indexes, concurrency, and queries represent the target workload.

### Step 5: Determine IOPS and throughput demand

Measure read and write IOPS and MiB/s during sustained peak, checkpoint, batch, migration, initial sync, and restore scenarios.

```text
Required IOPS = (Peak read IOPS + Peak write IOPS) × IOPS safety factor

Required throughput =
  (Peak read MiB/s + Peak write MiB/s) × Throughput safety factor
```

Evaluate IOPS and throughput separately. Either limit can become the bottleneck depending on I/O size.

### Step 6: Evaluate EBS candidates

For each approved EBS candidate, verify all of the following:

- Volume capacity is at least the required per-node disk capacity
- Provisioned IOPS meet required IOPS
- Provisioned throughput meets required throughput
- Requested IOPS and throughput are within the volume type's limits and ratios
- Expected latency is acceptable for the tested workload
- Selected EC2 instance can deliver the volume's provisioned performance

Current AWS documentation lists gp3 and io2 Block Express specifications. Treat workbook reference values as dated data and verify them against AWS documentation before approval.

### Step 7: Evaluate EC2 candidates

Start with organization-approved memory-optimized instances unless testing supports another family. For every candidate compare:

- vCPU against calculated CPU demand
- RAM against working-set and process-memory demand
- Baseline EBS IOPS and throughput against sustained requirements
- Maximum EBS IOPS and throughput against burst requirements
- Baseline and maximum network bandwidth against database, replication, backup, and monitoring traffic
- Processor architecture compatibility with MongoDB Enterprise, Ops Manager automation, security agents, backup agents, and application drivers

For instances with baseline/burst performance, use baseline values for sustained demand unless the peak duration and credit behavior have been explicitly validated.

### Step 8: Apply the lower-limit rule

Effective storage performance is bounded by the smaller of the EBS configuration and EC2 EBS limit:

```text
Effective IOPS = MIN(Provisioned volume IOPS, EC2 EBS IOPS limit)

Effective throughput = MIN(Provisioned volume throughput, EC2 EBS throughput limit)
```

An EBS volume can therefore be correctly provisioned but still be throttled by the EC2 instance.

### Step 9: Validate the complete candidate

Test the selected EC2 and EBS combination with the proposed schema, indexes, data distribution, encryption, agents, and workload. Include node failure, initial sync, backup, and restore scenarios when they are part of platform qualification.

## 3. Data and Storage Projection

Project logical data at launch and at one, three, and five years. Use application-supplied projections when available. Otherwise, document the growth model explicitly.

Example linear model:

```text
Projected logical data = Initial logical data + (Monthly logical growth × Number of months)
```

Example compound model:

```text
Projected logical data = Initial logical data × (1 + Annual growth rate) ^ Years
```

Estimate stored collection data from a representative sample whenever possible:

```text
Estimated stored data = Projected logical data × Measured storage-to-logical ratio
```

Estimate index storage separately. Prefer index builds on representative data over generic ratios.

Per-node storage must consider:

- Stored collection data
- Indexes
- Oplog
- Journal and diagnostic files
- Temporary space for index builds, compaction, initial sync, and maintenance
- Growth headroom

Do not multiply per-node disk capacity by replica-set member count when selecting the capacity of one node. Multiplication is used only for total infrastructure and cost estimates.

## 4. Working Set and Memory

The working set is the portion of data and indexes accessed frequently enough to benefit from memory. Estimate it from query time ranges, hot collections, hot tenants, frequently used indexes, and observed cache behavior.

Planning estimate:

```text
Hot working set = Hot collection data + Hot index pages
```

MongoDB documents that WiredTiger uses an internal cache and the operating system also uses available memory for filesystem cache. The default WiredTiger cache is the larger of `50% × (RAM - 1 GB)` or `0.256 GB`. Do not automatically increase it above the default.

Memory sizing must also reserve capacity for:

- Operating system and filesystem cache
- Connections and per-operation memory
- Aggregations and sorts
- Index builds
- Backup, monitoring, security, and management agents
- Other processes colocated on the host

Validate the estimate with representative reads and writes while observing cache eviction, page faults, latency, and disk activity.

## 5. CPU

Do not derive final CPU solely from data volume or a fixed CPU-to-RAM ratio. CPU demand depends on concurrency, query efficiency, compression, encryption, aggregation, index maintenance, transactions, and background work.

Use the questionnaire to identify CPU-sensitive features:

- High concurrent operation counts
- Aggregation pipelines and large sorts
- Compression and encryption
- High write rates with multiple indexes
- Multi-document transactions
- Initial loads, index builds, and backups
- Search or vector processing

MongoDB production notes recommend at least two real cores or one multi-core physical CPU per `mongod` or `mongos`, but production core count must be validated against the workload.

## 6. Storage IOPS, Throughput, and Latency

Capacity and performance are separate decisions. Evaluate:

- Read and write IOPS
- Sequential and random throughput
- Average and tail latency
- Checkpoint behavior
- Journal writes
- Index maintenance
- Initial sync and restore throughput
- EBS and EC2 bandwidth limits

Use a representative workload to measure IOPS and throughput. Provider rules of thumb may be used only as documented heuristics. For AWS, verify current gp3 or io2 limits and the selected EC2 instance's EBS bandwidth before recommending a configuration.

## 7. Network

Estimate traffic among applications, drivers, replica-set members, shards, backup services, and monitoring systems. Consider:

- Peak request and response payloads
- Replication traffic generated by writes
- Initial sync, backup, and restore traffic
- Cross-AZ or cross-region traffic
- Latency between application and database nodes
- Latency among voting members

Network compression assumptions must be measured with the selected driver and payloads.

## 8. Oplog

Size the oplog from the measured or tested oplog generation rate and the required recovery window:

```text
Required oplog capacity = Peak oplog generation per hour × Required oplog window hours × Safety factor
```

The required window must cover anticipated replication interruptions, change-stream consumer outages, maintenance, and migration CDC requirements. Measure oplog growth because update patterns and document structure can make it differ materially from business-data growth.

## 9. Replica Set, Availability, and Recovery

Translate application RTO, RPO, maintenance, and regional requirements into topology decisions. Document:

- Voting and data-bearing members
- Availability-zone placement
- Read and write concerns
- Read preference
- Backup frequency and retention
- Restore method and tested restore time
- Disaster-recovery location and activation process

Application teams provide service requirements; the DBA and architect select the topology.

## 10. Sharding Assessment

Do not recommend sharding only because the projected dataset is large. Evaluate whether a replica set can meet storage, throughput, maintenance, and growth requirements.

If sharding may be required, assess candidate shard keys using:

- Cardinality
- Frequency distribution
- Monotonicity
- Targeted versus scatter-gather query patterns
- Read and write distribution
- Zone or locality requirements

MongoDB provides `analyzeShardKey` for data-driven assessment using sampled queries. Record both the proposed key and the supporting workload evidence.

## 11. Index Assessment

Build the index plan from common query shapes, not from fields viewed in isolation. Review:

- Equality filters
- Sort fields and direction
- Range filters
- Projection and covered-query opportunities
- Uniqueness requirements
- Arrays and multikey behavior
- TTL, partial, sparse, wildcard, text, geospatial, hashed, and vector indexes
- Index build and maintenance cost
- Write-to-read ratio

MongoDB recommends identifying common queries, creating supporting indexes, measuring index use, and periodically removing unnecessary indexes. The ESR guideline is a starting point for compound-index order, subject to query selectivity and testing.

## 12. Validation and Right-Sizing

Before production approval:

1. Generate representative document sizes and value distributions.
2. Create the proposed schema and indexes.
3. Load a meaningful data volume.
4. Run normal, sustained peak, burst, batch, and failure scenarios.
5. Measure latency percentiles, throughput, CPU, cache, disk, replication lag, and connection behavior.
6. Test backup and restore against RTO and RPO.
7. Record the configuration and test evidence.
8. Revise the sizing assessment.

Repeat right-sizing after production metrics represent a normal business cycle.

## Sources

### Primary sources

- MongoDB production notes for self-managed deployments: https://www.mongodb.com/docs/manual/administration/production-notes/
- MongoDB WiredTiger storage engine: https://www.mongodb.com/docs/manual/core/wiredtiger/
- MongoDB schema design process: https://www.mongodb.com/docs/manual/data-modeling/schema-design-process/
- Identify application workload: https://www.mongodb.com/docs/manual/data-modeling/schema-design-process/identify-workload/
- Create indexes to support queries: https://www.mongodb.com/docs/manual/data-modeling/schema-design-process/create-indexes/
- ESR guideline: https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/
- Replication: https://www.mongodb.com/docs/manual/replication/
- Read concern: https://www.mongodb.com/docs/manual/reference/read-concern/
- Write concern: https://www.mongodb.com/docs/manual/reference/write-concern/
- Choose a shard key: https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/
- MongoDB limits: https://www.mongodb.com/docs/manual/reference/limits/
- Amazon EBS volume types: https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html
- Amazon EC2 memory-optimized instance specifications: https://docs.aws.amazon.com/ec2/latest/instancetypes/mo.html
- Amazon EC2 EBS-optimized instance tables: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-optimized.html
- Amazon EBS gp3 specifications: https://docs.aws.amazon.com/ebs/latest/userguide/general-purpose.html
- Amazon EBS io2 Block Express specifications: https://docs.aws.amazon.com/ebs/latest/userguide/provisioned-iops.html

### Secondary source reviewed

- OVHcloud MongoDB cluster sizing: https://docs.ovhcloud.com/en/guides/public-cloud/databases/mongodb-cluster-sizing

The OVHcloud formulas are treated as planning heuristics and are not copied as MongoDB product requirements or AWS deployment specifications.
