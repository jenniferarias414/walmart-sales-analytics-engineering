# dbt Project Setup and Snowflake Connection

## Purpose

After loading the Walmart source files into Snowflake raw tables, I set up dbt so the project can begin modeling the data.

This phase does not transform data yet. It confirms that dbt is installed, connected to Snowflake, and aware of the raw source tables.

## Local dbt Core setup

This project uses dbt Core locally from the command line.

That means:

```text
VS Code is used to edit project files.
The terminal is used to run dbt commands.
Snowflake is the warehouse where SQL runs.
GitHub version-controls the project files.
```

This is different from a browser-based dbt workspace where connection settings and the development environment may be managed through the UI.

## Why I used dbt Core here

The Walmart project is an end-to-end repo that includes:

```text
Python profiling
Python S3 ingestion
Snowflake SQL setup
dbt transformation project
documentation
screenshots
learning notes
```

Using dbt Core locally keeps the dbt project files inside the same repo as the rest of the build.

The Snowflake connection profile lives outside the repo so credentials are not committed.

## Repo files created

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

## Local profile outside the repo

dbt Core uses a local profile file for warehouse connection settings:

```text
~/.dbt/profiles.yml
```

On this machine, that means:

```text
/Users/e189958/.dbt/profiles.yml
```

This file is outside the repo and should not be committed.

The profile points dbt to Snowflake using:

```text
account
user
role
warehouse
database
schema
password environment variable
```

## Environment variables

The profile uses environment variables for credentials:

```yaml
account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
user: "{{ env_var('SNOWFLAKE_USER') }}"
password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
```

The password is supplied in the terminal session instead of being saved to GitHub.

Because this terminal uses zsh, the working password prompt command was:

```bash
read -s "SNOWFLAKE_PASSWORD?Snowflake password: "
```

## dbt command sequence used

```bash
dbt debug
dbt parse
dbt ls --resource-type source
dbt docs generate
dbt docs serve
```

What each command proved:

| Command | Purpose |
|---|---|
| `dbt debug` | Validated the dbt project, profile, adapter, and Snowflake connection |
| `dbt parse` | Parsed the dbt project files |
| `dbt ls --resource-type source` | Listed the declared raw Snowflake tables as dbt sources |
| `dbt docs generate` | Generated local documentation artifacts |
| `dbt docs serve` | Opened a local dbt docs site in the browser |

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

instead of hardcoding the full database, schema, and table name.

## Completed evidence

`dbt debug` confirmed the local dbt project could connect to Snowflake:

![dbt debug success](../screenshots/full-walkthrough/07-dbt-debug-success.png)

`dbt ls --resource-type source` confirmed dbt recognized the raw Snowflake tables as sources:

![dbt source list](../screenshots/full-walkthrough/08-dbt-source-list.png)

The local dbt docs site showed the Walmart raw sources in the generated documentation:

![dbt docs source lineage](../screenshots/full-walkthrough/09-dbt-docs-source-lineage.png)

## Official dbt references

- [dbt Core connection profiles](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles)
- [dbt sources](https://docs.getdbt.com/docs/build/sources)
- [dbt commands](https://docs.getdbt.com/reference/dbt-commands)
- [dbt debug](https://docs.getdbt.com/reference/commands/debug)
- [dbt docs generate and serve](https://docs.getdbt.com/reference/commands/cmd-docs)
- [dbt Studio IDE](https://docs.getdbt.com/docs/cloud/studio-ide/develop-in-studio)

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

Next, the project moves into dbt staging models, where the raw `VARCHAR` fields will be renamed and cast into intentional warehouse types.
