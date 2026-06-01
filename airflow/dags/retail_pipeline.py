from __future__ import annotations

from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_ROOT = Path(__file__).resolve().parents[2]

default_args = {
    "owner": "retail-intelligence-platform",
    "depends_on_past": False,
}

with DAG(
    dag_id="retail_intelligence_pipeline",
    description="Clean retail CSV files, load PostgreSQL, and refresh SQL models.",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["retail", "postgres", "analytics"],
) as dag:
    clean_data = BashOperator(
        task_id="clean_data",
        bash_command=f"cd {PROJECT_ROOT.as_posix()} && python src/transform.py",
    )

    load_raw_tables = BashOperator(
        task_id="load_raw_tables",
        bash_command=f"cd {PROJECT_ROOT.as_posix()} && python src/load_to_postgres.py",
    )

    refresh_staging = BashOperator(
        task_id="refresh_staging",
        bash_command=(
            f"cd {PROJECT_ROOT.as_posix()} && "
            "psql -h ${POSTGRES_HOST:-localhost} "
            "-p ${POSTGRES_PORT:-5432} "
            "-U ${POSTGRES_USER:-postgres} "
            "-d ${POSTGRES_DB:-retail_warehouse} "
            "-f sql/02_create_staging_tables.sql"
        ),
    )

    refresh_warehouse = BashOperator(
        task_id="refresh_warehouse",
        bash_command=(
            f"cd {PROJECT_ROOT.as_posix()} && "
            "psql -h ${POSTGRES_HOST:-localhost} "
            "-p ${POSTGRES_PORT:-5432} "
            "-U ${POSTGRES_USER:-postgres} "
            "-d ${POSTGRES_DB:-retail_warehouse} "
            "-f sql/03_create_warehouse_tables.sql"
        ),
    )

    clean_data >> load_raw_tables >> refresh_staging >> refresh_warehouse
