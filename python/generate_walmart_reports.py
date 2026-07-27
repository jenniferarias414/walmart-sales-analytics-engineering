"""
Generate Walmart sales reporting outputs from Snowflake marts.

Outputs:
- CSV files under reports/generated/
- PNG charts under reports/generated/
- reporting_summary.md under reports/generated/

Required environment variables:
- SNOWFLAKE_ACCOUNT
- SNOWFLAKE_USER
- SNOWFLAKE_PASSWORD

Optional environment variables:
- SNOWFLAKE_ROLE
- SNOWFLAKE_WAREHOUSE
- SNOWFLAKE_DATABASE
- SNOWFLAKE_SCHEMA
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import snowflake.connector


OUTPUT_DIR = Path("reports/generated")

SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "WH_WALMART_XS"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "WALMART_SALES_ANALYTICS"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "MARTS"),
}


QUERIES = {
    "sales_by_month": """
        SELECT
            DATE_TRUNC('month', d.store_date) AS sales_month,
            SUM(f.store_weekly_sales) AS total_sales
        FROM WALMART_FACT_TABLE f
        JOIN WALMART_DATE_DIM d
            ON f.date_id = d.date_id
        WHERE f.vrsn_end_date IS NULL
        GROUP BY 1
        ORDER BY 1
    """,
    "sales_by_store_type": """
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
        ORDER BY total_sales DESC
    """,
    "holiday_vs_nonholiday_sales": """
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
        ORDER BY d.is_holiday DESC
    """,
    "top_10_store_departments": """
        SELECT
            f.store_id,
            f.dept_id,
            SUM(f.store_weekly_sales) AS total_sales
        FROM WALMART_FACT_TABLE f
        WHERE f.vrsn_end_date IS NULL
        GROUP BY 1, 2
        ORDER BY total_sales DESC
        LIMIT 10
    """,
    "sales_and_markdowns_by_year": """
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
        ORDER BY 1
    """,
    "sales_by_temperature_band": """
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
        ORDER BY sort_order
    """,
}


def validate_config(config: dict[str, Any]) -> None:
    """Make sure required Snowflake connection values are present."""
    missing = [
        key
        for key in ["account", "user", "password"]
        if not config.get(key)
    ]

    if missing:
        missing_names = ", ".join(missing)
        raise RuntimeError(
            f"Missing Snowflake config values: {missing_names}. "
            "Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and SNOWFLAKE_PASSWORD."
        )


def fetch_dataframe(
    connection: snowflake.connector.SnowflakeConnection,
    sql: str,
) -> pd.DataFrame:
    """Run a SQL query and return a pandas DataFrame."""
    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [column[0].lower() for column in cursor.description]

    return pd.DataFrame(rows, columns=columns)


def save_csv_outputs(dataframes: dict[str, pd.DataFrame]) -> None:
    """Write each reporting DataFrame to CSV."""
    for name, dataframe in dataframes.items():
        output_path = OUTPUT_DIR / f"{name}.csv"
        dataframe.to_csv(output_path, index=False)
        print(f"Wrote {output_path}")


def chart_sales_by_month(dataframe: pd.DataFrame) -> None:
    chart_df = dataframe.copy()
    chart_df["sales_month"] = pd.to_datetime(chart_df["sales_month"])

    plt.figure(figsize=(10, 5))
    plt.plot(chart_df["sales_month"], chart_df["total_sales"], marker="o")
    plt.title("Monthly Walmart Sales")
    plt.xlabel("Sales Month")
    plt.ylabel("Total Sales")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sales_by_month.png", dpi=150)
    plt.close()


def chart_sales_by_store_type(dataframe: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))
    plt.bar(dataframe["store_type"], dataframe["total_sales"])
    plt.title("Total Sales by Store Type")
    plt.xlabel("Store Type")
    plt.ylabel("Total Sales")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sales_by_store_type.png", dpi=150)
    plt.close()


def chart_holiday_vs_nonholiday(dataframe: pd.DataFrame) -> None:
    chart_df = dataframe.copy()
    chart_df["holiday_label"] = chart_df["is_holiday"].map({
        True: "Holiday",
        False: "Non-Holiday",
    })

    plt.figure(figsize=(8, 5))
    plt.bar(chart_df["holiday_label"], chart_df["avg_weekly_sales"])
    plt.title("Average Weekly Sales: Holiday vs Non-Holiday")
    plt.xlabel("Week Type")
    plt.ylabel("Average Weekly Sales")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "holiday_vs_nonholiday_sales.png", dpi=150)
    plt.close()


def chart_top_store_departments(dataframe: pd.DataFrame) -> None:
    chart_df = dataframe.copy()
    chart_df["store_dept"] = (
        "Store "
        + chart_df["store_id"].astype(str)
        + " / Dept "
        + chart_df["dept_id"].astype(str)
    )

    plt.figure(figsize=(10, 6))
    plt.barh(chart_df["store_dept"], chart_df["total_sales"])
    plt.title("Top 10 Store/Department Combinations by Sales")
    plt.xlabel("Total Sales")
    plt.ylabel("Store / Department")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "top_10_store_departments.png", dpi=150)
    plt.close()


def chart_sales_by_temperature_band(dataframe: pd.DataFrame) -> None:
    plt.figure(figsize=(9, 5))
    plt.bar(dataframe["temperature_band"], dataframe["avg_weekly_sales"])
    plt.title("Average Weekly Sales by Temperature Band")
    plt.xlabel("Temperature Band")
    plt.ylabel("Average Weekly Sales")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sales_by_temperature_band.png", dpi=150)
    plt.close()


def write_summary(dataframes: dict[str, pd.DataFrame]) -> None:
    sales_by_store_type = dataframes["sales_by_store_type"]
    top_store_type = sales_by_store_type.iloc[0]

    holiday = dataframes["holiday_vs_nonholiday_sales"].copy()
    holiday["holiday_label"] = holiday["is_holiday"].map({
        True: "Holiday",
        False: "Non-Holiday",
    })

    top_store_department = dataframes["top_10_store_departments"].iloc[0]

    summary = (
        "# Walmart Reporting Summary\n\n"
        "Generated from Snowflake mart tables.\n\n"
        "## Key observations\n\n"
        f"- Highest total sales by store type: Store Type {top_store_type['store_type']}.\n"
        f"- Top store/department combination: Store {top_store_department['store_id']}, "
        f"Department {top_store_department['dept_id']}.\n"
        "- Reporting outputs were generated from current fact records only, "
        "where `vrsn_end_date IS NULL`.\n\n"
        "## Output files\n\n"
        "CSV outputs and charts are saved under `reports/generated/`.\n\n"
        "## Report queries\n\n"
        "The SQL used for the reporting layer is documented in "
        "`sql/09_reporting_queries.sql`.\n"
    )

    output_path = OUTPUT_DIR / "reporting_summary.md"
    output_path.write_text(summary, encoding="utf-8")
    print(f"Wrote {output_path}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    validate_config(SNOWFLAKE_CONFIG)

    print("Connecting to Snowflake...")
    connection = snowflake.connector.connect(**SNOWFLAKE_CONFIG)

    try:
        dataframes: dict[str, pd.DataFrame] = {}
        for name, sql in QUERIES.items():
            print(f"Running query: {name}")
            dataframes[name] = fetch_dataframe(connection, sql)

        save_csv_outputs(dataframes)

        chart_sales_by_month(dataframes["sales_by_month"])
        chart_sales_by_store_type(dataframes["sales_by_store_type"])
        chart_holiday_vs_nonholiday(dataframes["holiday_vs_nonholiday_sales"])
        chart_top_store_departments(dataframes["top_10_store_departments"])
        chart_sales_by_temperature_band(dataframes["sales_by_temperature_band"])
        write_summary(dataframes)

        print("Reporting outputs generated successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
