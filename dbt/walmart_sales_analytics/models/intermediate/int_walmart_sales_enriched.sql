with department_sales as (

    select *
    from {{ ref('stg_walmart_department_sales') }}

),

store_features as (

    select *
    from {{ ref('stg_walmart_store_features') }}

),

stores as (

    select *
    from {{ ref('stg_walmart_stores') }}

),

enriched_sales as (

    select
        department_sales.store_id,
        department_sales.dept_id,
        department_sales.store_date,

        -- Deterministic date key used later by the date dimension and fact table.
        to_number(to_char(department_sales.store_date, 'YYYYMMDD')) as date_id,

        department_sales.store_weekly_sales,
        department_sales.is_holiday,

        stores.store_type,
        stores.store_size,

        store_features.store_temperature,
        store_features.fuel_price,
        store_features.markdown1,
        store_features.markdown2,
        store_features.markdown3,
        store_features.markdown4,
        store_features.markdown5,
        store_features.cpi,
        store_features.unemployment,

        department_sales.source_file_name as sales_source_file_name,
        store_features.source_file_name as features_source_file_name,
        stores.source_file_name as stores_source_file_name,

        department_sales.loaded_at as sales_loaded_at,
        store_features.loaded_at as features_loaded_at,
        stores.loaded_at as stores_loaded_at

    from department_sales

    left join store_features
        on department_sales.store_id = store_features.store_id
        and department_sales.store_date = store_features.store_date

    left join stores
        on department_sales.store_id = stores.store_id

)

select *
from enriched_sales
