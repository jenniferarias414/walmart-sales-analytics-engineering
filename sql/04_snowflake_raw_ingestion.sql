-- ============================================================
-- Phase 4: Snowflake Raw Ingestion
-- Project: Walmart Sales Analytics Engineering
--
-- Goal:
-- Load the original Walmart CSV files from the S3 landing bucket
-- into Snowflake raw tables.
--
-- At this point in the project, I am not building the final
-- dimensions or fact table yet. This phase only creates the raw
-- Snowflake layer.
--
-- Raw layer decision:
-- The CSV files are loaded into mostly VARCHAR columns so the raw
-- tables stay close to the original source files. The intentional
-- casts to NUMBER, DATE, BOOLEAN, and DECIMAL will happen later in
-- dbt staging models.
-- ============================================================


-- ============================================================
-- 1. Use setup role
-- ============================================================
-- I am using ACCOUNTADMIN for this setup because this is my personal
-- Snowflake project account and storage integrations require elevated
-- privileges.
--
-- In a work environment, this type of setup would usually be handled
-- by a Snowflake admin/platform role instead of an individual developer
-- role.
-- ============================================================
USE ROLE ACCOUNTADMIN;


-- ============================================================
-- 2. Create project warehouse, database, and schemas
-- ============================================================
-- The warehouse provides compute for running SQL.
-- The database keeps this project isolated from other work.
-- The schemas separate the pipeline layers:
--
-- RAW:
--   Source-preserving tables loaded from S3.
--
-- STAGING:
--   dbt models that rename fields and apply data types.
--
-- MARTS:
--   Final business-ready dimension and fact tables.
-- ============================================================

CREATE WAREHOUSE IF NOT EXISTS WH_WALMART_XS
    WAREHOUSE_SIZE = XSMALL
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS WALMART_SALES_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS WALMART_SALES_ANALYTICS.RAW;
CREATE SCHEMA IF NOT EXISTS WALMART_SALES_ANALYTICS.STAGING;
CREATE SCHEMA IF NOT EXISTS WALMART_SALES_ANALYTICS.MARTS;

USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA RAW;


-- ============================================================
-- 3. Create CSV file format
-- ============================================================
-- This tells Snowflake how to read the CSV files in S3.
--
-- The source files have a header row, so SKIP_HEADER = 1.
-- The files are comma-delimited.
-- Blank fields should load as NULL instead of empty strings.
-- EMPTY_FIELD_AS_NULL and NULL_IF help preserve blanks as NULL.
-- FIELD_OPTIONALLY_ENCLOSED_BY = '"' handles quoted CSV values.
-- TRIM_SPACE = TRUE removes leading/trailing whitespace from values.
--
-- This file format is used by the external stage and COPY INTO
-- commands below.
-- ============================================================

CREATE OR REPLACE FILE FORMAT FF_WALMART_CSV
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    EMPTY_FIELD_AS_NULL = TRUE
    NULL_IF = ('', 'NULL', 'null')
    TRIM_SPACE = TRUE;


-- ============================================================
-- 4. Create Snowflake storage integration
-- ============================================================
-- The storage integration is the Snowflake object that connects
-- Snowflake to the allowed S3 location.
--
-- This does not load data by itself. It only defines the secure access
-- path Snowflake will use later when reading files from S3.
--
-- Replace <AWS_ACCOUNT_ID> locally before running this script.
-- Do not commit Snowflake external IDs or secret values to GitHub.
-- ============================================================

CREATE OR REPLACE STORAGE INTEGRATION INT_WALMART_S3
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = S3
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<AWS_ACCOUNT_ID>:role/snowflake-walmart-s3-read-role'
    STORAGE_ALLOWED_LOCATIONS = (
        's3://walmart-sales-landing-jenny/landing/walmart/batch_01/'
    );


-- ============================================================
-- 5. Describe the storage integration
-- ============================================================
-- DESC INTEGRATION returns Snowflake-generated values needed for
-- the AWS IAM role trust policy:
--
-- STORAGE_AWS_IAM_USER_ARN:
--   The Snowflake IAM principal that AWS should trust.
--
-- STORAGE_AWS_EXTERNAL_ID:
--   The external ID AWS uses to confirm the AssumeRole request is
--   coming from this Snowflake integration.
--
-- I used these values in AWS when creating the IAM role. I do not
-- commit the actual external ID to the repo.
-- ============================================================

DESC INTEGRATION INT_WALMART_S3;


-- ============================================================
-- Phase 4B: Create stage, raw tables, and load files
-- ============================================================
-- After the Snowflake integration and AWS IAM role trust are connected,
-- Snowflake can read the files in the S3 landing prefix.
--
-- This section creates:
--   1. An external stage pointing to the S3 batch folder
--   2. Raw tables for each source file
--   3. COPY INTO commands to load each CSV
--   4. Row-count validation queries
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA RAW;


-- ============================================================
-- 6. Create external stage
-- ============================================================
-- The stage is a Snowflake pointer to the S3 folder where the batch
-- files landed.
--
-- The stage uses:
--   - the storage integration for S3 access
--   - the CSV file format for parsing
--
-- LIST confirms Snowflake can see the expected files before loading.
-- ============================================================

CREATE OR REPLACE STAGE STG_WALMART_S3_BATCH_01
    URL = 's3://walmart-sales-landing-jenny/landing/walmart/batch_01/'
    STORAGE_INTEGRATION = INT_WALMART_S3
    FILE_FORMAT = FF_WALMART_CSV;


-- Check that Snowflake can see the S3 files.
LIST @STG_WALMART_S3_BATCH_01;


-- ============================================================
-- 7. Create raw tables
-- ============================================================
-- These tables are the Snowflake raw layer.
--
-- I am keeping the source fields as VARCHAR on purpose because the
-- files came from CSV. This keeps the raw layer close to the original
-- source delivery.
--
-- dbt staging models will later cast these fields into the intended
-- warehouse types.
--
-- I also add:
--   source_file_name = which S3 file the row came from
--   loaded_at        = when Snowflake loaded the row
-- ============================================================

CREATE OR REPLACE TABLE RAW_WALMART_STORES (
    store_raw VARCHAR,
    type_raw VARCHAR,
    size_raw VARCHAR,
    source_file_name VARCHAR,
    loaded_at TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE RAW_WALMART_DEPARTMENT_SALES (
    store_raw VARCHAR,
    dept_raw VARCHAR,
    date_raw VARCHAR,
    weekly_sales_raw VARCHAR,
    is_holiday_raw VARCHAR,
    source_file_name VARCHAR,
    loaded_at TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE RAW_WALMART_STORE_FEATURES (
    store_raw VARCHAR,
    date_raw VARCHAR,
    temperature_raw VARCHAR,
    fuel_price_raw VARCHAR,
    markdown1_raw VARCHAR,
    markdown2_raw VARCHAR,
    markdown3_raw VARCHAR,
    markdown4_raw VARCHAR,
    markdown5_raw VARCHAR,
    cpi_raw VARCHAR,
    unemployment_raw VARCHAR,
    is_holiday_raw VARCHAR,
    source_file_name VARCHAR,
    loaded_at TIMESTAMP_NTZ
);


-- ============================================================
-- 8. Load raw tables from S3
-- ============================================================
-- COPY INTO loads data from the external stage into Snowflake tables.
--
-- The CSV columns are referenced by position:
--   $1 = first CSV column
--   $2 = second CSV column
--   etc.
--
-- I am not using column-name matching here because the raw tables
-- include extra metadata columns that do not exist in the CSV files.
--
-- ON_ERROR = 'ABORT_STATEMENT' tells Snowflake to stop if the load
-- encounters a problem instead of silently skipping bad rows.
-- ============================================================

COPY INTO RAW_WALMART_STORES (
    store_raw,
    type_raw,
    size_raw,
    source_file_name,
    loaded_at
)
FROM (
    SELECT
        $1,
        $2,
        $3,
        METADATA$FILENAME,
        CURRENT_TIMESTAMP()
    FROM @STG_WALMART_S3_BATCH_01/stores.csv
)
FILE_FORMAT = FF_WALMART_CSV
ON_ERROR = 'ABORT_STATEMENT';


COPY INTO RAW_WALMART_DEPARTMENT_SALES (
    store_raw,
    dept_raw,
    date_raw,
    weekly_sales_raw,
    is_holiday_raw,
    source_file_name,
    loaded_at
)
FROM (
    SELECT
        $1,
        $2,
        $3,
        $4,
        $5,
        METADATA$FILENAME,
        CURRENT_TIMESTAMP()
    FROM @STG_WALMART_S3_BATCH_01/department.csv
)
FILE_FORMAT = FF_WALMART_CSV
ON_ERROR = 'ABORT_STATEMENT';


COPY INTO RAW_WALMART_STORE_FEATURES (
    store_raw,
    date_raw,
    temperature_raw,
    fuel_price_raw,
    markdown1_raw,
    markdown2_raw,
    markdown3_raw,
    markdown4_raw,
    markdown5_raw,
    cpi_raw,
    unemployment_raw,
    is_holiday_raw,
    source_file_name,
    loaded_at
)
FROM (
    SELECT
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7,
        $8,
        $9,
        $10,
        $11,
        $12,
        METADATA$FILENAME,
        CURRENT_TIMESTAMP()
    FROM @STG_WALMART_S3_BATCH_01/fact.csv
)
FILE_FORMAT = FF_WALMART_CSV
ON_ERROR = 'ABORT_STATEMENT';


-- ============================================================
-- 9. Validate raw row counts
-- ============================================================
-- The raw Snowflake row counts should match the source profiling
-- results from analysis/output/source-data-profile.md.
--
-- Expected:
--   RAW_WALMART_STORES              45
--   RAW_WALMART_DEPARTMENT_SALES    421,570
--   RAW_WALMART_STORE_FEATURES      8,190
--
-- Matching counts confirm that the S3-to-Snowflake raw load preserved
-- the expected number of source rows.
-- ============================================================

SELECT 'RAW_WALMART_STORES' AS table_name, COUNT(*) AS row_count
FROM RAW_WALMART_STORES
UNION ALL
SELECT 'RAW_WALMART_DEPARTMENT_SALES' AS table_name, COUNT(*) AS row_count
FROM RAW_WALMART_DEPARTMENT_SALES
UNION ALL
SELECT 'RAW_WALMART_STORE_FEATURES' AS table_name, COUNT(*) AS row_count
FROM RAW_WALMART_STORE_FEATURES;


-- Preview raw rows.
SELECT * FROM RAW_WALMART_STORES LIMIT 10;    -- 45 rows expected
SELECT * FROM RAW_WALMART_DEPARTMENT_SALES LIMIT 10;  -- 421,570 rows expected
SELECT * FROM RAW_WALMART_STORE_FEATURES LIMIT 10;  -- 8,190 rows expected