from __future__ import annotations

import html
import json
from datetime import date, datetime
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import psycopg2
from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 8000


def load_env() -> dict[str, str]:
    env_path = PROJECT_ROOT / ".env"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


ENV = load_env()


def db_rows(sql: str, params: dict[str, object] | None = None) -> list[dict[str, object]]:
    connection = psycopg2.connect(
        host=ENV.get("POSTGRES_HOST", "localhost"),
        port=ENV.get("POSTGRES_PORT", "5432"),
        dbname=ENV.get("POSTGRES_DB", "retail_warehouse"),
        user=ENV.get("POSTGRES_USER", "postgres"),
        password=ENV.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params or {})
            return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def convert_json(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def render_home() -> str:
    counts = db_rows(
        """
        SELECT 'warehouse.fact_sales' AS object_name, COUNT(*) AS row_count
        FROM warehouse.fact_sales
        UNION ALL
        SELECT 'marts.forecasting_base', COUNT(*)
        FROM marts.forecasting_base
        UNION ALL
        SELECT 'marts.sales_overview', COUNT(*)
        FROM marts.sales_overview
        ORDER BY object_name
        """
    )
    overview = db_rows(
        """
        SELECT
            ROUND(SUM(total_revenue), 2) AS total_revenue,
            SUM(total_orders)::integer AS total_orders,
            ROUND(SUM(total_revenue) / NULLIF(SUM(total_orders), 0), 2) AS average_order_value
        FROM marts.sales_overview
        """
    )[0]

    rows_html = "\n".join(
        f"<tr><td>{html.escape(str(row['object_name']))}</td><td>{int(row['row_count']):,}</td></tr>"
        for row in counts
    )

    total_revenue = float(overview["total_revenue"] or 0)
    total_orders = int(overview["total_orders"] or 0)
    average_order_value = float(overview["average_order_value"] or 0)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Retail Intelligence Platform</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 40px; color: #17202a; line-height: 1.45; }}
    a {{ color: #075985; }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 4px; }}
    table {{ border-collapse: collapse; margin-top: 12px; }}
    td, th {{ border: 1px solid #ccd6e0; padding: 8px 12px; text-align: left; }}
    .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }}
    .card {{ border: 1px solid #ccd6e0; border-radius: 8px; padding: 14px 18px; min-width: 180px; background: #f8fafc; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
  </style>
</head>
<body>
  <h1>Retail Intelligence Platform</h1>
  <p>The project is running locally against PostgreSQL.</p>
  <div class="cards">
    <div class="card"><div>Total Revenue</div><div class="value">{total_revenue:,.2f}</div></div>
    <div class="card"><div>Total Orders</div><div class="value">{total_orders:,}</div></div>
    <div class="card"><div>Average Order Value</div><div class="value">{average_order_value:,.2f}</div></div>
  </div>
  <h2>Verified Objects</h2>
  <table>
    <tr><th>Object</th><th>Rows</th></tr>
    {rows_html}
  </table>
  <h2>Live Endpoints</h2>
  <ul>
    <li><a href="/health">/health</a></li>
    <li><a href="/sales-overview">/sales-overview</a></li>
    <li><a href="/top-products?limit=10">/top-products?limit=10</a></li>
    <li><a href="/store-performance?limit=20">/store-performance?limit=20</a></li>
  </ul>
  <p>FastAPI can replace this preview after dependencies install successfully with <code>pip install -r requirements.txt</code>.</p>
</body>
</html>"""


class PreviewHandler(BaseHTTPRequestHandler):
    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, default=convert_json, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, payload: str, status: int = 200) -> None:
        body = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path in {"/", "/index.html"}:
                self.send_html(render_home())
                return

            if parsed.path == "/health":
                row = db_rows("SELECT current_database() AS database_name")[0]
                self.send_json({"status": "ok", "database": row["database_name"]})
                return

            if parsed.path == "/sales-overview":
                row = db_rows(
                    """
                    SELECT
                        ROUND(SUM(total_revenue), 2) AS total_revenue,
                        SUM(total_orders)::integer AS total_orders,
                        ROUND(SUM(total_quantity), 2) AS total_quantity,
                        ROUND(SUM(total_revenue) / NULLIF(SUM(total_orders), 0), 2) AS average_order_value,
                        COUNT(*)::integer AS monthly_rows
                    FROM marts.sales_overview
                    """
                )[0]
                self.send_json(row)
                return

            if parsed.path == "/top-products":
                limit = int(parse_qs(parsed.query).get("limit", ["10"])[0])
                limit = max(1, min(limit, 50))
                rows = db_rows(
                    """
                    SELECT
                        product_name,
                        source_system,
                        sales_rows,
                        quantity_sold,
                        total_revenue,
                        revenue_rank,
                        performance_band
                    FROM marts.product_performance
                    ORDER BY total_revenue DESC, product_name
                    LIMIT %(limit)s
                    """,
                    {"limit": limit},
                )
                self.send_json(rows)
                return

            if parsed.path == "/store-performance":
                limit = int(parse_qs(parsed.query).get("limit", ["20"])[0])
                limit = max(1, min(limit, 100))
                rows = db_rows(
                    """
                    SELECT
                        store_id,
                        store_name,
                        store_type,
                        store_size,
                        source_system,
                        sales_rows,
                        total_revenue,
                        holiday_revenue,
                        non_holiday_revenue,
                        sales_per_store_size,
                        store_revenue_rank
                    FROM marts.store_performance
                    ORDER BY total_revenue DESC, store_reference
                    LIMIT %(limit)s
                    """,
                    {"limit": limit},
                )
                self.send_json(rows)
                return

            self.send_json({"detail": "Not found"}, status=404)
        except Exception as exc:
            self.send_json({"status": "error", "detail": str(exc)}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), PreviewHandler)
    print(f"Preview server running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
