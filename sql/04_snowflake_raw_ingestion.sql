-- ============================================================
-- Phase 4: Snowflake Raw Ingestion
-- Project: Walmart Sales Analytics Engineering
--
-- Goal:
-- Load the original S3-landed CSV files into Snowflake raw tables.
--
-- This script intentionally keeps the raw layer source-preserving.
-- Most raw columns are VARCHAR. Type casting happens later in dbt
-- staging models.
-- ============================================================


-- ============================================================
-- 1. Use an admin-capable role for setup
-- ============================================================
-- ACCOUNTADMIN is commonly used for learning/sandbox setup because
-- storage integrations require elevated privileges.
-- In an enterprise account, a more controlled role would usually own this.
USE ROLE ACCOUNTADMIN;


-- ============================================================
-- 2. Create project warehouse, database, and schemas
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
-- 3. Create a CSV file format
-- ============================================================
-- This tells Snowflake how to interpret the CSV files.
--
-- SKIP_HEADER = 1 means the first row contains column names.
-- FIELD_OPTIONALLY_ENCLOSED_BY = '"' handles quoted CSV values.
-- EMPTY_FIELD_AS_NULL and NULL_IF help preserve blanks as NULL.
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
-- 4. Create the storage integration
-- ============================================================
-- IMPORTANT:
-- Replace <AWS_ROLE_ARN_AFTER_YOU_CREATE_IT> after creating the
-- AWS IAM role.
--
-- First run this statement with a placeholder role name if you already
-- know what your IAM role ARN will be, or come back to it after creating
-- the IAM role in AWS.
--
-- Planned IAM role name:
-- snowflake-walmart-s3-read-role
--
-- Example final ARN format:
-- arn:aws:iam::<your_account_id>:role/snowflake-walmart-s3-read-role
-- ============================================================

CREATE OR REPLACE STORAGE INTEGRATION INT_WALMART_S3
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = S3
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::272987324508:role/snowflake-walmart-s3-read-role'
    STORAGE_ALLOWED_LOCATIONS = (
        's3://walmart-sales-landing-jenny/landing/walmart/batch_01/'
    );


-- ============================================================
-- 5. Run this after creating the storage integration
-- ============================================================
-- Copy the values for:
-- STORAGE_AWS_IAM_USER_ARN
-- STORAGE_AWS_EXTERNAL_ID
--
-- You will use those values in the AWS IAM role trust policy.
-- ============================================================

DESC INTEGRATION INT_WALMART_S3;


-- ============================================================
-- Phase 4B: Create external stage, raw tables, and load S3 files
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA RAW;


-- ============================================================
-- 6. Create external stage
-- ============================================================
-- The stage points Snowflake to the S3 prefix that contains the CSVs.
-- It uses the storage integration for secure access.
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
-- Raw tables intentionally keep values as VARCHAR.
-- dbt staging will cast to NUMBER, DATE, BOOLEAN, DECIMAL, etc.
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
-- COPY INTO loads staged files into Snowflake tables.
-- We are loading CSV columns by position: $1, $2, $3, etc.
-- We also add source metadata columns manually.
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
-- These should match the source profile:
-- stores: 45
-- department sales: 421,570
-- store features: 8,190
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
SELECT * FROM RAW_WALMART_STORES LIMIT 10;
SELECT * FROM RAW_WALMART_DEPARTMENT_SALES LIMIT 10;
SELECT * FROM RAW_WALMART_STORE_FEATURES LIMIT 10;