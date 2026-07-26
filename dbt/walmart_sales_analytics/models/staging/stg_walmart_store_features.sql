with source as (

    select *
    from {{ source('walmart_raw', 'store_features') }}

),

renamed_and_casted as (

    select
        try_cast(store_raw as number(10, 0)) as store_id,
        try_to_date(date_raw) as store_date,
        try_cast(temperature_raw as number(10, 2)) as store_temperature,
        try_cast(fuel_price_raw as number(10, 3)) as fuel_price,
        try_cast(markdown1_raw as number(18, 2)) as markdown1,
        try_cast(markdown2_raw as number(18, 2)) as markdown2,
        try_cast(markdown3_raw as number(18, 2)) as markdown3,
        try_cast(markdown4_raw as number(18, 2)) as markdown4,
        try_cast(markdown5_raw as number(18, 2)) as markdown5,
        try_cast(cpi_raw as number(18, 6)) as cpi,
        try_cast(unemployment_raw as number(10, 4)) as unemployment,
        try_cast(is_holiday_raw as boolean) as is_holiday,

        source_file_name,
        loaded_at

    from source

)

select *
from renamed_and_casted
