# Retail Intelligence Platform

[![CI](https://github.com/amir-ai-bot/retail-intelligence-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/amir-ai-bot/retail-intelligence-platform/actions/workflows/ci.yml)

Retail Intelligence Platform is a data engineering and analytics portfolio project for retail sales analysis. It shows how raw CSV datasets can be cleaned with Python, loaded into PostgreSQL, modeled with SQL, and prepared for Power BI dashboards, forecasting, and API access.

The project is intentionally practical: it focuses on repeatable data preparation, clear warehouse layers, documented SQL logic, and a small FastAPI surface for serving metrics.

## What This Project Demonstrates

| Area | Evidence in this repository |
| --- | --- |
| Python data pipelines | Cleaning, validation, loading, and baseline forecasting scripts in `src/` |
| SQL and PostgreSQL | Raw, staging, warehouse, and mart schemas under `sql/` |
| Business intelligence | Dashboard-ready marts and KPI queries for Power BI |
| Backend systems | FastAPI endpoints for health checks and retail metrics |
| Machine learning | Baseline weekly sales forecasting workflow |
| Documentation | Architecture notes, data dictionary, staging models, and cleaning log |

## Business Questions

The project is designed around retail questions that are useful for BI and analytics:

- What are the main revenue, order, customer, product, and store trends?
- Which products, departments, stores, and countries contribute most to sales?
- How do holiday periods and time patterns affect weekly sales?
- What cleaned data can support dashboards, forecasting, and backend APIs?

## Architecture

```text
Kaggle CSV files
      |
      v
Python cleaning pipeline
      |
      v
PostgreSQL raw schema
      |
      v
PostgreSQL staging schema
      |
      v
warehouse dimensions and facts
      |
      v
dashboard/API/ML marts
      |
      +--> Power BI
      +--> FastAPI
      `--> Forecasting scripts
```

## Repository Structure

```text
retail-intelligence-platform/
|-- airflow/        # Optional orchestration DAG
|-- api/            # FastAPI service for selected metrics
|-- data/           # Local-only raw and processed datasets
|-- docs/           # Architecture and data documentation
|-- notebooks/      # Exploration and modeling notebooks
|-- screenshots/    # Dashboard and output screenshots
|-- sql/            # PostgreSQL schemas, staging models, marts, KPIs
|-- src/            # Python ETL and forecasting scripts
|-- docker-compose.yml
|-- requirements.txt
`-- README.md
```

## Data Sources

This project is designed for local Kaggle downloads. Large datasets are not committed to GitHub.

Expected local layout:

```text
data/
|-- raw/
|   |-- archive/OnlineRetail.csv
|   `-- walmart-recruiting-store-sales-forecasting/
|-- processed/
`-- external/
```

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Start PostgreSQL locally:

```bash
docker compose up -d postgres
```

Create a local `.env` file from `.env.example`:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=retail_warehouse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

## Run The Pipeline

Clean local CSV files:

```bash
python src/transform.py
```

Load cleaned outputs into PostgreSQL:

```bash
python src/load_to_postgres.py
```

Create staging tables:

```bash
psql -h localhost -p 5432 -U postgres -d retail_warehouse -f sql/02_create_staging_tables.sql
```

Create warehouse tables, marts, and KPI views:

```bash
psql -h localhost -p 5432 -U postgres -d retail_warehouse -f sql/create_tables.sql
psql -h localhost -p 5432 -U postgres -d retail_warehouse -f sql/views.sql
```

Run the API:

```bash
uvicorn api.main:app --reload
```

Train a baseline forecasting model:

```bash
python src/train_model.py
python src/predict.py
```

## Current Capabilities

- Cleans Online Retail and Walmart sales datasets.
- Produces cleaned CSV outputs and a data quality report.
- Loads processed files into PostgreSQL.
- Builds typed staging tables with documented transformation rules.
- Defines a star-schema direction for warehouse modeling.
- Provides SQL marts and KPI queries for dashboard consumption.
- Exposes selected metrics through FastAPI.
- Includes a baseline forecasting workflow for Walmart weekly sales.

## Notes For Reviewers

The repository is designed as a portfolio project, so it favors clarity over excessive infrastructure. The code avoids hard-coded database credentials, keeps large files out of Git, and documents the assumptions behind each data layer.

The intended profile signal is a junior engineer who can connect Python, SQL, PostgreSQL, BI, and backend basics into one organized project.
