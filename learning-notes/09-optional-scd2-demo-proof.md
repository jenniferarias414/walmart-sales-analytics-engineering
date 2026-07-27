# Optional SCD2 Demo Proof

## Purpose

The official fact table uses SCD2-style versioning, but the project only has one source batch.

Because of that, the official fact table has:

```text
421,570 current rows
0 historical rows
```

That is expected for the first observed version of the data.

This optional demo proves what would happen when a later batch changes a tracked value for an existing business key.

## Demo flow

```text
int_walmart_sales_enriched
    ↓
demo_walmart_fact_snapshot
```

The demo snapshot does not feed the official fact table.

It is only a proof artifact.

## Business key

The same logical business key is used:

```text
store_id + dept_id + date_id
```

This represents one weekly department sales record for one store and one date.

## How the demo works

The demo snapshot uses a dbt variable:

```text
demo_adjust_weekly_sales
```

First run:

```bash
dbt snapshot --select demo_walmart_fact_snapshot
```

Second run:

```bash
dbt snapshot --select demo_walmart_fact_snapshot --vars '{"demo_adjust_weekly_sales": true}'
```

The second run adjusts one controlled row:

```text
store_id = 1
dept_id  = 1
date_id  = 20100205
```

The changed field is:

```text
store_weekly_sales
```

Because `store_weekly_sales` is included in the snapshot's check columns, dbt detects the change.

## Expected result

After the second run, the demo snapshot should show:

```text
total rows       421,571
current rows     421,570
historical rows  1
```

The changed business key should have two versions:

```text
old version:
dbt_valid_to is populated

new version:
dbt_valid_to is null
```

## Why this matters

The official fact table has no historical rows because there has only been one source batch.

The demo proves the versioning behavior without changing:

```text
raw source data
official fact snapshot
official fact table
official reporting outputs
```

## Completed evidence

The SCD2 demo proof is shown here:

![SCD2 demo versioning proof](../screenshots/full-walkthrough/23-scd2-demo-versioning-proof.png)

## Main takeaway

SCD2 history appears when the same business key arrives again with a changed tracked value.

The snapshot does not create history just because it runs again.

It creates history when a tracked column changes for an existing key.
