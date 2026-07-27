with snapshotted_fact as (

    select *
    from {{ ref('walmart_fact_snapshot') }}

),

final as (

    select
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
        markdown5,

        dbt_valid_from::timestamp_ntz as vrsn_start_date,
        dbt_valid_to::timestamp_ntz as vrsn_end_date,

        dbt_valid_from::timestamp_ntz as insert_date,
        dbt_updated_at::timestamp_ntz as update_date

    from snapshotted_fact

)

select *
from final
