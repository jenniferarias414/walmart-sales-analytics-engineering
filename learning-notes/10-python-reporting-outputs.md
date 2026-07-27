# Python Reporting Outputs

## Purpose

After building the final mart tables, I created reporting outputs from Snowflake using Python.

This phase shows that the warehouse can support analysis, not just table creation.

## Reporting flow

```text
Snowflake marts
    ↓
Python reporting script
    ↓
CSV outputs and PNG charts
```

Final mart tables used:

```text
WALMART_FACT_TABLE
WALMART_DATE_DIM
WALMART_STORE_DIM
```

## Reports created

The reporting script creates outputs for:

```text
monthly sales trend
sales by store type
holiday versus non-holiday sales
top 10 store/department combinations
sales and markdowns by year
sales by temperature band
```

These reports were selected because they use the key fields modeled in the warehouse:

```text
weekly sales
dates
holidays
store type
store/department combinations
markdowns
temperature
```

## Why use Python?

Python makes the reporting step reproducible.

Instead of manually running each query and exporting each file, the script can:

```text
connect to Snowflake
run each SQL query
save results as CSV files
create charts
write a short reporting summary
```

## Script

The reporting script is:

```text
scripts/generate_walmart_reports.py
```

## SQL

The report SQL is also documented separately in:

```text
sql/09_reporting_queries.sql
```

This keeps the business queries visible even without reading the Python script.

## Environment variables

The script reads Snowflake connection settings from environment variables.

Required:

```text
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PASSWORD
```

Optional:

```text
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
SNOWFLAKE_SCHEMA
```

Using environment variables keeps credentials out of the public repo.

## Main Python libraries

### pandas

Used to hold query results in DataFrames and write CSV files.

### matplotlib

Used to create PNG charts.

### snowflake.connector

Used to connect from Python to Snowflake and run SQL queries.

### pathlib

Used for clean file path handling.

### os

Used to read environment variables.

## Output files

Generated outputs are saved under:

```text
reports/generated/
```

Examples:

```text
sales_by_month.csv
sales_by_month.png
sales_by_store_type.csv
sales_by_store_type.png
holiday_vs_nonholiday_sales.csv
holiday_vs_nonholiday_sales.png
top_10_store_departments.csv
top_10_store_departments.png
reporting_summary.md
```

## Completed evidence

The Python reporting script completed successfully:

![Python reporting script success](../screenshots/full-walkthrough/24-python-reporting-script-success.png)

The generated reporting files are shown here:

![Reporting outputs generated](../screenshots/full-walkthrough/25-reporting-outputs-generated.png)

Sample report chart:

![Sample report chart](../screenshots/full-walkthrough/26-sample-report-chart.png)

## Main takeaway

The reporting phase connects the engineering work back to business analysis.

The important distinction is:

```text
dbt models:
Build trusted mart tables.

Reporting SQL:
Ask business questions from the marts.

Python script:
Automate the query export and chart generation.
```
