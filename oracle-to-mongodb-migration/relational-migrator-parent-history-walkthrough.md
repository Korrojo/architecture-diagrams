# Oracle-to-MongoDB Relational Migrator Learning Labs

_Last reviewed: July 30, 2026_

## Purpose

This teaching guide documents three progressively more advanced MongoDB Relational Migrator workflows using the same sanitized Oracle sample:

- `PRODUCT_CATALOG_ITEM`: the current state of a catalog item
- `PRODUCT_PRICE_HISTORY`: historical price changes for the catalog item

Students can migrate one table directly, migrate both tables as separate collections with a reference, or embed the history rows inside the parent document.

All source names and infrastructure details in this guide are sanitized. Replace them with approved local values from the source data dictionary. Never place credentials, internal hostnames, or production data in a public repository.

## Learning Path

```mermaid
flowchart TD
    S["Start with source analysis and connections"] --> L1["Lab 1: One table → one collection"]
    L1 --> L2["Lab 2: Two tables → two referenced collections"]
    L2 --> L3["Lab 3: Two tables → parent with embedded array"]
```

| Lab | Source scope | MongoDB outcome | Use it to learn |
|---|---|---|---|
| 1. Direct mapping | `PRODUCT_CATALOG_ITEM` only | `catalogItems` | The simplest snapshot, field mapping, and validation workflow |
| 2. Reference model | Both tables | `catalogItems` and `priceHistoryEvents` | Separate collections, retained join key, indexes, and application-side or `$lookup` joins |
| 3. Embedded model | Both tables | `catalogItems` with `priceHistory[]` | One-to-many embedding, redundant-field removal, array ordering, and document growth |

Create a separate Relational Migrator project, or a deliberate copy of the base project, for each lab. Reference and embedded mappings are alternative target designs; do not combine both in the same student result unless duplicating the child data is an explicit requirement.

### Choosing between the three models

| Condition | Direct mapping | Reference model | Embedded model |
|---|---:|---:|---:|
| Only one independent table is in scope | Best fit | Not applicable | Not applicable |
| Child records are queried or retained independently | — | Prefer | Avoid unless also bounded and read with parent |
| Child collection grows without a practical bound | — | Prefer | Avoid |
| Parent and children are usually read together | — | Possible | Prefer |
| Aggregate should be updated atomically in one document | — | No | Prefer |
| Child has a separate lifecycle or very high write rate | — | Prefer | Usually avoid |

Embedding is not automatically better than referencing. Choose from application access patterns, lifecycle, write behavior, child cardinality, retention, and the MongoDB document-size limit—not merely from the presence of a foreign key.

```javascript
{
  _id: ObjectId("..."),
  itemKey: "ITEM-10001",
  sku: "SKU-20001",
  productName: "Example Product",
  categoryCode: "OFFICE",
  supplierKey: "SUP-30001",
  currentPrice: NumberDecimal("29.95"),
  currencyCode: "USD",
  active: true,
  createdAt: ISODate("2026-07-01T12:00:00.000Z"),
  updatedAt: ISODate("2026-07-02T14:30:00.000Z"),
  priceHistory: [
    {
      priceEventId: 501,
      previousPrice: NumberDecimal("24.95"),
      newPrice: NumberDecimal("29.95"),
      currencyCode: "USD",
      changeReason: "Annual price review",
      changeAction: "INCREASE",
      effectiveAt: ISODate("2026-07-02T00:00:00.000Z"),
      recordedAt: ISODate("2026-07-02T14:30:00.000Z")
    }
  ]
}
```

## 1. Preliminary Analysis

### 1.1 Confirm the business relationship

Establish that:

- `PRODUCT_CATALOG_ITEM.ITEM_KEY` identifies the current catalog item.
- `PRODUCT_PRICE_HISTORY.ITEM_KEY` refers to the parent catalog item.
- The relationship is one parent to zero or more history rows.
- History normally belongs to and is read with the current catalog item.
- History retention and growth will not create unbounded MongoDB documents.

Do not decide to embed solely because a foreign key exists. The application access pattern and maximum child cardinality must support embedding.

### 1.2 Collect source statistics

Run equivalent queries using the approved schema owner:

```sql
SELECT COUNT(*) AS parent_rows
FROM <SOURCE_OWNER>.PRODUCT_CATALOG_ITEM;

SELECT
    COUNT(*) AS history_rows,
    COUNT(DISTINCT ITEM_KEY) AS parents_with_history
FROM <SOURCE_OWNER>.PRODUCT_PRICE_HISTORY;

SELECT MAX(history_count) AS maximum_price_history_rows_per_item
FROM (
    SELECT ITEM_KEY, COUNT(*) AS history_count
    FROM <SOURCE_OWNER>.PRODUCT_PRICE_HISTORY
    GROUP BY ITEM_KEY
);
```

Check parent-key quality:

```sql
SELECT ITEM_KEY, COUNT(*) AS duplicate_count
FROM <SOURCE_OWNER>.PRODUCT_CATALOG_ITEM
GROUP BY ITEM_KEY
HAVING COUNT(*) > 1;

SELECT COUNT(*) AS null_item_keys
FROM <SOURCE_OWNER>.PRODUCT_CATALOG_ITEM
WHERE ITEM_KEY IS NULL;
```

Check for orphaned history:

```sql
SELECT COUNT(*) AS orphan_history_rows
FROM <SOURCE_OWNER>.PRODUCT_PRICE_HISTORY h
LEFT JOIN <SOURCE_OWNER>.PRODUCT_CATALOG_ITEM p
    ON p.ITEM_KEY = h.ITEM_KEY
WHERE p.ITEM_KEY IS NULL;
```

Embedding is reasonable when the maximum history count remains controlled and the resulting document stays well below MongoDB's 16 MiB BSON document limit. Keep history as a separate collection if it can grow indefinitely, is queried independently, or has a separate lifecycle.

### 1.3 Inspect keys, constraints, and types

Confirm:

- Whether `ITEM_KEY` is a declared primary key, a unique key, or merely unique in current data.
- The exact foreign-key relationship.
- Nullable columns.
- Oracle `NUMBER` precision and scale.
- Timestamp types and timezone semantics.
- Maximum lengths of product names, change reasons, and identifier columns.

Relational Migrator can inherit a declared single-column primary key into MongoDB `_id`. If the parent has no declared primary key, its default is an autogenerated `ObjectId`. In that case, retain `itemKey` as a separate field and create a unique MongoDB index only after proving the field is non-null and unique.

### 1.4 Run Pre-Migration Analysis

In the project, open **Pre-Migration Analysis** and select **Run analysis**.

The report can identify:

- Unsupported Oracle features
- Data-type incompatibilities
- Schema-mapping risks
- Migration-performance risks

The feature is a public preview and is advisory. It normally takes several minutes to crawl the source database.

#### If connection testing succeeds but analysis fails

A successful connection test proves basic authentication and connectivity; it does not prove that the account can read all metadata needed by the analysis.

Common causes include:

- The account reads tables owned by another schema but lacks catalog permissions.
- The project uses a generic/custom JDBC connection. Pre-Migration Analysis supports Oracle through the supported Oracle connection, not generic JDBC sources.
- Relational Migrator cannot discover cross-schema key metadata.
- The installed Relational Migrator version has a source-specific defect.

For a Linux installation, inspect:

```bash
grep -Ei 'ORA-|analysis|error|exception' \
  ~/.mongodb/relational-migrator/migrator.log | tail -100
```

If Relational Migrator runs as another operating-system account, inspect the same path under that service account's home directory. Do not include credentials or internal infrastructure details when sharing logs.

Pre-Migration Analysis is optional. If the preview feature remains unavailable, complete the manual checks in this guide and run a controlled test snapshot with verification.

## 2. Required Access

Use dedicated migration service accounts. Do not build a repeatable migration around a person's account.

### 2.1 Oracle permissions

The source user should not copy or export another schema's tables into its own schema merely to make Relational Migrator work. Copying can omit constraints, relationships, indexes, statistics, triggers, and ownership semantics.

MongoDB documents the following baseline when the Relational Migrator account owns the source tables:

```sql
GRANT CREATE SESSION TO <MIGRATOR_USER>;
GRANT SELECT ON V_$DATABASE TO <MIGRATOR_USER>;
```

When the migration account does not own the tables:

```sql
GRANT CREATE SESSION TO <MIGRATOR_USER>;
GRANT SELECT_CATALOG_ROLE TO <MIGRATOR_USER>;
GRANT SELECT ANY TABLE TO <MIGRATOR_USER>;
GRANT SELECT ON V_$DATABASE TO <MIGRATOR_USER>;
GRANT FLASHBACK ANY TABLE TO <MIGRATOR_USER>;
```

These are broad Oracle privileges. The Oracle DBA and security team must review and approve them. In a multitenant Oracle deployment, grants may require `CONTAINER=ALL`; follow the generated prerequisite script and the organization's Oracle standards.

For a narrowly scoped test, direct `SELECT` grants may be sufficient to read the two tables, but the analysis or snapshot-prerequisite check may still report missing database-level access.

### 2.2 MongoDB permissions

Create a dedicated MongoDB user with `readWrite` on the target database:

```javascript
use admin

db.createUser({
  user: "relational_migrator_writer",
  pwd: passwordPrompt(),
  roles: [
    { role: "readWrite", db: "migration_test" }
  ]
})
```

Use the organization's approved authentication mechanism and TLS settings. Do not place a password in the project name, documentation, Git, screenshots, or a connection URI stored in source control.

### 2.3 Credential handling

A saved Relational Migrator connection can be reused across projects and migration jobs. The credentials supplied for a migration job do not need to be the same credentials used when the project was created.

Recommended practice:

- Save connection metadata using a clear name such as `oracle-sat-product-catalog` or `mongodb-sat-product-catalog`.
- Add the correct environment tag.
- Enter secrets in the credential fields rather than embedding them in documentation.
- Avoid saving personal credentials on a shared Relational Migrator server.
- Prefer a controlled service account whose password lifecycle is managed through the organization's secrets process.

When **Save password** is selected, Relational Migrator stores the password securely on the machine where Relational Migrator runs. On a shared EC2 host, that machine is the server, not the administrator's browser workstation.

## 3. Build the Connections

### 3.1 Oracle source connection

1. Create or open the Relational Migrator project.
2. Select **Connect to live database**.
3. Choose the supported Oracle database type.
4. Supply the approved host, port, service name or SID, and migration-user credentials.
5. Give the connection a readable name and environment tag.
6. Test the connection.
7. Select the source schema and the two tables.
8. Refresh the schema after any privilege or source-DDL change.

If schema discovery cannot see the real cross-schema relationship, use a DDL import for modeling or create a synthetic foreign key in Relational Migrator. A live source connection is still required to move the data.

### 3.2 MongoDB destination connection

1. At the top of the project or during migration-job creation, select **Add MongoDB connection**.
2. Enter the replica-set connection string and target database.
3. Enter the dedicated migration-writer credentials.
4. Test the connection.
5. Give it a readable name and environment tag.

Use a dedicated empty test database for the first migration. Confirm the target database name before enabling any option that drops destination collections.

## 4. Create Separate Lab Projects

Use a common naming pattern:

```text
<application>-<domain>-<model>-<environment>
```

Sanitized lab examples:

```text
catalog-pricing-single-table-lab
catalog-pricing-reference-lab
catalog-pricing-embedded-lab
```

Use `camelCase` for MongoDB collection and field names. Start each lab from a separate project or project copy so its mappings and validation results remain unambiguous.

A production project can contain multiple related tables and migration jobs. The separate-project recommendation here is for teaching and design comparison, not a Relational Migrator limitation.

## 5. Lab 1 — Migrate One Table Directly

This is the simplest workflow: one Oracle table becomes one MongoDB collection, without relationships or embedded arrays.

### 5.1 Initial mapping

1. Select only `PRODUCT_CATALOG_ITEM`.
2. Select **Start with a MongoDB schema that matches your relational schema** for the clearest one-to-one exercise. The recommended schema is also acceptable if it produces one top-level collection.
3. Map the table as **New documents**.
4. Name the collection `catalogItems`.

### 5.2 Field mapping

| Source column | MongoDB field | Treatment |
|---|---|---|
| `ITEM_KEY` | `itemKey` | Retain as the business key |
| `SKU` | `sku` | Retain |
| `PRODUCT_NAME` | `productName` | Retain |
| `CATEGORY_CODE` | `categoryCode` | Retain |
| `SUPPLIER_KEY` | `supplierKey` | Retain |
| `CURRENT_PRICE` | `currentPrice` | Map to the approved decimal type |
| `CURRENCY_CODE` | `currencyCode` | Retain |
| `ACTIVE_FLAG` | `active` | Convert to the agreed Boolean representation |
| `CREATED_AT` | `createdAt` | Map to BSON Date |
| `UPDATED_AT` | `updatedAt` | Map to BSON Date |

### 5.3 `_id` decision

- If `ITEM_KEY` is a declared, non-null, single-column Oracle primary key, consider **Single Inherited Primary Key**.
- If it is only a unique constraint or logical key, keep the default `ObjectId` and retain `itemKey`.
- Use the same parent `_id` decision in Labs 2 and 3 so the results are comparable.

Expected document shape:

```javascript
{
  _id: ObjectId("..."),
  itemKey: "ITEM-10001",
  sku: "SKU-20001",
  productName: "Example Product",
  categoryCode: "OFFICE",
  supplierKey: "SUP-30001",
  currentPrice: NumberDecimal("29.95"),
  currencyCode: "USD",
  active: true,
  createdAt: ISODate("2026-07-01T12:00:00.000Z"),
  updatedAt: ISODate("2026-07-02T14:30:00.000Z")
}
```

## 6. Lab 2 — Migrate Two Tables as Referenced Collections

This model keeps parent and history records independent. MongoDB does not enforce a foreign key; the retained `itemKey` is an application-level reference.

### 6.1 Initial mapping

1. Select both Oracle tables.
2. Keep both as top-level collections.
3. Map `PRODUCT_CATALOG_ITEM` as **New documents** in `catalogItems`.
4. Map `PRODUCT_PRICE_HISTORY` as **New documents** in `priceHistoryEvents`.

Use the Lab 1 field mapping for `catalogItems`. For `priceHistoryEvents`, use:

| Source column | MongoDB field | Treatment |
|---|---|---|
| `PRICE_EVENT_KEY` | `priceEventId` | Retain; candidate child identifier |
| `ITEM_KEY` | `itemKey` | Retain; required reference to the parent |
| `PREVIOUS_PRICE` | `previousPrice` | Retain |
| `NEW_PRICE` | `newPrice` | Retain |
| `CURRENCY_CODE` | `currencyCode` | Retain |
| `CHANGE_REASON` | `changeReason` | Retain |
| `CHANGE_ACTION` | `changeAction` | Retain |
| `EFFECTIVE_AT` | `effectiveAt` | Retain |
| `RECORDED_AT` | `recordedAt` | Retain |

If `PRICE_EVENT_KEY` is a declared primary key, it can become the child `_id`. Otherwise, keep the generated `ObjectId` and retain `priceEventId`.

Expected shapes:

```javascript
// catalogItems
{
  _id: ObjectId("..."),
  itemKey: "ITEM-10001",
  sku: "SKU-20001",
  productName: "Example Product",
  currentPrice: NumberDecimal("29.95")
}

// priceHistoryEvents
{
  _id: ObjectId("..."),
  priceEventId: 501,
  itemKey: "ITEM-10001",
  previousPrice: NumberDecimal("24.95"),
  newPrice: NumberDecimal("29.95"),
  changeAction: "INCREASE",
  recordedAt: ISODate("2026-07-02T14:30:00.000Z")
}
```

### 6.2 Add reference indexes

After confirming uniqueness and data quality, create:

```javascript
db.catalogItems.createIndex(
  { itemKey: 1 },
  { unique: true, name: "uq_itemKey" }
)

db.priceHistoryEvents.createIndex(
  { itemKey: 1, recordedAt: 1 },
  { name: "ix_itemKey_recordedAt" }
)
```

The application can query the two collections separately or join them with `$lookup`. Treat the reference as an application contract because MongoDB will not reject a child whose `itemKey` has no matching parent.

## 7. Lab 3 — Embed the Related Table

This model creates one `catalogItems` collection and embeds matching history records in a `priceHistory` array.

### 7.1 Confirm the relationship is available

An embedded-array mapping is enabled only when Relational Migrator recognizes the history table as the many side of a usable relationship and the parent is mapped to a collection.

If **Embedded array** is disabled:

1. Cancel the new-document mapping.
2. Refresh the relational schema after correcting Oracle metadata permissions.
3. Confirm that a relationship line appears between the tables.
4. If the source relationship remains unavailable, add a synthetic one-to-many foreign key:

```text
Parent table:  PRODUCT_CATALOG_ITEM
Parent field:  ITEM_KEY
Child table:   PRODUCT_PRICE_HISTORY
Child field:   ITEM_KEY
Cardinality:   One-to-many
```

Prefer the real Oracle constraint when it can be imported. Use a synthetic relationship only to represent a verified logical relationship that Relational Migrator cannot discover.

### 7.2 Configure the mappings

Map `PRODUCT_CATALOG_ITEM` as **New documents** in `catalogItems`, using the Lab 1 parent fields. Select `PRODUCT_PRICE_HISTORY`, click **+ Add**, and configure:

```text
Migrate table as: Embedded array
Parent collection: catalogItems
Prefix: (root)
Field name: priceHistory
Foreign-key link: ITEM_KEY relationship
```

Use `priceHistory`, not an autogenerated name that repeats the full table or collection name.

### 7.3 Embedded field treatment

| Source column | MongoDB field | Treatment |
|---|---|---|
| generated embedded `_id` | — | Exclude when `priceEventId` is retained |
| `PRICE_EVENT_KEY` | `priceEventId` | Retain |
| `ITEM_KEY` | — | Exclude; the parent already provides the relationship |
| `PREVIOUS_PRICE` | `previousPrice` | Retain as a historical snapshot |
| `NEW_PRICE` | `newPrice` | Retain as a historical snapshot |
| `CURRENCY_CODE` | `currencyCode` | Retain |
| `CHANGE_REASON` | `changeReason` | Retain |
| `CHANGE_ACTION` | `changeAction` | Retain |
| `EFFECTIVE_AT` | `effectiveAt` | Retain |
| `RECORDED_AT` | `recordedAt` | Retain |

Repeated price and currency fields should remain when they represent event-time state. Remove them only after the application owner confirms they are redundant.

### 7.4 Sort the embedded array

In the history mapping:

1. Expand **Advanced settings**.
2. Leave **Add mapping rule filter** unchecked unless a real filtering requirement exists.
3. Select **Add array conditions**.
4. Configure:

```text
Sort by: RECORDED_AT
Order: Ascending
Limit: No limit
```

Keep `RECORDED_AT` included in the mapping; an excluded field cannot be used for array sorting.

### 7.5 Handle Oracle `TIMESTAMP(6)`

MongoDB BSON Date stores millisecond precision, while Oracle `TIMESTAMP(6)` can store microseconds. Mapping to BSON Date may lose the final three fractional-second digits.

Use BSON Date when millisecond precision is sufficient and add this note:

```text
Oracle TIMESTAMP(6) has microsecond precision. BSON Date preserves
millisecond precision; sub-millisecond digits may be truncated.
Use priceEventId as a secondary ordering key.
```

If exact microsecond fidelity is required, use a supported String or Long conversion strategy and document how the application will query and compare it.

Expected embedded shape:

```javascript
{
  _id: ObjectId("..."),
  itemKey: "ITEM-10001",
  sku: "SKU-20001",
  productName: "Example Product",
  currentPrice: NumberDecimal("29.95"),
  priceHistory: [
    {
      priceEventId: 501,
      previousPrice: NumberDecimal("24.95"),
      newPrice: NumberDecimal("29.95"),
      currencyCode: "USD",
      changeReason: "Annual price review",
      changeAction: "INCREASE",
      effectiveAt: ISODate("2026-07-02T00:00:00.000Z"),
      recordedAt: ISODate("2026-07-02T14:30:00.000Z")
    }
  ]
}
```

## 8. Review the Generated Model

Open **JSON Schema** for the selected lab and confirm:

- Lab 1 has one root collection and no relationship artifacts.
- Lab 2 has two root collections and retains `itemKey` in each child document.
- Lab 3 has one root collection, a `priceHistory` array, no redundant child `itemKey`, and no unnecessary generated embedded `_id`.
- Oracle numbers map to intentional BSON numeric types.
- Timestamps use the approved precision strategy.
- Null-handling choices match application requirements.
- Names follow the chosen casing convention.

The Lab 3 sample usually contains only one history element. It proves the shape, not the sort order; verify ordering after migrating a parent with multiple history rows.

## 9. Run the Snapshot Migration

### 9.1 Understand the prerequisite warning

The migration-job wizard may report:

> The source database is not configured for running snapshot migration jobs.

This means Relational Migrator detected missing Oracle configuration or privileges. A successful connection test does not override this warning.

Select **Generate script**, then:

1. Save the generated SQL script.
2. Review every statement.
3. Have the Oracle DBA approve and execute only the required statements using the appropriate privileged account.
4. Regenerate or rerun the prerequisite check.

Do not execute a generated database-configuration script blindly, especially against a shared or production Oracle database.

### 9.2 Recommended first-test options

```text
Mode: Snapshot
Drop destination collections: Yes, only for a disposable test database
Stop migration after: 1 error
Verify migrated data: Yes
```

The drop option deletes the existing destination collections before loading. Never use it against data that must be retained.

Snapshot jobs are non-idempotent by default and can insert duplicates when rerun. For repeatable disposable tests, start with an empty target or drop the test collection. Relational Migrator can enable idempotency through `user.properties`, but MongoDB warns that this can materially affect performance on large jobs.

### 9.3 Start and monitor

1. Review source and destination connection names.
2. Confirm the target database is the test database.
3. Confirm the selected collection and migration options.
4. Start the job.
5. Monitor the snapshot, transformation, write, cleanup, and verification stages.
6. Download the job log if any row or mapping fails.

For a Linux installation, the application log is:

```text
~/.mongodb/relational-migrator/migrator.log
```

## 10. Validate the Result

Built-in verification should be enabled, but also perform model-specific checks.

### 10.1 Lab 1 checks

The `catalogItems` count must equal the valid Oracle parent-row count:

```javascript
db.catalogItems.countDocuments()
```

Sample representative rows and compare identifiers, prices, null handling, timestamp interpretation, non-ASCII strings, and maximum-length strings.

### 10.2 Lab 2 checks

The two MongoDB counts must equal the corresponding valid Oracle row counts:

```javascript
db.catalogItems.countDocuments()
db.priceHistoryEvents.countDocuments()
```

Find child references that do not resolve to a parent:

```javascript
db.priceHistoryEvents.aggregate([
  {
    $lookup: {
      from: "catalogItems",
      localField: "itemKey",
      foreignField: "itemKey",
      as: "parent"
    }
  },
  { $match: { parent: { $eq: [] } } },
  { $count: "orphanReferences" }
])
```

The expected orphan count is zero unless the source analysis identified and approved exceptions. Confirm the parent and child indexes from Section 6.2 are present.

### 10.3 Lab 3 checks

The root-document count must equal the valid parent-row count. The total number of embedded elements must equal the valid, joined child-row count:

```javascript
db.catalogItems.countDocuments()

db.catalogItems.aggregate([
  {
    $project: {
      historyCount: { $size: { $ifNull: ["$priceHistory", []] } }
    }
  },
  {
    $group: {
      _id: null,
      totalHistoryRows: { $sum: "$historyCount" }
    }
  }
])
```

Inspect parents with multiple history entries:

```javascript
db.catalogItems.find(
  { "priceHistory.1": { $exists: true } },
  { itemKey: 1, priceHistory: 1 }
).limit(10)
```

If timestamp values can collide after microsecond-to-millisecond conversion, use `priceEventId` as a deterministic secondary ordering key in application logic.

### 10.4 Compare all three results

For the same sample parent, compare:

- Lab 1: a single independent parent document
- Lab 2: a parent document plus independently queryable child documents
- Lab 3: a parent document containing an ordered child array

Document which design best matches the intended queries, writes, retention, and ownership. The exercise is complete only when the model choice is explained, not merely when the row counts match.

For Labs 1 and 3, add the parent business-key index after confirming uniqueness:

```javascript
db.catalogItems.createIndex(
  { itemKey: 1 },
  { unique: true, name: "uq_itemKey" }
)
```

Create other indexes from verified application query patterns, not solely from the indexes that existed in Oracle.

## 11. Snapshot Versus CDC

### Snapshot

A snapshot is a bounded, one-time migration of source data. It does not continue applying Oracle inserts, updates, and deletes after the snapshot boundary.

Snapshot is appropriate for:

- Modeling and test migrations
- One-time loads
- Cutovers with an approved write freeze
- Migrations with a separately engineered delta process

### Why Continuous/CDC is disabled

The screen label is **MongoDB AMP**, not APM.

**AMP** means **Application Modernization Platform**. It combines MongoDB modernization tooling, a delivery framework, and MongoDB delivery engineers. It is different from application performance monitoring, which is commonly abbreviated APM.

Beginning with Relational Migrator 1.15, released October 17, 2025, MongoDB moved Continuous Sync (CDC) out of the standalone Relational Migrator product. It is now available only as part of an AMP engagement. Therefore:

- The disabled Continuous option is not caused by the Oracle user.
- It is not caused by the MongoDB user's roles.
- It cannot be enabled through a local checkbox or normal `user.properties` setting.
- Upgrading the standalone tool does not unlock CDC.

An **AMP engagement** is a scoped modernization engagement with MongoDB's account and delivery teams. It is not simply a feature flag, community download, or separately documented self-service CDC plug-in. MongoDB publicly describes AMP as a combination of platform tooling, a delivery framework, and delivery engineers. The account team determines access, commercial scope, deployment components, and implementation responsibilities.

To pursue CDC through Relational Migrator:

1. Contact the organization's MongoDB account representative.
2. Request an **AMP assessment for Oracle-to-MongoDB Continuous Sync (CDC)**.
3. Provide the Oracle version and topology, data volume and change rate, downtime target, MongoDB target type, document mappings, and network/security constraints.
4. Confirm support for the target deployment, including self-managed MongoDB where applicable.
5. Obtain the AMP-specific tooling/access, deployment plan, Oracle logging and privilege requirements, monitoring, recovery, validation, and cutover procedure.
6. Test CDC correctness for embedded arrays before production cutover.

For regulated or isolated environments, confirm early whether AMP delivery and connectivity satisfy organizational requirements.

### If AMP is not available

Choose an explicit alternative:

- Controlled application write freeze, final snapshot, validation, and cutover
- Oracle-aware CDC through an approved product such as Oracle GoldenGate
- Debezium Oracle plus Kafka and an engineered MongoDB sink or consumer
- AWS Database Migration Service when available and approved
- A custom timestamp/sequence-based delta process when deletes and transaction ordering are not required

AWS Glue JDBC bookmarks are incremental batch processing, not complete Oracle redo-log CDC. They do not automatically capture arbitrary updates, deletes, or transaction order.

## 12. Errors and Warnings Encountered in This Workflow

| Symptom | Meaning | Response |
|---|---|---|
| Connection test succeeds; Pre-Migration Analysis fails unexpectedly | Basic table access works, but metadata access, connector support, or preview analysis fails | Inspect `migrator.log`; verify Oracle connector and catalog access; continue with manual analysis if necessary |
| Embedded array option is disabled | Relational Migrator does not recognize an eligible one-to-many relationship | Refresh schema after permissions; import relationship metadata or add a verified synthetic foreign key |
| `TIMESTAMP(6)` to BSON Date truncation warning | Oracle microseconds exceed BSON Date millisecond precision | Accept and document, or map to a full-precision String/Long representation |
| Snapshot source-configuration warning | Required Oracle privileges or configuration are missing | Generate the SQL script and have the Oracle DBA review and apply approved statements |
| Continuous option is unavailable | Standalone Relational Migrator 1.15+ no longer includes CDC | Engage MongoDB AMP or select another approved CDC/cutover strategy |

## 13. Completion Checklist

- [ ] Lab scope selected: direct, reference, or embedded
- [ ] Parent and history ownership confirmed
- [ ] Parent key is unique and non-null
- [ ] Foreign key and orphan count reviewed
- [ ] Maximum history cardinality measured
- [ ] Document-size growth assessed
- [ ] Oracle migration account approved
- [ ] MongoDB migration writer approved
- [ ] Connections named and tagged by environment
- [ ] Lab 1 maps the parent table to one collection without relationship artifacts
- [ ] Lab 2 maps both tables to collections and retains the child `itemKey` reference
- [ ] Lab 2 reference indexes and orphan-reference validation completed
- [ ] Lab 3 maps the child as the `priceHistory` embedded array
- [ ] Lab 3 excludes the redundant embedded `_id` and parent join key
- [ ] Historical snapshot fields are retained intentionally
- [ ] Timestamp precision decision documented
- [ ] Lab 3 array sorted ascending with no unintended limit
- [ ] JSON Schema and sample document reviewed
- [ ] Generated Oracle prerequisite script reviewed by DBA
- [ ] First snapshot targets a disposable database
- [ ] Error threshold and built-in verification enabled
- [ ] Lab-specific counts, values, references or array ordering, and nulls reconciled
- [ ] Reference-versus-embedding decision recorded using access patterns and growth
- [ ] CDC/AMP or controlled-cutover strategy documented
- [ ] Project export, logs, and validation evidence retained

## Official References

- [Relational Migrator overview](https://www.mongodb.com/docs/relational-migrator/getting-started/)
- [Pre-Migration Analysis](https://www.mongodb.com/docs/relational-migrator/app-analysis/)
- [Run Pre-Migration Analysis](https://www.mongodb.com/docs/relational-migrator/app-analysis/run-analysis/)
- [Manage the relational model](https://www.mongodb.com/docs/relational-migrator/projects/manage-relational-connection/)
- [Project settings and key handling](https://www.mongodb.com/docs/relational-migrator/projects/configure-settings/)
- [Embedded array mapping](https://www.mongodb.com/docs/relational-migrator/mapping-rules/mapping-rule-options/embedded-array/)
- [Synthetic foreign keys](https://www.mongodb.com/docs/relational-migrator/mapping-rules/synthetic-foreign-key/add-foreign-key/)
- [Create a migration job](https://www.mongodb.com/docs/relational-migrator/jobs/creating-jobs/)
- [Data migration behavior](https://www.mongodb.com/docs/relational-migrator/jobs/sync-jobs/)
- [Data verification](https://www.mongodb.com/docs/relational-migrator/jobs/data-verification/)
- [Oracle migration prerequisites](https://www.mongodb.com/docs/relational-migrator/jobs/prerequisites/oracle/)
- [Manage saved connections](https://www.mongodb.com/docs/relational-migrator/database-connections/manage-database-connections/)
- [Relational Migrator release notes](https://www.mongodb.com/docs/relational-migrator/release-notes/)
- [MongoDB Application Modernization Platform](https://www.mongodb.com/products/updates/mongodb-application-modernization-platform-amp-now-available/)

## Disclaimer

This is a sanitized teaching example. It is not a production migration authorization, security standard, or substitute for application-owner, Oracle DBA, MongoDB DBA, architecture, and change-management approval.
