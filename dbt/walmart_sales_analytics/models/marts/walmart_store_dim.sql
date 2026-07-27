with store_departments as (

    select distinct
        store_id,
        dept_id,
        store_type,
        store_size
    from {{ ref('int_walmart_sales_enriched') }}

),

store_dim as (

    select
        store_id,
        dept_id,
        store_type,
        store_size,

        current_timestamp()::timestamp_ntz as insert_date,
        current_timestamp()::timestamp_ntz as update_date

    from store_departments

)

select *
from store_dim
