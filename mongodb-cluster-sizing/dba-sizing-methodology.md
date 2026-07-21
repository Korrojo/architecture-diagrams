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

## 2. Data and Storage Projection

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

## 3. Working Set and Memory

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

## 4. CPU

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

## 5. Storage IOPS, Throughput, and Latency

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

## 6. Network

Estimate traffic among applications, drivers, replica-set members, shards, backup services, and monitoring systems. Consider:

- Peak request and response payloads
- Replication traffic generated by writes
- Initial sync, backup, and restore traffic
- Cross-AZ or cross-region traffic
- Latency between application and database nodes
- Latency among voting members

Network compression assumptions must be measured with the selected driver and payloads.

## 7. Oplog

Size the oplog from the measured or tested oplog generation rate and the required recovery window:

```text
Required oplog capacity = Peak oplog generation per hour × Required oplog window hours × Safety factor
```

The required window must cover anticipated replication interruptions, change-stream consumer outages, maintenance, and migration CDC requirements. Measure oplog growth because update patterns and document structure can make it differ materially from business-data growth.

## 8. Replica Set, Availability, and Recovery

Translate application RTO, RPO, maintenance, and regional requirements into topology decisions. Document:

- Voting and data-bearing members
- Availability-zone placement
- Read and write concerns
- Read preference
- Backup frequency and retention
- Restore method and tested restore time
- Disaster-recovery location and activation process

Application teams provide service requirements; the DBA and architect select the topology.

## 9. Sharding Assessment

Do not recommend sharding only because the projected dataset is large. Evaluate whether a replica set can meet storage, throughput, maintenance, and growth requirements.

If sharding may be required, assess candidate shard keys using:

- Cardinality
- Frequency distribution
- Monotonicity
- Targeted versus scatter-gather query patterns
- Read and write distribution
- Zone or locality requirements

MongoDB provides `analyzeShardKey` for data-driven assessment using sampled queries. Record both the proposed key and the supporting workload evidence.

## 10. Index Assessment

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

## 11. Validation and Right-Sizing

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

### Secondary source reviewed

- OVHcloud MongoDB cluster sizing: https://docs.ovhcloud.com/en/guides/public-cloud/databases/mongodb-cluster-sizing

The OVHcloud formulas are treated as planning heuristics and are not copied as MongoDB product requirements or AWS deployment specifications.
