{% snapshot walmart_fact_snapshot %}

{{
    config(
        target_database='WALMART_SALES_ANALYTICS',
        target_schema='MARTS',
        unique_key='fact_business_key',
        strategy='check',
        check_cols=[
            'store_size',
            'store_weekly_sales',
            'fuel_price',
            'store_temperature',
            'unemployment',
            'cpi',
            'markdown1',
            'markdown2',
            'markdown3',
            'markdown4',
            'markdown5'
        ]
    )
}}

with source as (

    select *
    from {{ ref('int_walmart_sales_enriched') }}

),

prepared as (

    select
        -- dbt snapshots need one unique key to identify the logical record.
        -- The business key for this fact is store_id + dept_id + date_id.
        store_id::varchar || '-' || dept_id::varchar || '-' || date_id::varchar
            as fact_business_key,

        store_id,
        dept_id,
        date_id,

        store_size,
        store_weekly_sales,
        fuel_price,
        store_temperature,
        unemployment,
        cpi,
        markdown1,
        markdown2,
        markdown3,
        markdown4,
        markdown5

    from source

)

select *
from prepared

{% endsnapshot %}
