# MongoDB Application Sizing Questionnaire

## Instructions

- Complete one questionnaire for each application or materially different workload.
- Use units in every numeric answer: documents, requests/second, MB, GB, TB, minutes, or hours.
- In **Answer basis**, enter `Measured`, `Estimated`, `Business target`, or `Unknown`.
- For measured answers, identify the report, log, query, or monitoring period in **Notes / evidence**.
- Do not include credentials, hostnames, internal URLs, customer names, or sensitive sample data.
- If separate workloads will share a cluster, the DBA will aggregate them after collection.

## 1. Application and Service Profile

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| APP-01 | What business capability does the application provide? |  |  |  |
| APP-02 | Is this a new application, an existing application, or a migration? |  |  |  |
| APP-03 | Which environments are required: development, test, staging, production, disaster recovery, or others? |  |  |  |
| APP-04 | What is the planned production launch date? |  |  |  |
| APP-05 | How critical is the service: low, moderate, high, or mission critical? |  |  |  |
| APP-06 | Who owns the application, data model, and workload estimates? Use team names or roles only. |  |  |  |

## 2. Initial Data Profile

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| DATA-01 | What is the expected logical data volume at launch, before MongoDB compression? |  |  |  |
| DATA-02 | How many records or MongoDB documents are expected at launch? |  |  |  |
| DATA-03 | How many collections are expected at launch? |  |  |  |
| DATA-04 | What is the estimated average document size for each major collection? |  |  |  |
| DATA-05 | What is the estimated largest normal document size for each major collection? |  |  |  |
| DATA-06 | Could any document grow continuously because events, history, comments, or items are appended to an embedded array? Describe the expected maximum. |  |  |  |
| DATA-07 | Are files, images, PDFs, audio, video, or other large binary objects stored in or referenced by the database? Provide average and maximum sizes. |  |  |  |
| DATA-08 | Are any fields highly repetitive, sparse, optional, encrypted, or already compressed? |  |  |  |
| DATA-09 | Is representative source data available for sampling document size and compression? State the approximate sample size. |  |  |  |
| DATA-10 | List the three to five collections expected to contain the most data. |  |  |  |

### Data-volume projection

| Measure | At launch | After 1 year | After 3 years | After 5 years | Basis / notes |
|---|---:|---:|---:|---:|---|
| Logical data volume |  |  |  |  |  |
| Document count |  |  |  |  |  |
| Estimated index volume, if known |  |  |  |  |  |

## 3. Growth, Retention, and Data Lifecycle

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| GROW-01 | How many new documents are created during a normal day and the busiest day? |  |  |  |
| GROW-02 | How much logical data is added during a normal month and the busiest month? |  |  |  |
| GROW-03 | Is growth expected to be linear, seasonal, event-driven, or exponential? Describe the pattern. |  |  |  |
| GROW-04 | What annual growth percentage is expected for users, transactions, documents, and data volume? |  |  |  |
| GROW-05 | How long must active data remain immediately queryable? |  |  |  |
| GROW-06 | Which data can expire automatically, and what retention period applies to each category? |  |  |  |
| GROW-07 | Must expired data be archived before deletion? If yes, state the archive destination, retrieval frequency, and required retrieval time. |  |  |  |

## 4. Data Model and Document Behavior

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| MODEL-01 | List the principal business entities that will become MongoDB documents or collections. |  |  |  |
| MODEL-02 | Which relationships are one-to-one, one-to-many, or many-to-many? |  |  |  |
| MODEL-03 | Which related data is expected to be embedded in the same document, and which is expected to be referenced? |  |  |  |
| MODEL-04 | What is the maximum expected number of elements in each embedded array? |  |  |  |
| MODEL-05 | Are documents frequently updated in place, appended to, or replaced as a whole? Identify the affected collections. |  |  |  |
| MODEL-06 | Are the same data elements duplicated across documents to improve reads? If yes, how are duplicates synchronized? |  |  |  |
| MODEL-07 | Is schema versioning required because document structure will change over time? Describe known versions or planned changes. |  |  |  |

## 5. Workload and Traffic Pattern

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| LOAD-01 | How many application users or client systems are expected at launch and at peak? |  |  |  |
| LOAD-02 | What are the average and peak read requests per second? |  |  |  |
| LOAD-03 | What are the average and peak insert requests per second? |  |  |  |
| LOAD-04 | What are the average and peak update requests per second? |  |  |  |
| LOAD-05 | What are the average and peak delete requests per second? |  |  |  |
| LOAD-06 | What percentage of the workload is reads versus writes? |  |  |  |
| LOAD-07 | Describe hourly, daily, weekly, monthly, seasonal, or event-driven peaks and their expected duration. |  |  |  |
| LOAD-08 | Are there batch imports, exports, reconciliations, reports, or maintenance jobs? State schedule, duration, and volume. |  |  |  |
| LOAD-09 | How many simultaneous application connections or concurrent operations are expected at average and peak load? |  |  |  |

### Peak-workload summary

| Measure | Normal | Peak | Peak duration | Future peak after 3 years | Basis / notes |
|---|---:|---:|---|---:|---|
| Reads per second |  |  |  |  |  |
| Inserts per second |  |  |  |  |  |
| Updates per second |  |  |  |  |  |
| Deletes per second |  |  |  |  |  |
| Concurrent operations |  |  |  |  |  |

## 6. Query, Reporting, Search, and Index Strategy

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| QUERY-01 | List the most frequent user or system actions that read or write data. |  |  |  |
| QUERY-02 | For each important read, which fields are used for exact-match filters? |  |  |  |
| QUERY-03 | Which fields are used for range filters such as date, amount, or status ranges? |  |  |  |
| QUERY-04 | Which fields and directions are used for sorting? |  |  |  |
| QUERY-05 | Which fields are normally returned, and approximately how many documents are returned per request? |  |  |  |
| QUERY-06 | Are aggregations, grouping, joins, window calculations, or large sorts required? Describe frequency and expected data scanned. |  |  |  |
| QUERY-07 | Does the application require keyword, text, autocomplete, geospatial, time-series, or vector similarity search? |  |  |  |
| QUERY-08 | What pagination method is planned: cursor/range based, continuation token, or page-number with skip/limit? |  |  |  |
| QUERY-09 | What indexes are currently proposed for each collection, including field order and uniqueness? |  |  |  |
| QUERY-10 | Are TTL, partial, sparse, wildcard, multikey, text, geospatial, hashed, or unique indexes expected? Explain the related query or rule. |  |  |  |

### Important query and operation inventory

| Business action | Read / write | Collection(s) | Filter fields | Sort fields | Returned fields / count | Average frequency | Peak frequency | Required response time | Priority |
|---|---|---|---|---|---|---:|---:|---|---|
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

## 7. Consistency, Transactions, and Integrations

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| CONS-01 | Must users immediately read their own writes, or is a short delay acceptable? |  |  |  |
| CONS-02 | Can any reads use slightly stale data, such as reporting reads from a secondary? State the acceptable delay. |  |  |  |
| CONS-03 | Are multi-document transactions required? Describe the business action, collections involved, operations per transaction, and frequency. |  |  |  |
| CONS-04 | Are change streams required? Describe consumers, filtering, event rate, and the longest expected consumer outage. |  |  |  |
| CONS-05 | Which upstream and downstream systems exchange data with MongoDB, and by what method? |  |  |  |
| CONS-06 | Are duplicate, late, or out-of-order events possible? Describe application requirements for idempotency and ordering. |  |  |  |

## 8. Availability, Recovery, and Migration

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| OPS-01 | What is the maximum acceptable unplanned service interruption? |  |  |  |
| OPS-02 | What recovery time objective (RTO) is required after a major failure? |  |  |  |
| OPS-03 | What recovery point objective (RPO), or maximum acceptable data loss, is required? |  |  |  |
| OPS-04 | What maintenance windows and planned downtime are acceptable? |  |  |  |
| OPS-05 | For a migration, what are the source data volume, source record count, initial-load window, and expected change rate during migration? |  |  |  |
| OPS-06 | Is a one-time load sufficient, or is ongoing CDC required before cutover? State the expected CDC duration and cutover downtime. |  |  |  |

## 9. Security, Compliance, and Future Change

| ID | Question | Application-team answer | Answer basis | Notes / evidence |
|---|---|---|---|---|
| SEC-01 | What data classifications apply: public, internal, confidential, regulated, or restricted? |  |  |  |
| SEC-02 | Are encryption, field-level encryption, customer-managed keys, auditing, or data-residency controls required? |  |  |  |
| SEC-03 | Are there regulatory retention, legal hold, purge, or right-to-delete requirements? |  |  |  |
| FUT-01 | What major features, integrations, acquisitions, geographic expansion, or workload changes are expected within five years? |  |  |  |

## Submission Confirmation

| Confirmation | Answer |
|---|---|
| Questionnaire completed by |  |
| Team or role |  |
| Completion date |  |
| Estimates reviewed by |  |
| Known unknowns or unresolved assumptions |  |

## DBA Review Use Only

| Review item | DBA notes |
|---|---|
| Missing required answers |  |
| Conflicting estimates |  |
| Values requiring measurement |  |
| Data sample required |  |
| Workload test required |  |
| Sizing decision status | Draft / Reviewed / Approved |
