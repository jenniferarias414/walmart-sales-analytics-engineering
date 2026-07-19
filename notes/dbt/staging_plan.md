dbt’s commonly recommended structure is:

sources
    ↓
staging
    ↓
intermediate
    ↓
marts


dbt describes staging models as source-aligned building blocks, typically with a one-to-one relationship to source tables. Intermediate models break complex transformations into reusable steps, and marts represent business-conformed entities intended for downstream use.




For this project:
-------------------------------------

BRONZE / RAW

S3 landing files
Snowflake raw_walmart_stores
Snowflake raw_walmart_department_sales
Snowflake raw_walmart_store_features

-------------------------------------

STAGING / EARLY SILVER

stg_walmart_stores
stg_walmart_department_sales
stg_walmart_store_features

-------------------------------------

SILVER / INTERMEDIATE

int_walmart_sales_enriched

-------------------------------------

GOLD / MARTS

walmart_date_dim
walmart_store_dim
walmart_fact_table

-------------------------------------


Medallion architecture broadly describes bronze as raw, silver as cleaned/refined, and gold as curated business-ready data.

The direction is:

staging models
        ↓
int_walmart_sales_enriched
        ↓
date dimension
store dimension
fact snapshot / final fact



The intermediate model does not contain the dimensions.

It supplies prepared data to them.

The snapshot is a technical history object supporting the final gold fact.