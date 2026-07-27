{% snapshot demo_walmart_fact_snapshot %}

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
        store_id::varchar || '-' || dept_id::varchar || '-' || date_id::varchar
            as fact_business_key,

        store_id,
        dept_id,
        date_id,

        store_size,

        case
            when {{ var('demo_adjust_weekly_sales', false) }}
                and store_id = 1
                and dept_id = 1
                and date_id = 20100205
            then store_weekly_sales + 100
            else store_weekly_sales
        end as store_weekly_sales,

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
