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
