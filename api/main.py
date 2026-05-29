from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.load_to_postgres import PostgresConfig, load_local_env


PROJECT_ROOT = Path(__file__).resolve().parents[1]

app = FastAPI(
    title="Retail Intelligence API",
    description="Small API layer for selected retail warehouse metrics.",
    version="0.1.0",
)


def get_engine() -> Engine:
    load_local_env(PROJECT_ROOT / ".env")
    config = PostgresConfig.from_env()
    return create_engine(config.sqlalchemy_url(), pool_pre_ping=True)


@contextmanager
def db_connection():
    try:
        engine = get_engine()
        with engine.connect() as connection:
            yield connection
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


def fetch_one(query: str) -> dict[str, Any]:
    with db_connection() as connection:
        row = connection.execute(text(query)).mappings().first()
    return dict(row or {})


def fetch_all(query: str) -> list[dict[str, Any]]:
    with db_connection() as connection:
        rows = connection.execute(text(query)).mappings().all()
    return [dict(row) for row in rows]


@app.get("/health")
def health() -> dict[str, str]:
    with db_connection() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/metrics/sales-overview")
def sales_overview() -> dict[str, Any]:
    return fetch_one(
        """
        SELECT
            COALESCE(SUM(sales_amount), 0)::numeric(14, 2) AS total_sales,
            COUNT(*)::integer AS sales_rows,
            COUNT(DISTINCT customer_key)::integer AS customers,
            COUNT(DISTINCT product_key)::integer AS products
        FROM warehouse.fact_sales
        """
    )


@app.get("/metrics/monthly-sales")
def monthly_sales() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            d.year,
            d.month,
            COALESCE(SUM(f.sales_amount), 0)::numeric(14, 2) AS sales_amount
        FROM warehouse.fact_sales f
        JOIN warehouse.dim_date d ON d.date_key = f.date_key
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
        """
    )


@app.get("/metrics/top-products")
def top_products(limit: int = 10) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 50))
    return fetch_all(
        f"""
        SELECT
            product_name,
            source_system,
            COALESCE(SUM(sales_amount), 0)::numeric(14, 2) AS sales_amount
        FROM marts.product_performance
        GROUP BY product_name, source_system
        ORDER BY sales_amount DESC
        LIMIT {safe_limit}
        """
    )
