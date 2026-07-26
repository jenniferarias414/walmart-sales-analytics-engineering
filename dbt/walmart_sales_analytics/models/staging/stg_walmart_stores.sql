with source as (

    select *
    from {{ source('walmart_raw', 'stores') }}

),

renamed_and_casted as (

    select
        try_cast(store_raw as number(10, 0)) as store_id,
        type_raw::varchar as store_type,
        try_cast(size_raw as number(18, 0)) as store_size,

        source_file_name,
        loaded_at

    from source

)

select *
from renamed_and_casted
