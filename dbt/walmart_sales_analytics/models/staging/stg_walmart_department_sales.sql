cat > models/staging/stg_walmart_department_sales.sql <<'SQL'
with source as (

    select *
    from {{ source('walmart_raw', 'department_sales') }}

),

renamed_and_casted as (

    select
        try_cast(store_raw as number(10, 0)) as store_id,
        try_cast(dept_raw as number(10, 0)) as dept_id,
        try_to_date(date_raw) as store_date,
        try_cast(weekly_sales_raw as number(18, 2)) as store_weekly_sales,
        try_cast(is_holiday_raw as boolean) as is_holiday,

        source_file_name,
        loaded_at

    from source

)

select *
from renamed_and_casted
SQL