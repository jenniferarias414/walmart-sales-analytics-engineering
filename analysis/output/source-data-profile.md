# Walmart Source Data Profile

## Purpose

This report profiles the supplied source CSV files before cloud ingestion or dbt modeling. It validates source grains, candidate keys, null patterns, date ranges, and expected join relationships.

## Source Summary

| Source | Rows | Candidate Key | Expected Grain | Columns |
| --- | --- | --- | --- | --- |
| stores.csv | 45 | Store | One row per store | Store, Type, Size |
| department.csv | 421,570 | Store + Dept + Date | One weekly sales row per store, department, and date | Store, Dept, Date, Weekly_Sales, IsHoliday |
| fact.csv | 8,190 | Store + Date | One context/features row per store and date | Store, Date, Temperature, Fuel_Price, MarkDown1, MarkDown2, MarkDown3, MarkDown4, MarkDown5, CPI, Unemployment, IsHoliday |

## Candidate-Key Validation

| Source | Candidate Key | Duplicate Rows | Result |
| --- | --- | --- | --- |
| stores.csv | Store | 0 | PASS |
| department.csv | Store + Dept + Date | 0 | PASS |
| fact.csv | Store + Date | 0 | PASS |

## stores.csv Profile

- Rows: **45**
- Unique stores: **45**
- Duplicate Store keys: **0**

| Column | Null Count | Null Percentage |
| --- | --- | --- |
| Store | 0 | 0.00% |
| Type | 0 | 0.00% |
| Size | 0 | 0.00% |

## department.csv Profile

- Rows: **421,570**
- Unique stores: **45**
- Distinct department numbers: **81**
- Unique Store + Dept combinations: **3,331**
- Unique dates: **143**
- Date range: **2010-02-05** through **2012-10-26**
- Invalid dates: **0**
- Negative Weekly_Sales rows: **1,285**
- Zero Weekly_Sales rows: **73**

| Column | Null Count | Null Percentage |
| --- | --- | --- |
| Store | 0 | 0.00% |
| Dept | 0 | 0.00% |
| Date | 0 | 0.00% |
| Weekly_Sales | 0 | 0.00% |
| IsHoliday | 0 | 0.00% |

## fact.csv Profile

- Rows: **8,190**
- Unique stores: **45**
- Unique dates: **182**
- Date range: **2010-02-05** through **2013-07-26**
- Invalid dates: **0**

| Column | Null Count | Null Percentage |
| --- | --- | --- |
| Store | 0 | 0.00% |
| Date | 0 | 0.00% |
| Temperature | 0 | 0.00% |
| Fuel_Price | 0 | 0.00% |
| MarkDown1 | 4158 | 50.77% |
| MarkDown2 | 5269 | 64.33% |
| MarkDown3 | 4577 | 55.89% |
| MarkDown4 | 4726 | 57.70% |
| MarkDown5 | 4140 | 50.55% |
| CPI | 585 | 7.14% |
| Unemployment | 585 | 7.14% |
| IsHoliday | 0 | 0.00% |

## Relationship and Join Validation

| Relationship | Join Key | Expected Cardinality | Rows Before | Rows After | Missing Matches |
| --- | --- | --- | --- | --- | --- |
| department → fact | Store + Date | many-to-one | 421,570 | 421,570 | 0 |
| department store/dept → stores | Store | many-to-one | 3,331 | 3,331 | 0 |

- Unique Store + Date keys in department.csv: **6,435**
- Unique Store + Date keys in fact.csv: **8,190**
- Department Store + Date keys without fact context: **0**
- Fact Store + Date keys without department sales: **1,755**
- Date range for fact-only keys: **2012-11-02** through **2013-07-26**
- Holiday mismatches between department.csv and fact.csv: **0**
- Inconsistent IsHoliday values within a Store + Date in department.csv: **0**
- Dates with inconsistent IsHoliday values across stores: **0**

## Modeling Conclusions

1. `department.csv` is the driving weekly-sales source.
2. The final fact grain is one row per `Store + Dept + Date + version`.
3. Join department sales to fact context using `Store + Date` with a many-to-one relationship.
4. Use a left join from department sales to fact context so sales rows remain authoritative.
5. Build the store dimension at the `Store + Dept` grain by joining distinct department keys to stores on `Store`.
6. Build the date dimension at one row per date. `IsHoliday` is consistent at the date grain in the supplied data.
7. Preserve negative and zero weekly sales until a business definition confirms whether they are adjustments, returns, or errors.
8. Markdown, CPI, and unemployment nulls require explicit transformation decisions rather than silent deletion.

## Proposed Date Key

Use an integer `YYYYMMDD` key, such as `2010-02-05 → 20100205`. This is deterministic, readable, and stable when older dates are added.
