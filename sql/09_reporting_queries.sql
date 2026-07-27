-- Phase 9: Reporting queries for Walmart Sales Analytics Engineering
-- These queries use the final mart tables.

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_WALMART_XS;
USE DATABASE WALMART_SALES_ANALYTICS;
USE SCHEMA MARTS;

-- 1. Monthly sales trend
SELECT
    DATE_TRUNC('month', d.store_date) AS sales_month,
    SUM(f.store_weekly_sales) AS total_sales
FROM WALMART_FACT_TABLE f
JOIN WALMART_DATE_DIM d
    ON f.date_id = d.date_id
WHERE f.vrsn_end_date IS NULL
GROUP BY 1
ORDER BY 1;

-- 2. Sales by store type
SELECT
    s.store_type,
    COUNT(DISTINCT f.store_id) AS store_count,
    SUM(f.store_weekly_sales) AS total_sales,
    AVG(f.store_weekly_sales) AS avg_weekly_sales
FROM WALMART_FACT_TABLE f
JOIN WALMART_STORE_DIM s
    ON f.store_id = s.store_id
    AND f.dept_id = s.dept_id
WHERE f.vrsn_end_date IS NULL
GROUP BY 1
ORDER BY total_sales DESC;

-- 3. Holiday versus non-holiday sales
SELECT
    d.is_holiday,
    COUNT(*) AS weekly_sales_records,
    SUM(f.store_weekly_sales) AS total_sales,
    AVG(f.store_weekly_sales) AS avg_weekly_sales
FROM WALMART_FACT_TABLE f
JOIN WALMART_DATE_DIM d
    ON f.date_id = d.date_id
WHERE f.vrsn_end_date IS NULL
GROUP BY 1
ORDER BY d.is_holiday DESC;

-- 4. Top 10 store/department combinations by total sales
SELECT
    f.store_id,
    f.dept_id,
    SUM(f.store_weekly_sales) AS total_sales
FROM WALMART_FACT_TABLE f
WHERE f.vrsn_end_date IS NULL
GROUP BY 1, 2
ORDER BY total_sales DESC
LIMIT 10;

-- 5. Sales and markdowns by year
SELECT
    EXTRACT(year FROM d.store_date) AS sales_year,
    SUM(f.store_weekly_sales) AS total_sales,
    SUM(
        COALESCE(f.markdown1, 0)
        + COALESCE(f.markdown2, 0)
        + COALESCE(f.markdown3, 0)
        + COALESCE(f.markdown4, 0)
        + COALESCE(f.markdown5, 0)
    ) AS total_markdowns,
    COUNT_IF(
        f.markdown1 IS NOT NULL
        OR f.markdown2 IS NOT NULL
        OR f.markdown3 IS NOT NULL
        OR f.markdown4 IS NOT NULL
        OR f.markdown5 IS NOT NULL
    ) AS rows_with_markdown
FROM WALMART_FACT_TABLE f
JOIN WALMART_DATE_DIM d
    ON f.date_id = d.date_id
WHERE f.vrsn_end_date IS NULL
GROUP BY 1
ORDER BY 1;

-- 6. Sales by temperature band
SELECT
    CASE
        WHEN f.store_temperature < 32 THEN 'Below 32'
        WHEN f.store_temperature < 50 THEN '32 to 49'
        WHEN f.store_temperature < 70 THEN '50 to 69'
        WHEN f.store_temperature < 90 THEN '70 to 89'
        ELSE '90 and above'
    END AS temperature_band,
    CASE
        WHEN f.store_temperature < 32 THEN 1
        WHEN f.store_temperature < 50 THEN 2
        WHEN f.store_temperature < 70 THEN 3
        WHEN f.store_temperature < 90 THEN 4
        ELSE 5
    END AS sort_order,
    COUNT(*) AS weekly_sales_records,
    SUM(f.store_weekly_sales) AS total_sales,
    AVG(f.store_weekly_sales) AS avg_weekly_sales
FROM WALMART_FACT_TABLE f
WHERE f.vrsn_end_date IS NULL
GROUP BY 1, 2
ORDER BY sort_order;
