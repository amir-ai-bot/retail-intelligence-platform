# Data Dictionary

This document will describe the cleaned datasets used in the Retail Intelligence Platform.

## Online Retail Dataset

| Column | Type | Description | Cleaning Notes |
| --- | --- | --- | --- |
| `invoice_no` | string | Transaction invoice number | Cancelled invoices removed |
| `stock_code` | string | Product identifier | Required field |
| `description` | string | Product description | Standardized text formatting |
| `quantity` | integer | Units purchased | Must be positive |
| `invoice_date` | datetime | Transaction timestamp | Parsed to datetime |
| `unit_price` | float | Unit price | Must be positive |
| `customer_id` | integer | Customer identifier | Missing customers removed |
| `country` | string | Customer country | Required field |
| `total_sales` | float | `quantity * unit_price` | Derived metric |

## Walmart Sales Forecasting Dataset

Document final feature definitions here after modeling tables are finalized.
