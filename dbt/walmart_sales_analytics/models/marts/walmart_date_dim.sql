with sales_dates as (

    select distinct
        date_id,
        store_date,
        is_holiday
    from {{ ref('int_walmart_sales_enriched') }}

),

date_dim as (

    select
        date_id,
        store_date,
        is_holiday,

        current_timestamp()::timestamp_ntz as insert_date,
        current_timestamp()::timestamp_ntz as update_date

    from sales_dates

)

select *
from date_dim
