# ETL Pipeline: Cleaned CSVs to PostgreSQL

## Purpose

This ETL pipeline loads locally cleaned CSV files into PostgreSQL so the project can move from file-based analysis into a structured warehouse workflow.

The current implementation focuses on the first database landing layer: the `raw` schema.

## Flow

```text
data/processed/*.csv
        |
        v
pandas DataFrame
        |
        v
SQLAlchemy engine
        |
        v
PostgreSQL raw schema
```

## Source

The loader automatically detects CSV files in:

```text
data/processed/
```

Each CSV file is loaded into PostgreSQL using a table name derived from the file name.

Examples:

- `online_retail_clean.csv` -> `raw.online_retail_clean`
- `walmart_train_clean.csv` -> `raw.walmart_train_clean`
- `walmart_train_model_ready.csv` -> `raw.walmart_train_model_ready`

## Target Layer

The `raw` schema is the database landing zone for cleaned but source-aligned data.

This layer is intentionally simple:

- One table per CSV file.
- Table names are generated from CSV filenames.
- Tables are replaced on each run with `if_exists="replace"`.
- No business aggregation is applied during loading.

## Configuration

Database credentials are loaded from environment variables.

Create a local `.env` file using `.env.example` as a template:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=retail_warehouse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

The `.env` file must stay local and should not be committed to GitHub.

## Run Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the loader:

```bash
python src/load_to_postgres.py
```

## Operational Notes

- The loader creates the `raw` schema if it does not already exist.
- The script uses clear logging for discovery, loading, row counts, and failures.
- Failed file loads raise an error so the pipeline does not silently hide data problems.
- This phase is designed for development. Later phases can add incremental loads, audit columns, row counts, and data quality checks.
