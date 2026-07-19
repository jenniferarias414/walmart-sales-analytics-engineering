# Source Intake, Profiling, and Modeling Process

## Purpose

This project started with three supplied Walmart CSV files and target table requirements for Snowflake and dbt.

Before loading the files to the cloud, I worked through a source-intake and profiling process to understand what the data represented and how the final warehouse tables should be modeled.

## Process followed

```text
1. Review project requirements
2. Inventory supplied files
3. Inspect schemas and sample rows
4. Profile row counts, nulls, dates, and distinct values
5. Identify the grain of each file
6. Propose and test candidate keys
7. Validate source relationships and joins
8. Create source-to-target mapping
9. Design the final dimensional model
```

## Key source findings

```text
stores.csv
    Store attributes such as type and size

department.csv
    Weekly department sales

fact.csv
    Store/date contextual features such as fuel price,
    temperature, markdowns, CPI, unemployment, and holiday flag
```

Even though one file was named `fact.csv`, the weekly sales measure was in `department.csv`. That made `department.csv` the driving source for the final fact table.

## Grain findings

| Source | Grain |
|---|---|
| `stores.csv` | One row per store |
| `department.csv` | One row per store, department, and date |
| `fact.csv` | One row per store and date |

Understanding the grain was important because the files could not be joined safely until I knew what one row represented in each source.

## Candidate keys

| Source | Candidate Key |
|---|---|
| `stores.csv` | `Store` |
| `department.csv` | `Store + Dept + Date` |
| `fact.csv` | `Store + Date` |

I tested these candidate keys for duplicates before using them in joins or model design.

## Join design

The final fact model begins with the weekly-sales source:

```text
department.csv
    LEFT JOIN fact.csv
        ON Store + Date
    LEFT JOIN stores.csv
        ON Store
```

The sales source stays on the left side of the join because the final fact table should preserve weekly department-sales records.

## Dimensional model

| Table | Grain | History Behavior |
|---|---|---|
| `walmart_date_dim` | One row per date | SCD Type 1 |
| `walmart_store_dim` | One row per store and department | SCD Type 1 |
| `walmart_fact_table` | One version of one store, department, and date sales record | SCD Type 2-style versioning |

The fact table follows the supplied project guide by using:

```text
store_id + dept_id + date_id
```

as the composite business key for the logical sales record.

## Main lesson

The important lesson from this phase was that loading data is not the first design step.

Before building dbt models, I needed to understand:

```text
What one row means
What identifies that row
How the files relate
How to prove joins preserve the intended grain
```
