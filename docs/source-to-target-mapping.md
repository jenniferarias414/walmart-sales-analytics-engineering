# Walmart Source-to-Target Mapping

## Purpose

This document maps the supplied Walmart CSV fields to the raw, staging, dimensional, and fact models used by the project.

The mapping was created after source-data profiling confirmed the grain, candidate keys, null patterns, date coverage, and relationships among the three source files.

## Source Files

| Source | Grain | Candidate Key | Primary Purpose |
|---|---|---|---|
| `stores.csv` | One row per store | `Store` | Store type and size attributes |
| `department.csv` | One row per store, department, and date | `Store + Dept + Date` | Weekly department sales |
| `fact.csv` | One row per store and date | `Store + Date` | Store/date economic, promotional, and environmental context |

## Source Interpretation

Despite its name, `fact.csv` is not the primary sales source.

The source responsibilities are:

```text
department.csv = weekly department sales
fact.csv       = store/date contextual features
stores.csv     = store attributes
```

The final sales model is driven by `department.csv` because it contains the business measure `Weekly_Sales` and establishes the required `Store + Dept + Date` grain.

## Raw Snowflake Tables

The files will first be loaded into Snowflake without applying business transformations.

| Source File | Raw Table |
|---|---|
| `stores.csv` | `raw_walmart_stores` |
| `department.csv` | `raw_walmart_department_sales` |
| `fact.csv` | `raw_walmart_store_features` |

The raw layer preserves the source structure so the original data can be audited and reprocessed.

## dbt Staging Models

The staging layer will standardize column names, cast data types, and preserve source meaning.

| Raw Table | Staging Model | Grain |
|---|---|---|
| `raw_walmart_stores` | `stg_walmart_stores` | One row per store |
| `raw_walmart_department_sales` | `stg_walmart_department_sales` | One row per store, department, and date |
| `raw_walmart_store_features` | `stg_walmart_store_features` | One row per store and date |

## Staging Transformations

### `stg_walmart_stores`

| Target Column | Source Column | Transformation |
|---|---|---|
| `store_id` | `Store` | Cast to integer |
| `store_type` | `Type` | Trim and cast to varchar |
| `store_size` | `Size` | Cast to integer |

### `stg_walmart_department_sales`

| Target Column | Source Column | Transformation |
|---|---|---|
| `store_id` | `Store` | Cast to integer |
| `dept_id` | `Dept` | Cast to integer |
| `store_date` | `Date` | Parse and cast to date |
| `store_weekly_sales` | `Weekly_Sales` | Cast to decimal |
| `is_holiday` | `IsHoliday` | Cast to boolean |

### `stg_walmart_store_features`

| Target Column | Source Column | Transformation |
|---|---|---|
| `store_id` | `Store` | Cast to integer |
| `store_date` | `Date` | Parse and cast to date |
| `store_temperature` | `Temperature` | Cast to decimal |
| `fuel_price` | `Fuel_Price` | Cast to decimal |
| `markdown1` | `MarkDown1` | Cast to decimal; preserve null |
| `markdown2` | `MarkDown2` | Cast to decimal; preserve null |
| `markdown3` | `MarkDown3` | Cast to decimal; preserve null |
| `markdown4` | `MarkDown4` | Cast to decimal; preserve null |
| `markdown5` | `MarkDown5` | Cast to decimal; preserve null |
| `cpi` | `CPI` | Cast to decimal; preserve null |
| `unemployment` | `Unemployment` | Cast to decimal; preserve null |
| `is_holiday` | `IsHoliday` | Cast to boolean |

## Final Dimension: `walmart_date_dim`

### Grain

One row per calendar date.

### SCD Behavior

SCD Type 1.

The final record stores the current value for the date attributes. No historical versions of the date record are retained.

| Target Column | Source / Derivation | Rule |
|---|---|---|
| `date_id` | `store_date` | Convert date to integer `YYYYMMDD` |
| `store_date` | `department.Date` | Distinct parsed date |
| `is_holiday` | `department.IsHoliday` | One consistent value per date |
| `insert_date` | System generated | Timestamp when row is first inserted |
| `update_date` | System generated | Timestamp when row is last updated |

Example:

```text
2010-02-05 → 20100205
```

The `YYYYMMDD` integer key is deterministic, readable, and stable if older dates are added later.

## Final Dimension: `walmart_store_dim`

### Grain

One row per store and department combination.

### Business Key

```text
Store_id + Dept_id
```

### SCD Behavior

SCD Type 1.

If store attributes change for an existing store/department combination, the previous values are overwritten.

| Target Column | Source / Derivation | Rule |
|---|---|---|
| `store_id` | `department.Store` | Existing store identifier |
| `dept_id` | `department.Dept` | Existing department identifier |
| `store_type` | `stores.Type` | Join on `Store` |
| `store_size` | `stores.Size` | Join on `Store` |
| `insert_date` | System generated | Timestamp when row is first inserted |
| `update_date` | System generated | Timestamp when row is last updated |

The source files are joined as:

```text
Distinct Store + Dept from department.csv
        LEFT JOIN stores.csv
        ON Store
```

`Dept` is already the department identifier. A row number is not required to create `dept_id`.

## Final Fact: `walmart_fact_table`

### Grain

One row per:

```text
Store + Department + Date + Version
```

### Business Key

The record being versioned is identified by:

```text
Store_id + Dept_id + Date_id
```

A technical hash key may also be created from these three values for dbt snapshot processing.

### SCD Behavior

SCD Type 2-style versioning, as required by the project specification.

If a tracked measure changes for the same `Store_id + Dept_id + Date_id` business key:

1. The existing current version is end-dated.
2. A new current version is inserted.
3. Both versions remain available for historical comparison.

| Target Column | Source / Derivation | Rule |
|---|---|---|
| `store_id` | `department.Store` | Integer |
| `dept_id` | `department.Dept` | Integer |
| `date_id` | `department.Date` | Convert to `YYYYMMDD` integer |
| `store_size` | `stores.Size` | Join through store; retained to match supplied target specification |
| `store_weekly_sales` | `department.Weekly_Sales` | Decimal |
| `fuel_price` | `fact.Fuel_Price` | Join on Store + Date |
| `store_temperature` | `fact.Temperature` | Join on Store + Date |
| `unemployment` | `fact.Unemployment` | Join on Store + Date |
| `cpi` | `fact.CPI` | Join on Store + Date |
| `markdown1` | `fact.MarkDown1` | Preserve null in modeled table |
| `markdown2` | `fact.MarkDown2` | Preserve null in modeled table |
| `markdown3` | `fact.MarkDown3` | Preserve null in modeled table |
| `markdown4` | `fact.MarkDown4` | Preserve null in modeled table |
| `markdown5` | `fact.MarkDown5` | Preserve null in modeled table |
| `insert_date` | System generated | Initial version insertion timestamp |
| `update_date` | System generated | Most recent processing timestamp |
| `vrsn_start_date` | dbt snapshot metadata | Timestamp version became valid |
| `vrsn_end_date` | dbt snapshot metadata | Timestamp version ended; null means current |

## Fact-Model Join

The fact model begins with `department.csv` and enriches it with the other sources:

```text
department sales
    LEFT JOIN store/date features
        ON Store + Date
    LEFT JOIN store attributes
        ON Store
```

A left join is used because the weekly sales records are authoritative.

The rule is:

> Preserve every weekly sales record, even if optional contextual data is missing.

## Join Validation

Profiling confirmed:

- All department sales `Store + Date` keys have matching feature records.
- The department-to-feature relationship is many-to-one.
- The department-to-store relationship is many-to-one.
- The context join preserves all 421,570 sales rows.
- The join does not multiply the expected sales grain.
- Holiday flags agree between the two source files.

## Null-Handling Decisions

### Raw and Staging Layers

Nulls are preserved.

This avoids silently inventing values before business meaning is established.

### Markdown Fields

Markdown nulls remain null in the warehouse model.

Reports may use:

```sql
COALESCE(markdown1, 0)
```

when the specific calculation treats missing markdown activity as zero.

### CPI and Unemployment

The full `fact.csv` source contains null CPI and unemployment values in later dates. Those later dates do not have matching department sales records in the supplied data.

The joined sales dataset should still be explicitly validated for null CPI and unemployment before final publication.

### Negative and Zero Weekly Sales

Negative and zero weekly sales are preserved.

They may represent:

- returns;
- adjustments;
- corrections;
- weeks with no net sales.

They should not be removed without a business rule.

## Source-to-Target Summary

```text
stores.csv
    → raw_walmart_stores
    → stg_walmart_stores
    → walmart_store_dim
    → walmart_fact_table enrichment

department.csv
    → raw_walmart_department_sales
    → stg_walmart_department_sales
    → walmart_date_dim
    → walmart_store_dim
    → walmart_fact_table

fact.csv
    → raw_walmart_store_features
    → stg_walmart_store_features
    → walmart_fact_table
```
