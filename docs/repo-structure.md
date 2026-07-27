# Repository Structure

This project is organized as an end-to-end analytics engineering workflow.

## Main folders

| Folder | Purpose |
|---|---|
| `analysis/` | Source profiling script and generated source-profile summary. |
| `data/raw/` | Local landing folder for supplied source CSVs. CSV files are gitignored. |
| `dbt/walmart_sales_analytics/` | Nested dbt Core project for staging, intermediate, mart, snapshot, macro, and test logic. |
| `docs/` | Project documentation, architecture decisions, validation queries, reporting notes, and design references. |
| `learning-notes/` | Public learning notes written as project walkthroughs. |
| `manifests/` | Local ingestion manifest folder. Generated JSON manifests are gitignored because they may include local paths/account metadata. |
| `reports/` | Reporting folder. Generated CSV and PNG outputs are written under `reports/generated/` and are gitignored. |
| `screenshots/` | Evidence screenshots captured during the build. |
| `scripts/` | Executable Python utilities, including S3 ingestion and Snowflake reporting generation. |
| `sql/` | Standalone SQL files for Snowflake setup/loading and reporting queries. |

## Local-only folders

| Folder | Purpose |
|---|---|
| `notes/` | Private working notes. This folder is ignored and should not be committed. |
| `.venv/` | Local Python virtual environment. This folder is ignored. |
| `dbt/walmart_sales_analytics/target/` | dbt-generated compiled artifacts and docs output. This folder is ignored. |
| `reports/generated/` | Generated report CSVs/charts. This folder is ignored; screenshots and reproducible scripts are committed instead. |

## Why there is a nested dbt folder

The repository is the full project:

```text
walmart-sales-analytics-engineering
```

The dbt project is nested inside it:

```text
dbt/walmart_sales_analytics
```

That separation keeps dbt-specific configuration and models together while allowing the repo to also include ingestion scripts, Snowflake SQL, reporting scripts, screenshots, and documentation.

## Why executable Python files live in `scripts/`

The project has two Python utilities:

```text
scripts/ingest_local_batch_to_s3.py
scripts/generate_walmart_reports.py
```

Both are executable workflow scripts, so they live together in `scripts/`.

The reporting SQL itself is still documented separately in:

```text
sql/09_reporting_queries.sql
```
