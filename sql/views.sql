-- Dashboard-ready marts built from warehouse tables.

CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE VIEW marts.sales_overview AS
SELECT
    d.year,
    d.month,
    d.month_name,
    f.source_system,
    COUNT(*) AS sales_rows,
    COUNT(DISTINCT f.invoice_no) FILTER (WHERE f.invoice_no IS NOT NULL) AS invoice_count,
    SUM(COALESCE(f.quantity, 0)) AS units_sold,
    SUM(COALESCE(f.sales_amount, 0))::numeric(14, 2) AS sales_amount
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d ON d.date_key = f.date_key
GROUP BY d.year, d.month, d.month_name, f.source_system;

CREATE OR REPLACE VIEW marts.product_performance AS
SELECT
    p.product_key,
    p.product_code,
    p.product_name,
    p.department_id,
    p.source_system,
    COUNT(*) AS sales_rows,
    SUM(COALESCE(f.quantity, 0)) AS units_sold,
    SUM(COALESCE(f.sales_amount, 0))::numeric(14, 2) AS sales_amount
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p ON p.product_key = f.product_key
GROUP BY
    p.product_key,
    p.product_code,
    p.product_name,
    p.department_id,
    p.source_system;

CREATE OR REPLACE VIEW marts.customer_performance AS
SELECT
    c.customer_key,
    c.customer_id,
    c.country,
    c.source_system,
    COUNT(DISTINCT f.invoice_no) FILTER (WHERE f.invoice_no IS NOT NULL) AS invoice_count,
    COUNT(*) AS sales_rows,
    SUM(COALESCE(f.sales_amount, 0))::numeric(14, 2) AS sales_amount
FROM warehouse.fact_sales f
JOIN warehouse.dim_customer c ON c.customer_key = f.customer_key
GROUP BY c.customer_key, c.customer_id, c.country, c.source_system;

CREATE OR REPLACE VIEW marts.store_performance AS
SELECT
    s.store_key,
    s.store_id,
    s.store_type,
    s.store_size,
    s.source_system,
    COUNT(*) AS sales_rows,
    SUM(COALESCE(f.sales_amount, 0))::numeric(14, 2) AS sales_amount,
    CASE
        WHEN s.store_size IS NULL OR s.store_size = 0 THEN NULL
        ELSE ROUND(SUM(COALESCE(f.sales_amount, 0)) / s.store_size, 4)
    END AS sales_per_store_size
FROM warehouse.fact_sales f
JOIN warehouse.dim_store s ON s.store_key = f.store_key
GROUP BY s.store_key, s.store_id, s.store_type, s.store_size, s.source_system;

CREATE OR REPLACE VIEW marts.forecasting_features AS
SELECT
    w.walmart_sales_id,
    w.store_id,
    w.department_id,
    w.sales_date,
    d.year,
    d.month,
    d.week_of_year,
    w.is_holiday,
    st.store_type,
    st.store_size,
    ft.temperature,
    ft.fuel_price,
    ft.markdown_1,
    ft.markdown_2,
    ft.markdown_3,
    ft.markdown_4,
    ft.markdown_5,
    ft.cpi,
    ft.unemployment_rate,
    w.weekly_sales_amount
FROM staging.stg_walmart_sales w
JOIN warehouse.dim_date d
  ON d.date = w.sales_date
LEFT JOIN staging.stg_walmart_stores st
  ON st.store_id = w.store_id
LEFT JOIN staging.stg_walmart_features ft
  ON ft.store_id = w.store_id
 AND ft.feature_date = w.sales_date;
