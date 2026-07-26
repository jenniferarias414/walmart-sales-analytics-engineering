with source as (

    select *
    from {{ source('walmart_raw', 'department_sales') }}

),

renamed_and_casted as (

   TODO: Add column renaming and type casting here, if needed

)

select *
from renamed_and_casted
