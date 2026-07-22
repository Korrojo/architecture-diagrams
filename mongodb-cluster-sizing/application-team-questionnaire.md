# MongoDB Application Sizing Questionnaire

## Instructions

- Complete one questionnaire for each application or materially different workload.
- Use units such as documents, requests/second, GB, TB, minutes, or hours.
- Mark each answer as `Measured`, `Estimated`, or `Unknown`.
- Replace the sample answers below with values for your application. The samples show the expected level of detail only.
- Do not select CPU, RAM, storage type, replica-set size, or shard count. The MongoDB DBA will determine those from the answers.

| No. | Question | Application-team answer — sample to replace | Measured / Estimated / Unknown | Notes or source |
|---:|---|---|---|---|
| 1 | Briefly describe the application and its main use of MongoDB. Is it a new application or a migration? | Customer order-management application storing orders, status history, and fulfillment events. This is a migration from an existing relational database. | Measured | Current production application and migration design. |
| 2 | How much data and how many records/documents will be loaded initially? | Approximately 500 GB representing 120 million documents will be loaded before go-live. This excludes indexes. | Estimated | Current source contains 430 GB and 110 million records; estimate includes growth before migration. |
| 3 | What are the major collections, and what is the approximate average and maximum document size for each? | `orders`: 60 million documents, 4 KB average, 200 KB maximum.<br>`customers`: 10 million documents, 2 KB average, 20 KB maximum.<br>`events`: 50 million documents, 1 KB average, 5 KB maximum. | Measured | Sizes were calculated from a representative source-data sample. |
| 4 | What total data volume and document count do you expect after 1 year, 3 years, and 5 years? | Year 1: 750 GB and 180 million documents.<br>Year 3: 1.4 TB and 340 million documents.<br>Year 5: 2.2 TB and 540 million documents. Expected growth is approximately 25 GB and 6 million documents per month. | Estimated | Business forecast assumes transaction growth of approximately 15% per year. Figures exclude indexes and operational headroom. |
| 5 | How long must data remain in MongoDB before it can be deleted or archived? | Orders and customer records remain online for 7 years. Detailed fulfillment events remain online for 24 months and can then be archived. | Estimated | Based on application reporting requirements; final archival process is still being designed. |
| 6 | What are the normal and peak numbers of reads, inserts, updates, and deletes per second? How long does the peak normally last? | Normal: 150 reads/sec, 40 inserts/sec, 25 updates/sec, and fewer than 5 deletes/sec.<br>Peak: 600 reads/sec, 150 inserts/sec, 100 updates/sec, and 10 deletes/sec. Peaks last 15–30 minutes. A monthly two-hour batch may add 250 writes/sec. | Estimated | Based on current API traffic with 30% growth added; performance testing is pending. |
| 7 | How many simultaneous users, application connections, or concurrent operations are expected during normal and peak periods? | About 500 simultaneous users normally and 2,000 at peak. Ten application instances will each have a connection pool capped at 50, for a maximum of 500 application connections. Approximately 50–100 database operations may run concurrently, rising to 250 at peak. | Estimated | User concurrency comes from current monitoring; connection and operation counts are based on the proposed deployment. |
| 8 | What are the most frequent and most critical queries? For each, list the filter fields, sort fields, and approximate number of documents returned. | Most frequent: find orders by `customerId` and `status`, sorted by `createdAt` descending; normally returns 20–50 documents.<br>Most critical: find one order by `orderId`; returns one document.<br>Operations search: filter by `status` and `updatedAt` range, sort by `updatedAt`; returns up to 500 documents per page. | Measured | Query shapes were taken from current API endpoints; sample queries contain no customer values. |
| 9 | What indexes are proposed or currently used for the major collections? | `orders`: unique `{orderId: 1}`, compound `{customerId: 1, status: 1, createdAt: -1}`, and `{status: 1, updatedAt: -1}`.<br>`customers`: unique `{customerId: 1}`.<br>`events`: compound `{orderId: 1, eventTime: -1}`. | Estimated | Proposed from known query patterns; the DBA will validate index order and remove redundant indexes after workload testing. |
| 10 | Are there scheduled reports, aggregations, imports, exports, or batch jobs? State their frequency, duration, and approximate data volume. | A nightly sales aggregation scans about 20 GB and normally completes in 30 minutes. A monthly finance export reads approximately 100 GB and runs for up to two hours. A daily partner import writes about 2 million documents over 45 minutes. | Measured | Current scheduler history and batch logs. |
| 11 | Can individual documents grow over time because records are embedded or added to arrays? If yes, provide the expected maximum document or array size. | Order documents contain an embedded status-history array. A typical order has fewer than 20 entries; the expected maximum is 500 entries and approximately 200 KB for the complete document. Unbounded events will be stored in the separate `events` collection. | Estimated | Maximum is based on the longest-running orders in the current system. |
| 12 | Is there an initial bulk load or migration followed by ongoing changes before cutover? Provide the load volume, available load window, ongoing change rate, and expected duration. | Yes. The initial load is approximately 500 GB/120 million documents and must complete within 24 hours. Change data capture will then apply an average of 50 and a peak of 200 changes/sec for up to seven days before cutover. The final cutover window is two hours. | Estimated | Rates are based on current transaction logs; a migration performance test is required. |

## DBA Review

| Review item | DBA notes |
|---|---|
| Missing or unknown sizing inputs |  |
| Values requiring measurement or sampling |  |
| Representative data sample available | Yes / No |
| Representative workload test required | Yes / No |
