# Intermediate Enriched Sales Model

## Purpose

After creating source-aligned staging models, I built an intermediate model that joins the cleaned Walmart sources together.

This model prepares the sales data for the final dimension and fact tables.

## Flow

```text
stg_walmart_department_sales
stg_walmart_store_features
stg_walmart_stores
    ↓
int_walmart_sales_enriched
```

## Why use an intermediate model?

The intermediate layer keeps reusable transformation logic between staging and final marts.

Instead of repeating the same joins in multiple final models, I join the cleaned staging data once in:

```text
int_walmart_sales_enriched
```

The final dimension and fact models can then build from this prepared dataset.

## Driving source

The driving source is:

```text
stg_walmart_department_sales
```

This is the source that contains:

```text
store_weekly_sales
```

It also defines the grain of the enriched sales model:

```text
one row per store, department, and date
```

## Join design

The join pattern is:

```text
department sales
    LEFT JOIN store/date features
        ON store_id + store_date

    LEFT JOIN store attributes
        ON store_id
```

Plain English:

```text
Keep every weekly department-sales row.
Add store/date context.
Add store attributes.
```

## Fields added

The intermediate model adds:

```text
date_id
store_type
store_size
store_temperature
fuel_price
markdown1-5
cpi
unemployment
```

The `date_id` is generated from the date:

```text
2010-02-05 -> 20100205
```

This key will be reused by the date dimension and fact table.

## Validation

I validated the intermediate model in two ways.

### Row-count validation

The row count from the driving staging model matched the intermediate model:

| Model | Row Count |
|---|---:|
| `STG_WALMART_DEPARTMENT_SALES` | 421,570 |
| `INT_WALMART_SALES_ENRICHED` | 421,570 |

This confirms that the joins did not lose or multiply sales rows.

### Missing-join validation

I also checked important joined fields for missing values using `COUNT_IF`.

`COUNT_IF(condition)` counts rows where the condition is true.

Example:

```sql
COUNT_IF(store_type IS NULL) AS missing_store_attributes
```

The missing-join checks returned zero for important store and context fields, which confirmed the expected matches were present.

Markdown fields were not treated as join failures because markdown nulls already existed in the source and are intentionally preserved.

## Completed evidence

The dbt intermediate build completed successfully:

![dbt intermediate build success](../screenshots/full-walkthrough/13-dbt-intermediate-build-success.png)

The Snowflake row-count validation confirmed the intermediate model preserved the sales grain:

![Snowflake intermediate validation](../screenshots/full-walkthrough/14-snowflake-intermediate-validation.png)

The dbt docs lineage shows the three staging models feeding the intermediate model:

![dbt docs intermediate lineage](../screenshots/full-walkthrough/15-dbt-docs-intermediate-lineage.png)

## Main takeaway

This phase is where the cleaned sources come together.

The important distinction is:

```text
STAGING:
Clean one source at a time.

INTERMEDIATE:
Join cleaned sources into reusable prepared data.

MARTS:
Build final dimensions and facts for reporting.
```

Next, the project moves into final mart models.
