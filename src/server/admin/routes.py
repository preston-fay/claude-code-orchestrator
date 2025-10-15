"""
Admin dashboard routes for Kearney Data Platform.

Provides HTMX-powered server-rendered admin interface with:
- KPI dashboard with cleanliness score and query metrics
- SQL console with allowlist, row limits, and CSV export
- Artifacts browser for downloading run outputs
"""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import io
import csv

# Import warehouse from parent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.data.warehouse import DuckDBWarehouse, QueryNotAllowed, QueryTimeout

# Import ops modules for metrics
try:
    from src.ops.metrics import get_metrics
    from src.data.cache import get_cache
    from src.ops.logging import get_logger
    logger = get_logger("admin")
    HAS_OPS = True
except ImportError:
    logger = None
    HAS_OPS = False

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Constants
MAX_ROWS = 1000
DEFAULT_TIMEOUT = 3


def get_warehouse() -> DuckDBWarehouse:
    """Get warehouse instance."""
    return DuckDBWarehouse(db_path=":memory:", timeout_seconds=DEFAULT_TIMEOUT)


def format_size(bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def parse_prometheus_metrics(metrics_text: bytes) -> Dict[str, Any]:
    """
    Parse Prometheus metrics text format into structured data.

    Returns dict with:
    - http_requests_total: total requests
    - http_request_latency_p95: p95 latency in seconds
    - cache_hits: total cache hits
    - cache_misses: total cache misses
    - recent_errors: list of recent errors (placeholder)
    """
    result = {
        "http_requests_total": 0,
        "http_request_latency_p95": 0.0,
        "cache_hits": 0,
        "cache_misses": 0,
        "orchestrator_phases": {},
        "recent_errors": [],
    }

    try:
        lines = metrics_text.decode("utf-8").split("\n")

        for line in lines:
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse metric lines: metric_name{labels} value
            if "http_requests_total" in line and "{" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        result["http_requests_total"] += float(parts[-1])
                    except ValueError:
                        pass

            elif "http_request_latency_seconds" in line and "quantile=\"0.95\"" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        result["http_request_latency_p95"] = float(parts[-1])
                    except ValueError:
                        pass

            elif "cache_hits_total" in line and "{" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        result["cache_hits"] += float(parts[-1])
                    except ValueError:
                        pass

            elif "cache_misses_total" in line and "{" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        result["cache_misses"] += float(parts[-1])
                    except ValueError:
                        pass

            elif "orchestrator_phase_seconds" in line and "phase=" in line:
                # Extract phase name and value
                if "{" in line:
                    phase_start = line.find('phase="') + 7
                    phase_end = line.find('"', phase_start)
                    if phase_start > 6 and phase_end > phase_start:
                        phase = line[phase_start:phase_end]
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                # Store as average (simplified)
                                result["orchestrator_phases"][phase] = float(parts[-1])
                            except ValueError:
                                pass

    except Exception as e:
        if logger:
            logger.warning("Failed to parse metrics", error=str(e))

    return result


def get_ops_metrics() -> Dict[str, Any]:
    """
    Get ops metrics for admin dashboard.

    Returns:
    - request_rate_sparkline: list of recent request counts (last 10 minutes, 1min buckets)
    - p95_latency_sparkline: list of recent p95 latencies
    - orchestrator_phase_durations: dict of phase -> duration
    - cache_hit_ratio: float 0-1
    - recent_warnings: list of recent warnings with trace IDs
    """
    if not HAS_OPS:
        return {
            "request_rate_sparkline": [0] * 10,
            "p95_latency_sparkline": [0.0] * 10,
            "orchestrator_phase_durations": {},
            "cache_hit_ratio": 0.0,
            "recent_warnings": [],
        }

    # Get current metrics snapshot
    try:
        metrics_bytes = get_metrics()
        metrics = parse_prometheus_metrics(metrics_bytes)

        # Get cache stats
        cache = get_cache()
        cache_stats = cache.get_stats()

        # Calculate cache hit ratio
        total_cache_ops = metrics["cache_hits"] + metrics["cache_misses"]
        cache_hit_ratio = metrics["cache_hits"] / total_cache_ops if total_cache_ops > 0 else 0.0

        # Generate sparklines (simplified - in production, store historical data)
        # For now, use mock data that varies slightly
        import random
        request_rate_sparkline = [int(metrics["http_requests_total"] * random.uniform(0.05, 0.15)) for _ in range(10)]
        p95_latency_sparkline = [metrics["http_request_latency_p95"] * random.uniform(0.8, 1.2) for _ in range(10)]

        return {
            "request_rate_sparkline": request_rate_sparkline,
            "p95_latency_sparkline": p95_latency_sparkline,
            "orchestrator_phase_durations": metrics["orchestrator_phases"],
            "cache_hit_ratio": cache_hit_ratio,
            "cache_stats": cache_stats,
            "recent_warnings": [
                {"timestamp": "2 min ago", "message": "High latency detected", "trace_id": "a1b2c3d4"},
                {"timestamp": "15 min ago", "message": "Cache miss rate elevated", "trace_id": "e5f6g7h8"},
            ],
        }

    except Exception as e:
        if logger:
            logger.error("Failed to get ops metrics", error=str(e))
        return {
            "request_rate_sparkline": [0] * 10,
            "p95_latency_sparkline": [0.0] * 10,
            "orchestrator_phase_durations": {},
            "cache_hit_ratio": 0.0,
            "recent_warnings": [],
        }


def generate_sparkline_svg(values: List[float], width: int = 100, height: int = 30, color: str = "#7823DC") -> str:
    """
    Generate inline SVG sparkline (NO GRIDLINES per Kearney brand).

    Args:
        values: List of numeric values
        width: SVG width in pixels
        height: SVG height in pixels
        color: Line color (hex)

    Returns:
        SVG markup as string
    """
    if not values or len(values) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'

    # Normalize values to 0-1 range
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1.0

    normalized = [(v - min_val) / val_range for v in values]

    # Generate points
    x_step = width / (len(values) - 1)
    points = []
    for i, val in enumerate(normalized):
        x = i * x_step
        y = height - (val * height * 0.9)  # Leave 10% padding
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)

    # SVG with no gridlines, clean line
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

    return svg


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    GET /admin - Main dashboard with KPIs and recent activity.

    Shows:
    - Cleanliness score with trend
    - Total queries and avg query time
    - Last run ID and timestamp
    - 7-day query activity sparkline (NO GRIDLINES)
    - Recent tables
    - Ops readouts: request rate, p95 latency, orchestrator phases, cache hit ratio, recent warnings
    """
    # Mock KPI data (replace with real metrics)
    cleanliness_score = 85
    cleanliness_trend = 5
    total_queries = 1234
    avg_query_time_ms = 45
    query_time_trend = -5
    last_run_id = "run_20251015_123456"
    last_run_time = "2 hours ago"

    # 7-day query history (mock)
    query_history = [120, 150, 180, 140, 200, 170, 190]
    max_queries = max(query_history)
    days_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Recent tables (mock)
    recent_tables = [
        {"name": "customers", "row_count": "1.2M", "size": "45 MB", "updated": "2 hours ago"},
        {"name": "orders", "row_count": "3.5M", "size": "120 MB", "updated": "5 hours ago"},
        {"name": "products", "row_count": "50K", "size": "8 MB", "updated": "1 day ago"},
    ]

    # Get ops metrics
    ops_metrics = get_ops_metrics()

    # Generate sparklines for ops metrics
    request_rate_svg = generate_sparkline_svg(ops_metrics["request_rate_sparkline"], width=150, height=40, color="#7823DC")
    p95_latency_svg = generate_sparkline_svg(ops_metrics["p95_latency_sparkline"], width=150, height=40, color="#E63946")

    # Format cache hit ratio as percentage
    cache_hit_ratio_pct = ops_metrics["cache_hit_ratio"] * 100

    return templates.TemplateResponse("index.html", {
        "request": request,
        "cleanliness_score": cleanliness_score,
        "cleanliness_trend": cleanliness_trend,
        "total_queries": total_queries,
        "avg_query_time_ms": avg_query_time_ms,
        "query_time_trend": query_time_trend,
        "last_run_id": last_run_id,
        "last_run_time": last_run_time,
        "query_history": query_history,
        "max_queries": max_queries,
        "days_labels": days_labels,
        "recent_tables": recent_tables,
        # Ops metrics
        "request_rate_svg": request_rate_svg,
        "p95_latency_svg": p95_latency_svg,
        "p95_latency_ms": ops_metrics["p95_latency_sparkline"][-1] * 1000 if ops_metrics["p95_latency_sparkline"] else 0,
        "orchestrator_phases": ops_metrics["orchestrator_phase_durations"],
        "cache_hit_ratio": cache_hit_ratio_pct,
        "cache_stats": ops_metrics.get("cache_stats", {}),
        "recent_warnings": ops_metrics["recent_warnings"],
        "has_ops": HAS_OPS,
    })


@router.get("/admin/sql", response_class=HTMLResponse)
async def sql_console_get(request: Request):
    """
    GET /admin/sql - SQL console form.

    Shows:
    - SQL textarea with allowlist notice
    - Row limit and timeout inputs
    - Available tables list
    """
    wh = get_warehouse()

    # Get available tables
    try:
        result = wh.query("SELECT name FROM sqlite_master WHERE type='table'", check_allowlist=False)
        tables = [row[0] for row in result.fetchall()]
    except:
        tables = []

    return templates.TemplateResponse("sql.html", {
        "request": request,
        "max_rows": MAX_ROWS,
        "tables": tables,
    })


@router.post("/admin/sql", response_class=HTMLResponse)
async def sql_console_post(
    request: Request,
    sql: str = Form(...),
    limit: int = Form(MAX_ROWS),
    timeout: int = Form(DEFAULT_TIMEOUT),
    export: Optional[str] = Form(None)
):
    """
    POST /admin/sql - Execute SQL query with safety guards.

    Args:
        sql: SQL query (SELECT/WITH only)
        limit: Row limit (max MAX_ROWS)
        timeout: Query timeout in seconds (max 10)
        export: If 'csv', return CSV download

    Returns:
        HTML with results table or CSV download

    Safety:
        - Allowlist check (SELECT/WITH only)
        - Row limit enforcement
        - Timeout protection
    """
    wh = get_warehouse()

    # Get available tables
    try:
        table_result = wh.query("SELECT name FROM sqlite_master WHERE type='table'", check_allowlist=False)
        tables = [row[0] for row in table_result.fetchall()]
    except:
        tables = []

    # Enforce limits
    limit = min(limit, MAX_ROWS)
    timeout = min(timeout, 10)

    # Add LIMIT if not present
    sql_with_limit = sql.strip()
    if "LIMIT" not in sql_with_limit.upper():
        sql_with_limit += f" LIMIT {limit}"

    try:
        start_time = time.time()
        result = wh.query(sql_with_limit, timeout=timeout)
        execution_time = int((time.time() - start_time) * 1000)

        columns = [desc[0] for desc in result.description] if result.description else []
        rows = result.fetchall()
        row_count = len(rows)
        has_more = row_count >= limit

        # CSV export
        if export == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)

            csv_content = output.getvalue()
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=query_results_{int(time.time())}.csv"}
            )

        # HTML response
        return templates.TemplateResponse("sql.html", {
            "request": request,
            "max_rows": MAX_ROWS,
            "sql": sql,
            "limit": limit,
            "timeout": timeout,
            "tables": tables,
            "results": {
                "columns": columns,
                "rows": rows,
                "row_count": row_count,
                "execution_time_ms": execution_time,
                "has_more": has_more,
            }
        })

    except QueryNotAllowed as e:
        return templates.TemplateResponse("sql.html", {
            "request": request,
            "max_rows": MAX_ROWS,
            "sql": sql,
            "limit": limit,
            "timeout": timeout,
            "tables": tables,
            "error": f"Query not allowed: {str(e)}. Only SELECT and WITH queries are permitted."
        })

    except QueryTimeout as e:
        return templates.TemplateResponse("sql.html", {
            "request": request,
            "max_rows": MAX_ROWS,
            "sql": sql,
            "limit": limit,
            "timeout": timeout,
            "tables": tables,
            "error": f"Query timeout: {str(e)}"
        })

    except Exception as e:
        return templates.TemplateResponse("sql.html", {
            "request": request,
            "max_rows": MAX_ROWS,
            "sql": sql,
            "limit": limit,
            "timeout": timeout,
            "tables": tables,
            "error": f"Query error: {str(e)}"
        })


@router.get("/admin/artifacts", response_class=HTMLResponse)
async def artifacts_browser(request: Request):
    """
    GET /admin/artifacts - Browse artifacts by run ID.

    Shows:
    - List of run IDs
    - Artifacts per run with sizes and download links
    - Storage summary
    """
    artifacts_dir = Path("artifacts")

    if not artifacts_dir.exists():
        return templates.TemplateResponse("artifacts.html", {
            "request": request,
            "run_ids": [],
            "artifacts": {},
            "total_artifacts": 0,
            "total_size": "0 B",
        })

    # Scan artifacts directory
    run_ids = []
    artifacts = {}
    total_artifacts = 0
    total_bytes = 0

    for run_dir in sorted(artifacts_dir.iterdir(), reverse=True):
        if run_dir.is_dir():
            run_id = run_dir.name
            run_ids.append(run_id)
            artifacts[run_id] = []

            for artifact_file in run_dir.iterdir():
                if artifact_file.is_file():
                    size = artifact_file.stat().st_size
                    total_bytes += size
                    total_artifacts += 1

                    artifacts[run_id].append({
                        "name": artifact_file.name,
                        "size": format_size(size),
                        "type": artifact_file.suffix.upper().replace('.', '') or "FILE",
                    })

    return templates.TemplateResponse("artifacts.html", {
        "request": request,
        "run_ids": run_ids,
        "artifacts": artifacts,
        "total_artifacts": total_artifacts,
        "total_size": format_size(total_bytes),
    })


@router.get("/admin/artifacts/{run_id}/{filename}")
async def download_artifact(run_id: str, filename: str):
    """
    GET /admin/artifacts/{run_id}/{filename} - Download artifact file.

    Args:
        run_id: Run ID directory name
        filename: Artifact filename

    Returns:
        File download response

    Security:
        - Path traversal prevention
        - File existence check
    """
    # Prevent path traversal
    if ".." in run_id or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid path")

    artifact_path = Path("artifacts") / run_id / filename

    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")

    return StreamingResponse(
        open(artifact_path, "rb"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
