-- Create PostgreSQL staging tables for the Retail Intelligence Platform.
-- Run from the repository root with:
-- psql -h localhost -p 5432 -U postgres -d retail_warehouse -f sql/02_create_staging_tables.sql

CREATE SCHEMA IF NOT EXISTS staging;

\echo 'Creating staging.stg_online_retail_transactions'
\i sql/staging/stg_online_retail_transactions.sql

\echo 'Creating staging.stg_walmart_sales'
\i sql/staging/stg_walmart_sales.sql

\echo 'Creating staging.stg_walmart_stores'
\i sql/staging/stg_walmart_stores.sql

\echo 'Creating staging.stg_walmart_features'
\i sql/staging/stg_walmart_features.sql
