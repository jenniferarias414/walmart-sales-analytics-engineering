# Walmart Reporting Summary

Generated from Snowflake mart tables.

## Key observations

- Highest total sales by store type: Store Type A.
- Top store/department combination: Store 14, Department 92.
- Reporting outputs were generated from current fact records only, where `vrsn_end_date IS NULL`.

## Output files

CSV outputs and charts are saved under `reports/generated/`.

## Report queries

The SQL used for the reporting layer is documented in `sql/09_reporting_queries.sql`.
