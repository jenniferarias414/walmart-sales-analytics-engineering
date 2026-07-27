# Validation Queries

This file collects the main validation queries used throughout the Walmart Sales Analytics Engineering project.

The goal of these checks is to prove that each layer preserves the expected grain, row counts, joins, and business keys.

## Source profiling validation

The source files were profiled with:

```bash
python analysis/profile_source_data.py
```

Profile output:

```text
analysis/output/source-data-profile.md
```

Key expected counts from profiling:

```text
stores.csv                 45 rows
department.csv             421,570 rows
fact.csv / store features  8,190 rows
department sales dates     143 distinct sales dates
store + department combos  3,331 distinct combinations
```

## Snowflake raw load validation

Schema:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA RAW;
```

Raw row-count validation:

```sql
SELECT 'RAW_WALMART_STORES' AS table_name, COUNT(*) AS row_count
FROM RAW_WALMART_STORES
UNION ALL
SELECT 'RAW_WALMART_DEPARTMENT_SALES' AS table_name, COUNT(*) AS row_count
FROM RAW_WALMART_DEPARTMENT_SALES
UNION ALL
SELECT 'RAW_WALMART_STORE_FEATURES' AS table_name, COUNT(*) AS row_count
FROM RAW_WALMART_STORE_FEATURES;
```

Expected:

```text
RAW_WALMART_STORES              45
RAW_WALMART_DEPARTMENT_SALES    421,570
RAW_WALMART_STORE_FEATURES      8,190
```

## dbt connection validation

From the dbt project folder:

```bash
cd /Users/e189958/repos/DEA/walmart-sales-analytics-engineering/dbt/walmart_sales_analytics
dbt debug
```

Expected:

```text
All checks passed!
```

Source listing:

```bash
dbt ls --resource-type source
```

Expected sources:

```text
source:walmart_sales_analytics.walmart_raw.department_sales
source:walmart_sales_analytics.walmart_raw.store_features
source:walmart_sales_analytics.walmart_raw.stores
```

## dbt staging validation

Build staging models:

```bash
dbt build --select path:models/staging
```

Snowflake staging row-count validation:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA STAGING;

SELECT 'STG_WALMART_STORES' AS model_name, COUNT(*) AS row_count
FROM STG_WALMART_STORES
UNION ALL
SELECT 'STG_WALMART_DEPARTMENT_SALES' AS model_name, COUNT(*) AS row_count
FROM STG_WALMART_DEPARTMENT_SALES
UNION ALL
SELECT 'STG_WALMART_STORE_FEATURES' AS model_name, COUNT(*) AS row_count
FROM STG_WALMART_STORE_FEATURES;
```

Expected:

```text
STG_WALMART_STORES              45
STG_WALMART_DEPARTMENT_SALES    421,570
STG_WALMART_STORE_FEATURES      8,190
```

## Intermediate model validation

Build intermediate model:

```bash
dbt build --select int_walmart_sales_enriched
```

Row-count validation:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA STAGING;

SELECT 'STG_WALMART_DEPARTMENT_SALES' AS model_name, COUNT(*) AS row_count
FROM STG_WALMART_DEPARTMENT_SALES
UNION ALL
SELECT 'INT_WALMART_SALES_ENRICHED' AS model_name, COUNT(*) AS row_count
FROM INT_WALMART_SALES_ENRICHED;
```

Expected:

```text
STG_WALMART_DEPARTMENT_SALES    421,570
INT_WALMART_SALES_ENRICHED      421,570
```

Missing-join validation:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA STAGING;

SELECT
    COUNT_IF(store_type IS NULL) AS missing_store_attributes,
    COUNT_IF(store_temperature IS NULL) AS missing_store_features,
    COUNT_IF(fuel_price IS NULL) AS missing_fuel_price,
    COUNT_IF(cpi IS NULL) AS missing_cpi,
    COUNT_IF(unemployment IS NULL) AS missing_unemployment
FROM INT_WALMART_SALES_ENRICHED;
```

Expected:

```text
missing_store_attributes    0
missing_store_features      0
missing_fuel_price          0
missing_cpi                 0
missing_unemployment        0
```

Markdown fields were not checked as missing joins because markdown nulls existed in the source and were intentionally preserved.

## Dimension validation

Build dimension models:

```bash
dbt build --select walmart_date_dim walmart_store_dim
```

Dimension row-count validation:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA MARTS;

SELECT 'WALMART_DATE_DIM' AS table_name, COUNT(*) AS row_count
FROM WALMART_DATE_DIM
UNION ALL
SELECT 'WALMART_STORE_DIM' AS table_name, COUNT(*) AS row_count
FROM WALMART_STORE_DIM;
```

Expected:

```text
WALMART_DATE_DIM     143
WALMART_STORE_DIM    3,331
```

Date dimension uniqueness validation:

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT date_id) AS distinct_date_ids,
    COUNT(DISTINCT store_date) AS distinct_store_dates
FROM WALMART_DATE_DIM;
```

Expected:

```text
row_count = distinct_date_ids = distinct_store_dates = 143
```

Store dimension uniqueness validation:

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT store_id || '-' || dept_id) AS distinct_store_dept_keys
FROM WALMART_STORE_DIM;
```

Expected:

```text
row_count = distinct_store_dept_keys = 3,331
```

## SCD2-style fact validation

Run snapshot:

```bash
dbt snapshot --select walmart_fact_snapshot
```

Build final fact table:

```bash
dbt build --select walmart_fact_table
```

Snapshot and fact row-count validation:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA MARTS;

SELECT 'WALMART_FACT_SNAPSHOT' AS table_name, COUNT(*) AS row_count
FROM WALMART_FACT_SNAPSHOT
UNION ALL
SELECT 'WALMART_FACT_TABLE' AS table_name, COUNT(*) AS row_count
FROM WALMART_FACT_TABLE;
```

Expected first-run result:

```text
WALMART_FACT_SNAPSHOT    421,570
WALMART_FACT_TABLE       421,570
```

Current versus historical fact rows:

```sql
SELECT
    COUNT(*) AS total_fact_rows,
    COUNT_IF(vrsn_end_date IS NULL) AS current_fact_rows,
    COUNT_IF(vrsn_end_date IS NOT NULL) AS historical_fact_rows
FROM WALMART_FACT_TABLE;
```

Expected first-run result:

```text
total_fact_rows       421,570
current_fact_rows     421,570
historical_fact_rows  0
```

Current business-key uniqueness:

```sql
SELECT
    COUNT(*) AS current_fact_rows,
    COUNT(DISTINCT store_id || '-' || dept_id || '-' || date_id) AS distinct_current_business_keys
FROM WALMART_FACT_TABLE
WHERE vrsn_end_date IS NULL;
```

Expected first-run result:

```text
current_fact_rows = distinct_current_business_keys = 421,570
```

Dimension relationship coverage:

```sql
SELECT
    COUNT_IF(d.date_id IS NULL) AS missing_date_dim_matches,
    COUNT_IF(s.store_id IS NULL) AS missing_store_dim_matches
FROM WALMART_FACT_TABLE f
LEFT JOIN WALMART_DATE_DIM d
    ON f.date_id = d.date_id
LEFT JOIN WALMART_STORE_DIM s
    ON f.store_id = s.store_id
    AND f.dept_id = s.dept_id;
```

Expected:

```text
missing_date_dim_matches       0
missing_store_dim_matches      0
```

## dbt docs validation

Generate and serve documentation:

```bash
dbt docs generate
dbt docs serve
```

Useful screenshots:

```text
09-dbt-docs-source-lineage.png
12-dbt-docs-staging-lineage.png
15-dbt-docs-intermediate-lineage.png
18-dbt-docs-dimension-lineage.png
22-dbt-docs-fact-lineage.png
```

## Optional SCD2 demo validation

The optional demo snapshot proves SCD2 behavior without changing the official fact table.

Baseline run:

```bash
dbt snapshot --select demo_walmart_fact_snapshot
```

Simulated changed-batch run:

```bash
dbt snapshot --select demo_walmart_fact_snapshot --vars '{"demo_adjust_weekly_sales": true}'
```

Demo current/historical validation:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA MARTS;

SELECT
    COUNT(*) AS total_rows,
    COUNT_IF(dbt_valid_to IS NULL) AS current_rows,
    COUNT_IF(dbt_valid_to IS NOT NULL) AS historical_rows
FROM DEMO_WALMART_FACT_SNAPSHOT;
```

Expected after the changed-batch simulation:

```text
total_rows       421,571
current_rows     421,570
historical_rows  1
```

Changed-key inspection:

```sql
SELECT
    store_id,
    dept_id,
    date_id,
    store_weekly_sales,
    dbt_valid_from,
    dbt_valid_to
FROM DEMO_WALMART_FACT_SNAPSHOT
WHERE store_id = 1
  AND dept_id = 1
  AND date_id = 20100205
ORDER BY dbt_valid_from;
```

Expected:

```text
Two rows for the changed key:
- one historical row with dbt_valid_to populated
- one current row with dbt_valid_to null
```
