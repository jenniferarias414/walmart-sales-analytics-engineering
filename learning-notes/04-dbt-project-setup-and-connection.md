# dbt Project Setup and Snowflake Connection

## Purpose

After loading the Walmart source files into Snowflake raw tables, I set up dbt so the project can begin modeling the data.

This phase does not transform data yet. It confirms that dbt is installed, connected to Snowflake, and aware of the raw source tables.

## Flow

```text
Snowflake raw tables
    ↓
dbt project configuration
    ↓
local dbt profile
    ↓
dbt debug
    ↓
dbt source definitions
```

## Local dbt Core setup

This project uses local dbt Core from the command line.

That means dbt commands are run from the terminal, while project files are edited in VS Code.

Examples:

```bash
dbt debug
dbt parse
dbt ls
dbt run
dbt test
```

A browser-based dbt workflow can hide some of this setup in the UI. With local dbt Core, I need a local profile file so dbt knows how to connect to Snowflake.

## Files created in the repo

The dbt project lives under:

```text
dbt/walmart_sales_analytics/
```

Important files:

```text
dbt_project.yml
models/staging/_walmart_sources.yml
macros/generate_schema_name.sql
```

## Local profile

dbt Core uses a local profile file for warehouse connection settings:

```text
~/.dbt/profiles.yml
```

This file is outside the repo and should not be committed.

The profile points dbt to Snowflake using account, user, role, warehouse, database, schema, and a password environment variable.

## Source configuration

The source YAML file declares the raw Snowflake tables as dbt sources:

```text
RAW_WALMART_STORES
RAW_WALMART_DEPARTMENT_SALES
RAW_WALMART_STORE_FEATURES
```

Future dbt models can reference the raw tables with:

```sql
{{ source('walmart_raw', 'department_sales') }}
```

instead of hardcoding full database and schema names.

## Validation

`dbt debug` was used to confirm that the dbt project and Snowflake connection are working.

A successful result shows:

```text
All checks passed!
```

## Completed evidence

Add the dbt debug screenshot here:

```text
screenshots/full-walkthrough/07-dbt-debug-success.png
```

![dbt debug success](../screenshots/full-walkthrough/07-dbt-debug-success.png)

Add the dbt source list screenshot here:

```text
screenshots/full-walkthrough/08-dbt-source-list.png
```

![dbt source list](../screenshots/full-walkthrough/08-dbt-source-list.png)

## Main takeaway

This phase connects dbt to the warehouse but does not transform data yet.

The important distinction is:

```text
Snowflake raw tables:
Already loaded source data.

dbt project files:
Version-controlled modeling code.

profiles.yml:
Local connection settings outside the repo.

Environment variables:
Temporary credential values used by dbt at runtime.
```
