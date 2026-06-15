
# Walmart Source-to-Target Mapping

## Purpose

This document maps the supplied Walmart CSV fields to the raw, staging, dimensional, and fact models used by the project.

The mapping was created after source-data profiling confirmed the grain, candidate keys, null patterns, date coverage, and relationships among the source files.

## Source Files

| Source           | Grain                                   | Candidate Key         | Primary Purpose                                             |
| ---------------- | --------------------------------------- | --------------------- | ----------------------------------------------------------- |
| `stores.csv`     | One row per store                       | `Store`               | Store type and size attributes                              |
| `department.csv` | One row per store, department, and date | `Store + Dept + Date` | Weekly department sales                                     |
| `fact.csv`       | One row per store and date              | `Store + Date`        | Store/date economic, promotional, and environmental context |

## Source Interpretation

Despite its name, `fact.csv` is not the primary weekly-sales source.

The source responsibilities are:

```text
department.csv = weekly department sales
fact.csv       = store/date contextual features
stores.csv     = store attributes
```

The final fact model is driven by `department.csv` because it contains `Weekly_Sales` and establishes the required Store + Department + Date grain.

## Raw Snowflake Tables

| Source File      | Raw Table                      |
| ---------------- | ------------------------------ |
| `stores.csv`     | `raw_walmart_stores`           |
| `department.csv` | `raw_walmart_department_sales` |
| `fact.csv`       | `raw_walmart_store_features`   |

The raw layer preserves source data for audit, troubleshooting, and reprocessing.

## dbt Staging Models

| Raw Table                      | Staging Model                  | Grain                                   |
| ------------------------------ | ------------------------------ | --------------------------------------- |
| `raw_walmart_stores`           | `stg_walmart_stores`           | One row per store                       |
| `raw_walmart_department_sales` | `stg_walmart_department_sales` | One row per store, department, and date |
| `raw_walmart_store_features`   | `stg_walmart_store_features`   | One row per store and date              |

## Staging Mapping: Stores

| Target Column | Source Column | Transformation           |
| ------------- | ------------- | ------------------------ |
| `store_id`    | `Store`       | Cast to integer          |
| `store_type`  | `Type`        | Trim and cast to varchar |
| `store_size`  | `Size`        | Cast to integer          |

## Staging Mapping: Department Sales

| Target Column        | Source Column  | Transformation         |
| -------------------- | -------------- | ---------------------- |
| `store_id`           | `Store`        | Cast to integer        |
| `dept_id`            | `Dept`         | Cast to integer        |
| `store_date`         | `Date`         | Parse and cast to date |
| `store_weekly_sales` | `Weekly_Sales` | Cast to decimal        |
| `is_holiday`         | `IsHoliday`    | Cast to boolean        |

## Staging Mapping: Store Features

| Target Column       | Source Column  | Transformation                 |
| ------------------- | -------------- | ------------------------------ |
| `store_id`          | `Store`        | Cast to integer                |
| `store_date`        | `Date`         | Parse and cast to date         |
| `store_temperature` | `Temperature`  | Cast to decimal                |
| `fuel_price`        | `Fuel_Price`   | Cast to decimal                |
| `markdown1`         | `MarkDown1`    | Cast to decimal; preserve null |
| `markdown2`         | `MarkDown2`    | Cast to decimal; preserve null |
| `markdown3`         | `MarkDown3`    | Cast to decimal; preserve null |
| `markdown4`         | `MarkDown4`    | Cast to decimal; preserve null |
| `markdown5`         | `MarkDown5`    | Cast to decimal; preserve null |
| `cpi`               | `CPI`          | Cast to decimal; preserve null |
| `unemployment`      | `Unemployment` | Cast to decimal; preserve null |
| `is_holiday`        | `IsHoliday`    | Cast to boolean                |

## Final Dimension: walmart_date_dim

### Grain

```text
One row per date
```

### Business Key

```text
date_id
```

### SCD Behavior

SCD Type 1.

| Target Column | Source / Derivation        | Rule                                 |
| ------------- | -------------------------- | ------------------------------------ |
| `date_id`     | `department.Date`          | Convert date to integer `YYYYMMDD`   |
| `store_date`  | `department.Date`          | Distinct parsed date                 |
| `is_holiday`  | `department.IsHoliday`     | One consistent value per date        |
| `insert_date` | System-generated timestamp | Set when row is inserted             |
| `update_date` | System-generated timestamp | Set when row is processed or updated |

Example:

```text
2010-02-05 → 20100205
```

## Final Dimension: walmart_store_dim

### Grain

```text
One row per store and department combination
```

### Composite Business Key

```text
store_id + dept_id
```

### SCD Behavior

SCD Type 1.

| Target Column | Source / Derivation        | Rule                                  |
| ------------- | -------------------------- | ------------------------------------- |
| `store_id`    | `department.Store`         | Existing source store identifier      |
| `dept_id`     | `department.Dept`          | Existing source department identifier |
| `store_type`  | `stores.Type`              | Join using Store                      |
| `store_size`  | `stores.Size`              | Join using Store                      |
| `insert_date` | System-generated timestamp | Set when row is inserted              |
| `update_date` | System-generated timestamp | Set when row is processed or updated  |

The dimension is created using:

```text
Distinct Store + Dept from department.csv
        LEFT JOIN stores.csv
        ON Store
```

`Dept` already acts as the department identifier. No row number is required to create `dept_id`.

## Final Fact: walmart_fact_table

### Grain

```text
One version of one Store + Department + Date weekly-sales record
```

### Composite Business Key

```text
store_id + dept_id + date_id
```

The three foreign-key columns together identify the same logical fact record across versions.

### SCD Behavior

SCD Type 2-style versioning, as required by the supplied project guide.

If a tracked value changes for the same:

```text
store_id + dept_id + date_id
```

then:

1. The existing version is end-dated.
2. The old version remains available.
3. A new current version is inserted.
4. The current version has a null `vrsn_end_date`.

The effective uniqueness of a historical version is:

```text
store_id + dept_id + date_id + vrsn_start_date
```

The final table does not require an additional visible surrogate-key column because one is not included in the supplied project guide.

## Final Fact Mapping

| Target Column        | Source / Derivation        | Rule                                          |
| -------------------- | -------------------------- | --------------------------------------------- |
| `store_id`           | `department.Store`         | Foreign-key component                         |
| `dept_id`            | `department.Dept`          | Foreign-key component                         |
| `date_id`            | `department.Date`          | Convert to integer `YYYYMMDD`                 |
| `store_size`         | `stores.Size`              | Join on Store; retained to match guide        |
| `store_weekly_sales` | `department.Weekly_Sales`  | Decimal sales measure                         |
| `fuel_price`         | `fact.Fuel_Price`          | Join on Store + Date                          |
| `store_temperature`  | `fact.Temperature`         | Join on Store + Date                          |
| `unemployment`       | `fact.Unemployment`        | Join on Store + Date                          |
| `cpi`                | `fact.CPI`                 | Join on Store + Date                          |
| `markdown1`          | `fact.MarkDown1`           | Preserve null                                 |
| `markdown2`          | `fact.MarkDown2`           | Preserve null                                 |
| `markdown3`          | `fact.MarkDown3`           | Preserve null                                 |
| `markdown4`          | `fact.MarkDown4`           | Preserve null                                 |
| `markdown5`          | `fact.MarkDown5`           | Preserve null                                 |
| `vrsn_start_date`    | dbt snapshot metadata      | Timestamp version became valid                |
| `vrsn_end_date`      | dbt snapshot metadata      | Timestamp version ended; null means current   |
| `insert_date`        | System-generated timestamp | Timestamp version was inserted                |
| `update_date`        | System-generated timestamp | Timestamp version was most recently processed |

## Fact-Model Join

The fact model begins with the weekly-sales source:

```text
department sales
    LEFT JOIN store/date features
        ON Store + Date
    LEFT JOIN store attributes
        ON Store
```

The weekly-sales source remains authoritative.

A left join preserves all weekly-sales records even if optional context data is unavailable.

## Internal dbt Snapshot Helper

A dbt snapshot requires a unique identifier for the logical incoming record.

The intermediate model may derive an internal helper from:

```text
store_id + dept_id + date_id
```

That helper supports dbt snapshot processing but is not exposed in the final project-guide table.

dbt metadata is mapped as:

```text
dbt_valid_from → vrsn_start_date
dbt_valid_to   → vrsn_end_date
```

## Join Validation

Profiling confirmed:

* all department-sales Store + Date keys have matching feature records;
* the department-to-feature relationship is many-to-one;
* the department-to-store relationship is many-to-one;
* the context join preserves all 421,570 sales rows;
* the context join does not multiply the sales grain;
* holiday values agree between the sales and feature sources.

## Null-Handling Decisions

### Raw and Staging Layers

Preserve null values.

### Markdown Fields

Preserve warehouse nulls.

A report may use:

```sql
COALESCE(markdown1, 0)
```

when a specific calculation interprets missing markdown activity as zero.

### CPI and Unemployment

The complete store-feature source includes later dates with null CPI and unemployment values.

The final sales join will be validated to determine whether these nulls affect the sales date range.

### Negative and Zero Weekly Sales

Preserve negative and zero sales until a valid business rule identifies them as invalid.

They may represent:

* returns;
* adjustments;
* corrections;
* weeks with zero net sales.

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

