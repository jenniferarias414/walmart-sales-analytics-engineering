# Architecture Decisions

## ADR 001: Source profiling before cloud ingestion

### Decision

Profile and analyze the supplied CSV files locally before loading them to S3 and Snowflake.

### Rationale

The source files had different grains and responsibilities. Profiling confirmed row counts, candidate keys, null patterns, date ranges, and join relationships before dbt models were built.

This reduced the risk of designing transformations from assumptions.

### Outcome

The project identified `department.csv` as the driving weekly-sales source, `fact.csv` as store/date context, and `stores.csv` as store attributes.

## ADR 002: Python batch-ingestion utility for local source delivery

### Decision

Use an operator-triggered Python utility to upload the controlled local CSV batch to S3.

### Alternatives considered

| Option | Notes |
|---|---|
| AWS console upload | Simple, but not reproducible or auditable |
| Individual AWS CLI upload commands | Reproducible, but does not validate the batch as a unit |
| Python batch utility | Validates files, records metadata, uploads, verifies, and writes a manifest |
| Lambda/event-driven ingestion | Better for recurring AWS-accessible arrivals, but unnecessary for a one-time local batch |

### Rationale

The source data was supplied locally as one controlled batch. A Python utility provided repeatability, validation, and audit metadata without introducing unnecessary event-driven infrastructure.

### Outcome

The utility uploaded the source files to the S3 landing prefix and created a JSON manifest for the ingestion run.

## ADR 003: Snowflake raw layer with source-preserving VARCHAR columns

### Decision

Load the S3-landed CSV files into Snowflake raw tables with mostly `VARCHAR` columns.

### Rationale

The source files are CSVs, which are text-based and do not enforce a strong schema. The raw Snowflake layer is intended to preserve the source delivery with minimal assumptions.

Intentional casting to dates, numbers, booleans, and decimals will happen later in dbt staging models.

### Outcome

The raw tables preserve the original source fields and include metadata columns for source file name and load timestamp. Row counts were validated against the original source profile.

## ADR 004: Local dbt Core setup with external profile

### Decision

Use a local dbt Core project inside the repository and keep Snowflake connection settings in `~/.dbt/profiles.yml`.

### Rationale

The dbt project files should be version controlled, but local connection details and credentials should not be committed to GitHub.

Using environment variables allows the project to reference Snowflake credentials without storing the password in the repo.

This project uses dbt Core from the command line instead of building directly in the browser-based dbt workspace. That keeps the dbt code, screenshots, SQL scripts, and project documentation together in one GitHub repository while still connecting to the same Snowflake warehouse.

### Outcome

`dbt debug` confirmed that the local dbt project and Snowflake connection are working.

### Evidence

The successful dbt connection check is shown below.

![dbt debug success](../screenshots/full-walkthrough/07-dbt-debug-success.png)

The declared raw Snowflake tables are visible to dbt as sources.

![dbt source list](../screenshots/full-walkthrough/08-dbt-source-list.png)
