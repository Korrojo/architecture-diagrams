# MongoDB Application Sizing Questionnaire

## Instructions

- Complete one questionnaire for each application or materially different workload.
- Use units such as documents, requests/second, GB, TB, minutes, or hours.
- Mark each answer as `Measured`, `Estimated`, or `Unknown`.
- Do not select CPU, RAM, storage type, replica-set size, or shard count. The MongoDB DBA will determine those from the answers.

| No. | Question | Application-team answer | Measured / Estimated / Unknown | Notes or source |
|---:|---|---|---|---|
| 1 | Briefly describe the application and its main use of MongoDB. Is it a new application or a migration? |  |  |  |
| 2 | How much data and how many records/documents will be loaded initially? |  |  | Include GB/TB and record/document count. |
| 3 | What are the major collections, and what is the approximate average and maximum document size for each? |  |  | Use KB or MB. |
| 4 | What total data volume and document count do you expect after 1 year, 3 years, and 5 years? |  |  | Include expected monthly or annual growth if known. |
| 5 | How long must data remain in MongoDB before it can be deleted or archived? |  |  | Identify different retention periods if they vary by data type. |
| 6 | What are the normal and peak numbers of reads, inserts, updates, and deletes per second? How long does the peak normally last? |  |  | Provide production measurements when available. |
| 7 | How many simultaneous users, application connections, or concurrent operations are expected during normal and peak periods? |  |  |  |
| 8 | What are the most frequent and most critical queries? For each, list the filter fields, sort fields, and approximate number of documents returned. |  |  | Attach sample query shapes if available; remove real values. |
| 9 | What indexes are proposed or currently used for the major collections? |  |  | List indexed fields, compound field order, uniqueness, and special index types if known. |
| 10 | Are there scheduled reports, aggregations, imports, exports, or batch jobs? State their frequency, duration, and approximate data volume. |  |  |  |
| 11 | Can individual documents grow over time because records are embedded or added to arrays? If yes, provide the expected maximum document or array size. |  |  |  |
| 12 | Is there an initial bulk load or migration followed by ongoing changes before cutover? Provide the load volume, available load window, ongoing change rate, and expected duration. |  |  | Enter `Not applicable` for a new application without migration. |

## DBA Review

| Review item | DBA notes |
|---|---|
| Missing or unknown sizing inputs |  |
| Values requiring measurement or sampling |  |
| Representative data sample available | Yes / No |
| Representative workload test required | Yes / No |