from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data" / "raw"
OUTPUT_DIR = ROOT_DIR / "analysis" / "output"
REPORT_PATH = OUTPUT_DIR / "source-data-profile.md"


def require_file(filename: str) -> Path:
    """Return a source path or raise a clear error when it is missing."""
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required source file was not found: {path}\n"
            "Confirm stores.csv, department.csv, and fact.csv are in data/raw/."
        )

    return path


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    """Create a simple Markdown table without an extra dependency."""
    def clean(value: object) -> str:
        return str(value).replace("|", "\\|")

    header_row = "| " + " | ".join(clean(item) for item in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = [
        "| " + " | ".join(clean(item) for item in row) + " |"
        for row in rows
    ]

    return "\n".join([header_row, separator, *body])


def null_count_rows(df: pd.DataFrame) -> list[list[object]]:
    """Return one report row per column with null count and percentage."""
    rows: list[list[object]] = []

    for column in df.columns:
        null_count = int(df[column].isna().sum())
        null_percent = (null_count / len(df)) * 100 if len(df) else 0

        rows.append(
            [
                column,
                null_count,
                f"{null_percent:.2f}%",
            ]
        )

    return rows


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

stores = pd.read_csv(require_file("stores.csv"))
department = pd.read_csv(
    require_file("department.csv"),
    parse_dates=["Date"],
)
fact = pd.read_csv(
    require_file("fact.csv"),
    parse_dates=["Date"],
)

invalid_department_dates = int(department["Date"].isna().sum())
invalid_fact_dates = int(fact["Date"].isna().sum())

stores_duplicate_key_count = int(
    stores.duplicated(["Store"]).sum()
)

department_duplicate_key_count = int(
    department.duplicated(["Store", "Dept", "Date"]).sum()
)

fact_duplicate_key_count = int(
    fact.duplicated(["Store", "Date"]).sum()
)

department_store_dept_count = len(
    department[["Store", "Dept"]].drop_duplicates()
)

department_store_date = department[
    ["Store", "Date", "IsHoliday"]
].drop_duplicates()

fact_store_date = fact[
    ["Store", "Date", "IsHoliday"]
].drop_duplicates()

store_date_coverage = department_store_date.merge(
    fact_store_date,
    on=["Store", "Date"],
    how="outer",
    indicator=True,
    suffixes=("_department", "_fact"),
)

department_keys_without_fact = int(
    (store_date_coverage["_merge"] == "left_only").sum()
)

fact_keys_without_department = int(
    (store_date_coverage["_merge"] == "right_only").sum()
)

matched_store_dates = store_date_coverage[
    store_date_coverage["_merge"] == "both"
].copy()

holiday_mismatch_count = int(
    (
        matched_store_dates["IsHoliday_department"]
        != matched_store_dates["IsHoliday_fact"]
    ).sum()
)

department_holiday_inconsistencies = int(
    (
        department.groupby(["Store", "Date"])["IsHoliday"].nunique()
        > 1
    ).sum()
)

date_holiday_inconsistencies = int(
    (
        department.groupby("Date")["IsHoliday"].nunique()
        > 1
    ).sum()
)

sales_with_context = department.merge(
    fact,
    on=["Store", "Date"],
    how="left",
    validate="many_to_one",
    suffixes=("_sales", "_context"),
)

missing_context_after_join = int(
    sales_with_context["Fuel_Price"].isna().sum()
)

store_department_keys = department[
    ["Store", "Dept"]
].drop_duplicates()

store_dimension_preview = store_department_keys.merge(
    stores,
    on="Store",
    how="left",
    validate="many_to_one",
)

missing_store_attributes = int(
    store_dimension_preview["Type"].isna().sum()
)

negative_weekly_sales = int(
    (department["Weekly_Sales"] < 0).sum()
)

zero_weekly_sales = int(
    (department["Weekly_Sales"] == 0).sum()
)

unused_fact_rows = store_date_coverage[
    store_date_coverage["_merge"] == "right_only"
]

unused_fact_start = (
    unused_fact_rows["Date"].min().date()
    if not unused_fact_rows.empty
    else "N/A"
)

unused_fact_end = (
    unused_fact_rows["Date"].max().date()
    if not unused_fact_rows.empty
    else "N/A"
)

source_summary_rows = [
    [
        "stores.csv",
        f"{len(stores):,}",
        "Store",
        "One row per store",
        ", ".join(stores.columns),
    ],
    [
        "department.csv",
        f"{len(department):,}",
        "Store + Dept + Date",
        "One weekly sales row per store, department, and date",
        ", ".join(department.columns),
    ],
    [
        "fact.csv",
        f"{len(fact):,}",
        "Store + Date",
        "One context/features row per store and date",
        ", ".join(fact.columns),
    ],
]

key_check_rows = [
    [
        "stores.csv",
        "Store",
        stores_duplicate_key_count,
        "PASS" if stores_duplicate_key_count == 0 else "REVIEW",
    ],
    [
        "department.csv",
        "Store + Dept + Date",
        department_duplicate_key_count,
        "PASS" if department_duplicate_key_count == 0 else "REVIEW",
    ],
    [
        "fact.csv",
        "Store + Date",
        fact_duplicate_key_count,
        "PASS" if fact_duplicate_key_count == 0 else "REVIEW",
    ],
]

join_check_rows = [
    [
        "department → fact",
        "Store + Date",
        "many-to-one",
        f"{len(department):,}",
        f"{len(sales_with_context):,}",
        department_keys_without_fact,
    ],
    [
        "department store/dept → stores",
        "Store",
        "many-to-one",
        f"{len(store_department_keys):,}",
        f"{len(store_dimension_preview):,}",
        missing_store_attributes,
    ],
]

report_lines = [
    "# Walmart Source Data Profile",
    "",
    "## Purpose",
    "",
    (
        "This report profiles the supplied source CSV files before cloud "
        "ingestion or dbt modeling. It validates source grains, candidate "
        "keys, null patterns, date ranges, and expected join relationships."
    ),
    "",
    "## Source Summary",
    "",
    markdown_table(
        [
            "Source",
            "Rows",
            "Candidate Key",
            "Expected Grain",
            "Columns",
        ],
        source_summary_rows,
    ),
    "",
    "## Candidate-Key Validation",
    "",
    markdown_table(
        [
            "Source",
            "Candidate Key",
            "Duplicate Rows",
            "Result",
        ],
        key_check_rows,
    ),
    "",
    "## stores.csv Profile",
    "",
    f"- Rows: **{len(stores):,}**",
    f"- Unique stores: **{stores['Store'].nunique():,}**",
    f"- Duplicate Store keys: **{stores_duplicate_key_count:,}**",
    "",
    markdown_table(
        ["Column", "Null Count", "Null Percentage"],
        null_count_rows(stores),
    ),
    "",
    "## department.csv Profile",
    "",
    f"- Rows: **{len(department):,}**",
    f"- Unique stores: **{department['Store'].nunique():,}**",
    f"- Distinct department numbers: **{department['Dept'].nunique():,}**",
    (
        "- Unique Store + Dept combinations: "
        f"**{department_store_dept_count:,}**"
    ),
    f"- Unique dates: **{department['Date'].nunique():,}**",
    (
        "- Date range: "
        f"**{department['Date'].min().date()}** through "
        f"**{department['Date'].max().date()}**"
    ),
    f"- Invalid dates: **{invalid_department_dates:,}**",
    f"- Negative Weekly_Sales rows: **{negative_weekly_sales:,}**",
    f"- Zero Weekly_Sales rows: **{zero_weekly_sales:,}**",
    "",
    markdown_table(
        ["Column", "Null Count", "Null Percentage"],
        null_count_rows(department),
    ),
    "",
    "## fact.csv Profile",
    "",
    f"- Rows: **{len(fact):,}**",
    f"- Unique stores: **{fact['Store'].nunique():,}**",
    f"- Unique dates: **{fact['Date'].nunique():,}**",
    (
        "- Date range: "
        f"**{fact['Date'].min().date()}** through "
        f"**{fact['Date'].max().date()}**"
    ),
    f"- Invalid dates: **{invalid_fact_dates:,}**",
    "",
    markdown_table(
        ["Column", "Null Count", "Null Percentage"],
        null_count_rows(fact),
    ),
    "",
    "## Relationship and Join Validation",
    "",
    markdown_table(
        [
            "Relationship",
            "Join Key",
            "Expected Cardinality",
            "Rows Before",
            "Rows After",
            "Missing Matches",
        ],
        join_check_rows,
    ),
    "",
    (
        "- Unique Store + Date keys in department.csv: "
        f"**{len(department_store_date):,}**"
    ),
    (
        "- Unique Store + Date keys in fact.csv: "
        f"**{len(fact_store_date):,}**"
    ),
    (
        "- Department Store + Date keys without fact context: "
        f"**{department_keys_without_fact:,}**"
    ),
    (
        "- Fact Store + Date keys without department sales: "
        f"**{fact_keys_without_department:,}**"
    ),
    (
        "- Date range for fact-only keys: "
        f"**{unused_fact_start}** through **{unused_fact_end}**"
    ),
    (
        "- Holiday mismatches between department.csv and fact.csv: "
        f"**{holiday_mismatch_count:,}**"
    ),
    (
        "- Inconsistent IsHoliday values within a Store + Date in "
        f"department.csv: **{department_holiday_inconsistencies:,}**"
    ),
    (
        "- Dates with inconsistent IsHoliday values across stores: "
        f"**{date_holiday_inconsistencies:,}**"
    ),
    "",
    "## Modeling Conclusions",
    "",
    "1. `department.csv` is the driving weekly-sales source.",
    (
        "2. The final fact grain is one row per "
        "`Store + Dept + Date + version`."
    ),
    (
        "3. Join department sales to fact context using `Store + Date` "
        "with a many-to-one relationship."
    ),
    (
        "4. Use a left join from department sales to fact context so "
        "sales rows remain authoritative."
    ),
    (
        "5. Build the store dimension at the `Store + Dept` grain by "
        "joining distinct department keys to stores on `Store`."
    ),
    (
        "6. Build the date dimension at one row per date. `IsHoliday` "
        "is consistent at the date grain in the supplied data."
    ),
    (
        "7. Preserve negative and zero weekly sales until a business "
        "definition confirms whether they are adjustments, returns, or errors."
    ),
    (
        "8. Markdown, CPI, and unemployment nulls require explicit "
        "transformation decisions rather than silent deletion."
    ),
    "",
    "## Proposed Date Key",
    "",
    (
        "Use an integer `YYYYMMDD` key, such as "
        "`2010-02-05 → 20100205`. This is deterministic, readable, "
        "and stable when older dates are added."
    ),
    "",
]

REPORT_PATH.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("WALMART SOURCE PROFILING COMPLETE")
print("---------------------------------")
print(f"stores.csv rows: {len(stores):,}")
print(f"department.csv rows: {len(department):,}")
print(f"fact.csv rows: {len(fact):,}")
print()
print(
    "department grain duplicates "
    f"(Store + Dept + Date): {department_duplicate_key_count:,}"
)
print(
    "fact grain duplicates "
    f"(Store + Date): {fact_duplicate_key_count:,}"
)
print()
print(
    "Sales rows before context join: "
    f"{len(department):,}"
)
print(
    "Sales rows after context join:  "
    f"{len(sales_with_context):,}"
)
print(
    "Sales Store + Date keys missing context: "
    f"{department_keys_without_fact:,}"
)
print(
    "Rows missing Fuel_Price after join: "
    f"{missing_context_after_join:,}"
)
print()
print(f"Report written to: {REPORT_PATH}")
