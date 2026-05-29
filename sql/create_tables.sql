-- Build warehouse dimensions and fact tables from typed staging models.
-- Run after sql/02_create_staging_tables.sql.

CREATE SCHEMA IF NOT EXISTS warehouse;

DROP TABLE IF EXISTS warehouse.fact_sales;
DROP TABLE IF EXISTS warehouse.dim_date;
DROP TABLE IF EXISTS warehouse.dim_product;
DROP TABLE IF EXISTS warehouse.dim_customer;
DROP TABLE IF EXISTS warehouse.dim_store;

CREATE TABLE warehouse.dim_date AS
WITH dates AS (
    SELECT DISTINCT invoice_date AS date_value
    FROM staging.stg_online_retail_transactions
    UNION
    SELECT DISTINCT sales_date AS date_value
    FROM staging.stg_walmart_sales
)
SELECT
    TO_CHAR(date_value, 'YYYYMMDD')::integer AS date_key,
    date_value::date AS date,
    EXTRACT(DAY FROM date_value)::integer AS day_of_month,
    EXTRACT(ISODOW FROM date_value)::integer AS day_of_week,
    TO_CHAR(date_value, 'Day') AS day_name,
    EXTRACT(WEEK FROM date_value)::integer AS week_of_year,
    EXTRACT(MONTH FROM date_value)::integer AS month,
    TO_CHAR(date_value, 'Month') AS month_name,
    EXTRACT(QUARTER FROM date_value)::integer AS quarter,
    EXTRACT(YEAR FROM date_value)::integer AS year,
    CASE WHEN EXTRACT(ISODOW FROM date_value) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM dates
WHERE date_value IS NOT NULL;

ALTER TABLE warehouse.dim_date ADD PRIMARY KEY (date_key);

CREATE TABLE warehouse.dim_product AS
WITH products AS (
    SELECT DISTINCT
        stock_code AS product_code,
        product_description AS product_name,
        NULL::integer AS department_id,
        'online_retail'::text AS source_system
    FROM staging.stg_online_retail_transactions
    UNION
    SELECT DISTINCT
        department_id::text AS product_code,
        CONCAT('Department ', department_id::text) AS product_name,
        department_id,
        'walmart'::text AS source_system
    FROM staging.stg_walmart_sales
)
SELECT
    ROW_NUMBER() OVER (ORDER BY source_system, product_code) AS product_key,
    product_code,
    product_name,
    department_id,
    source_system
FROM products;

ALTER TABLE warehouse.dim_product ADD PRIMARY KEY (product_key);

CREATE TABLE warehouse.dim_customer AS
WITH customers AS (
    SELECT DISTINCT
        customer_id,
        country,
        'online_retail'::text AS source_system
    FROM staging.stg_online_retail_transactions
    UNION
    SELECT
        NULL::integer AS customer_id,
        NULL::text AS country,
        'walmart'::text AS source_system
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY source_system, customer_id NULLS FIRST, country NULLS FIRST
    ) AS customer_key,
    customer_id,
    country,
    source_system
FROM customers;

ALTER TABLE warehouse.dim_customer ADD PRIMARY KEY (customer_key);

CREATE TABLE warehouse.dim_store AS
WITH stores AS (
    SELECT
        store_id,
        store_type,
        store_size,
        'walmart'::text AS source_system
    FROM staging.stg_walmart_stores
    UNION
    SELECT
        NULL::integer AS store_id,
        'ONLINE'::text AS store_type,
        NULL::integer AS store_size,
        'online_retail'::text AS source_system
)
SELECT
    ROW_NUMBER() OVER (ORDER BY source_system, store_id NULLS FIRST) AS store_key,
    store_id,
    store_type,
    store_size,
    source_system
FROM stores;

ALTER TABLE warehouse.dim_store ADD PRIMARY KEY (store_key);

CREATE TABLE warehouse.fact_sales AS
WITH online_sales AS (
    SELECT
        t.transaction_line_id AS source_record_id,
        'online_retail'::text AS source_system,
        TO_CHAR(t.invoice_date, 'YYYYMMDD')::integer AS date_key,
        p.product_key,
        c.customer_key,
        s.store_key,
        t.invoice_no,
        NULL::boolean AS is_holiday,
        t.quantity,
        t.unit_price,
        t.sales_amount,
        NULL::numeric(14, 2) AS weekly_sales_amount
    FROM staging.stg_online_retail_transactions t
    JOIN warehouse.dim_product p
      ON p.product_code = t.stock_code
     AND p.source_system = 'online_retail'
    JOIN warehouse.dim_customer c
      ON c.customer_id = t.customer_id
     AND c.country = t.country
     AND c.source_system = 'online_retail'
    JOIN warehouse.dim_store s
      ON s.source_system = 'online_retail'
),
walmart_sales AS (
    SELECT
        w.walmart_sales_id AS source_record_id,
        'walmart'::text AS source_system,
        TO_CHAR(w.sales_date, 'YYYYMMDD')::integer AS date_key,
        p.product_key,
        c.customer_key,
        s.store_key,
        NULL::text AS invoice_no,
        w.is_holiday,
        NULL::integer AS quantity,
        NULL::numeric(12, 4) AS unit_price,
        w.weekly_sales_amount AS sales_amount,
        w.weekly_sales_amount
    FROM staging.stg_walmart_sales w
    JOIN warehouse.dim_product p
      ON p.department_id = w.department_id
     AND p.source_system = 'walmart'
    JOIN warehouse.dim_customer c
      ON c.customer_id IS NULL
     AND c.source_system = 'walmart'
    JOIN warehouse.dim_store s
      ON s.store_id = w.store_id
     AND s.source_system = 'walmart'
    WHERE w.dataset_split = 'train'
)
SELECT
    ROW_NUMBER() OVER (ORDER BY source_system, source_record_id) AS sales_key,
    source_record_id,
    source_system,
    date_key,
    product_key,
    customer_key,
    store_key,
    invoice_no,
    is_holiday,
    quantity,
    unit_price,
    sales_amount,
    weekly_sales_amount
FROM (
    SELECT * FROM online_sales
    UNION ALL
    SELECT * FROM walmart_sales
) combined;

ALTER TABLE warehouse.fact_sales ADD PRIMARY KEY (sales_key);
ALTER TABLE warehouse.fact_sales
    ADD CONSTRAINT fact_sales_date_fk FOREIGN KEY (date_key) REFERENCES warehouse.dim_date(date_key);
ALTER TABLE warehouse.fact_sales
    ADD CONSTRAINT fact_sales_product_fk FOREIGN KEY (product_key) REFERENCES warehouse.dim_product(product_key);
ALTER TABLE warehouse.fact_sales
    ADD CONSTRAINT fact_sales_customer_fk FOREIGN KEY (customer_key) REFERENCES warehouse.dim_customer(customer_key);
ALTER TABLE warehouse.fact_sales
    ADD CONSTRAINT fact_sales_store_fk FOREIGN KEY (store_key) REFERENCES warehouse.dim_store(store_key);
