# Final Project Summary

## Project

Walmart Sales Analytics Engineering

## Summary

This project built an end-to-end analytics engineering workflow for Walmart weekly sales data.

The workflow starts with local CSV source files, ingests them to Amazon S3, loads them into Snowflake raw tables, transforms them with dbt Core, validates the modeled data, and generates reporting outputs from the final mart tables.

## Architecture diagram

![Architecture overview](../screenshots/full-walkthrough/00-architecture-overview.png)

The diagram shows the project flow from source profiling and S3 batch landing through Snowflake ingestion, dbt transformations, dimensional modeling, SCD handling, and Python reporting outputs.

## Pipeline

```text
Local CSV files
    ↓
Python S3 ingestion
    ↓
Snowflake raw tables
    ↓
dbt staging models
    ↓
dbt intermediate enriched model
    ↓
SCD1 dimensions and SCD2-style fact table
    ↓
Python reporting outputs
```

## Final mart tables

```text
WALMART_DATE_DIM
WALMART_STORE_DIM
WALMART_FACT_TABLE
```

## Key modeling decisions

- Raw Snowflake tables preserve the CSV delivery shape.
- dbt staging models clean names and apply intentional data types.
- The intermediate model joins cleaned sources once for reuse.
- Date and store dimensions are modeled as SCD Type 1.
- The fact table is modeled with SCD2-style versioning using a dbt snapshot.
- Reporting queries use only current fact records where `vrsn_end_date IS NULL`.

## Validation results

The project validates row counts, source grains, composite keys, join coverage, dimension uniqueness, fact table current-row uniqueness, and fact-to-dimension relationships.

Key results:

```text
department sales rows              421,570
intermediate enriched rows         421,570
date dimension rows                143
store dimension rows               3,331
fact table rows                    421,570
current fact rows                  421,570
missing date dimension matches     0
missing store dimension matches    0
```

## Reporting outputs

The reporting script generates CSV and PNG outputs for:

```text
monthly sales trend
sales by store type
holiday versus non-holiday sales
top store/department combinations
sales and markdowns by year
sales by temperature band
```

## Main takeaway

The project demonstrates an end-to-end analytics engineering workflow, with emphasis on reproducibility, data modeling, validation, and business-facing reporting.
