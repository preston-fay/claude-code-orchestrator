"""FastAPI server with SQL endpoint, metrics, admin dashboard, and Mangum adapter for Lambda."""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from pathlib import Path
import io
import csv
import time as time_module

try:
    from mangum import Mangum
except ImportError:
    Mangum = None

from src.data.warehouse import DuckDBWarehouse, QueryNotAllowed, QueryTimeout
from src.server.admin.routes import router as admin_router
from src.server.theme_routes import router as theme_router
from src.server.registry_routes import router as registry_router
from src.server.gov_routes import router as gov_router
from src.server.iso_providers import get_isochrones

# Ops layer
from src.ops.logging import configure_logging, get_logger, bind_context
from src.ops.tracing import init_tracer, instrument_fastapi, get_current_trace_id
from src.ops.metrics import (
    http_requests_total,
    http_request_latency,
    get_metrics,
    get_content_type,
)

# Security layer
from src.security.context import get_optional_identity, attach_identity_to_request, require_auth, get_tenant_context
from src.security.schemas import Identity, TenantContext, ScopeEnum
from src.security.headers import SecurityHeadersMiddleware
from src.security.ratelimit import is_rate_limited
from src.security.audit import get_audit_logger
from src.security.signing import create_signed_artifact_url

# Configure logging and tracing on startup
configure_logging(json=False, level="INFO")
logger = get_logger(__name__)
init_tracer(service_name="kearney-platform-api")

# Create app
app = FastAPI(
    title="Kearney Data Platform API",
    description="DuckDB warehouse API with allowlisted SQL execution and admin dashboard",
    version="1.0.0",
)

# Instrument with OpenTelemetry
instrument_fastapi(app)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount admin routes
app.include_router(admin_router)

# Mount theme management routes
app.include_router(theme_router)

# Mount registry routes
app.include_router(registry_router)

# Mount governance routes
app.include_router(gov_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


# Request/Response logging middleware with auth and rate limiting
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests and responses with metrics, auth, and rate limiting."""
    start_time = time_module.time()

    # Bind request context
    request_id = request.headers.get("X-Request-ID", "unknown")
    trace_id = get_current_trace_id()
    bind_context(request_id=request_id, trace_id=trace_id, path=request.url.path)

    # Extract and attach identity (optional - non-blocking)
    x_api_key = request.headers.get("X-API-Key")
    authorization = request.headers.get("Authorization")
    identity = await get_optional_identity(x_api_key=x_api_key, authorization=authorization)
    attach_identity_to_request(request, identity)

    # Check rate limiting for authenticated requests
    if identity:
        tenant = request.headers.get("X-Tenant", identity.tenants[0] if identity.tenants else "default")
        is_limited, rate_headers = is_rate_limited(identity, tenant, request.url.path)

        if is_limited:
            # Log rate limit event
            audit_logger = get_audit_logger()
            audit_logger.log_access_denied(
                identity=identity,
                resource_type="api",
                resource_id=request.url.path,
                tenant=tenant,
                reason="rate_limit_exceeded",
                ip_address=request.client.host if request.client else None,
                trace_id=trace_id
            )

            # Return 429 with rate limit headers
            logger.warning(
                "rate_limit_exceeded",
                identity_id=identity.id,
                tenant=tenant,
                path=request.url.path
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please slow down.",
                },
                headers=rate_headers
            )

        # Add rate limit headers to response (done after processing)
        request.state.rate_headers = rate_headers

    # Log request
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None,
        identity=identity.id if identity else None,
    )

    # Process request
    response = await call_next(request)

    # Add rate limit headers if present
    if hasattr(request.state, "rate_headers"):
        for key, value in request.state.rate_headers.items():
            response.headers[key] = value

    # Calculate latency
    latency = time_module.time() - start_time

    # Record metrics
    http_requests_total.labels(
        route=request.url.path, method=request.method, status=response.status_code
    ).inc()
    http_request_latency.labels(route=request.url.path, method=request.method).observe(latency)

    # Log response
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=round(latency * 1000, 2),
        identity=identity.id if identity else None,
    )

    return response


# Warehouse instance
warehouse: Optional[DuckDBWarehouse] = None


def get_warehouse() -> DuckDBWarehouse:
    """Get or create warehouse instance."""
    global warehouse
    if warehouse is None:
        db_path = Path.cwd() / "warehouse" / "analytics.duckdb"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        warehouse = DuckDBWarehouse(db_path, read_only=False, timeout_seconds=30)
        warehouse.connect()
    return warehouse


# Request/Response models
class SQLRequest(BaseModel):
    """SQL query request."""

    sql: str = Field(..., description="SQL query (SELECT, WITH, DESCRIBE only)")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    timeout: Optional[int] = Field(None, description="Timeout in seconds", ge=1, le=300)
    limit: Optional[int] = Field(100, description="Result limit", ge=1, le=10000)
    offset: Optional[int] = Field(0, description="Result offset", ge=0)


class SQLResponse(BaseModel):
    """SQL query response."""

    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    has_more: bool


class MetricsResponse(BaseModel):
    """Metrics response."""

    orchestrator: Optional[Dict[str, Any]] = None
    cleanliness: Optional[Dict[str, Any]] = None
    isochrone: Optional[Dict[str, Any]] = None


# Routes
@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "kearney-data-platform"}


@app.post("/sql", response_model=SQLResponse)
async def execute_sql(request: SQLRequest):
    """
    Execute allowlisted SQL query.

    Allowed operations:
    - SELECT
    - WITH (CTEs)
    - DESCRIBE
    - SHOW
    - EXPLAIN

    Blocked operations:
    - DROP, DELETE, TRUNCATE
    - ALTER, CREATE USER
    - GRANT, REVOKE
    """
    import time

    try:
        wh = get_warehouse()

        start = time.time()

        # Add pagination
        sql_with_limit = request.sql
        if "LIMIT" not in sql_with_limit.upper():
            sql_with_limit += f" LIMIT {request.limit} OFFSET {request.offset}"

        # Execute query
        result = wh.query(sql_with_limit, params=request.params, timeout=request.timeout)

        # Fetch results
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]

        execution_time = (time.time() - start) * 1000

        # Check if there are more rows
        count_sql = f"SELECT COUNT(*) FROM ({request.sql}) AS _count"
        count_result = wh.query(count_sql, params=request.params, check_allowlist=False)
        total_rows = count_result.fetchone()[0]
        has_more = (request.offset + len(rows)) < total_rows

        return SQLResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time,
            has_more=has_more,
        )

    except QueryNotAllowed as e:
        raise HTTPException(status_code=403, detail=str(e))
    except QueryTimeout as e:
        raise HTTPException(status_code=408, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@app.get("/sql/export")
async def export_sql(
    sql: str = Query(..., description="SQL query"),
    format: str = Query("csv", description="Export format (csv or json)"),
):
    """
    Export query results as CSV or JSON.

    Args:
        sql: SQL query
        format: "csv" or "json"

    Returns:
        Streaming response with results
    """
    try:
        wh = get_warehouse()
        result = wh.query(sql, timeout=60)

        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]

        if format == "csv":
            # CSV export
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=export.csv"},
            )

        else:
            # JSON export
            data = [dict(zip(columns, row)) for row in rows]
            return JSONResponse(content={"data": data, "row_count": len(rows)})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Isochrone metrics tracking
_isochrone_requests = 0
_isochrone_latency_sum = 0
_isochrone_latency_count = 0


@app.get("/isochrone")
async def get_isochrone_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    range: int = Query(30, description="Max travel time in minutes", ge=1, le=60),
    buckets: int = Query(3, description="Number of isochrone zones", ge=1, le=4),
    profile: str = Query("driving", description="Travel profile"),
    provider: str = Query("stub", description="Provider (stub, openrouteservice, mapbox)")
):
    """
    Get isochrone polygons for travel time analysis.

    Args:
        lat: Latitude of starting point
        lon: Longitude of starting point
        range: Maximum travel time in minutes (1-60)
        buckets: Number of isochrone zones (1-4)
        profile: Travel profile (driving, walking, cycling)
        provider: Provider name (stub, openrouteservice, mapbox)

    Returns:
        GeoJSON FeatureCollection with isochrone polygons

    Features:
        - Rate limiting (10 req/min default)
        - 5s provider timeout with fallback to stub
        - Environment-based API key configuration
    """
    global _isochrone_requests, _isochrone_latency_sum, _isochrone_latency_count

    start_time = time_module.time()

    try:
        result, rate_limited = get_isochrones(lat, lon, range, buckets, profile, provider)

        latency_ms = int((time_module.time() - start_time) * 1000)
        _isochrone_requests += 1
        _isochrone_latency_sum += latency_ms
        _isochrone_latency_count += 1

        if rate_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "fallback": result,
                    "message": "Using stub data due to rate limit"
                }
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get orchestrator metrics and cleanliness score.

    Returns:
    - Latest orchestrator run metrics
    - Repository cleanliness score
    """
    metrics = {}

    # Orchestrator metrics
    metrics_dir = Path.cwd() / ".claude" / "metrics"
    if metrics_dir.exists():
        metric_files = sorted(metrics_dir.glob("run_*.json"), key=lambda p: p.stat().st_mtime)
        if metric_files:
            with open(metric_files[-1]) as f:
                metrics["orchestrator"] = json.load(f)

    # Cleanliness score
    hygiene_file = Path.cwd() / "reports" / "hygiene_summary.json"
    if hygiene_file.exists():
        with open(hygiene_file) as f:
            metrics["cleanliness"] = json.load(f)

    # Isochrone metrics
    if _isochrone_requests > 0:
        avg_latency = _isochrone_latency_sum / _isochrone_latency_count if _isochrone_latency_count > 0 else 0
        metrics["isochrone"] = {
            "requests_total": _isochrone_requests,
            "latency_ms_avg": round(avg_latency, 2)
        }

    return MetricsResponse(**metrics)


@app.get("/viz/palette")
async def get_viz_palette(theme: str = Query("light", description="Theme: light or dark")):
    """
    Get visualization color palettes for current theme.

    Args:
        theme: "light" or "dark"

    Returns:
        Color palettes and tokens
    """
    tokens_file = Path(__file__).parent.parent.parent / "design_system" / "tokens.json"
    palettes_file = Path(__file__).parent.parent.parent / "design_system" / "palettes.json"

    if not tokens_file.exists() or not palettes_file.exists():
        raise HTTPException(status_code=404, detail="Design tokens not found")

    with open(tokens_file) as f:
        tokens = json.load(f)

    with open(palettes_file) as f:
        palettes = json.load(f)

    theme_colors = tokens["theme"].get(theme, tokens["theme"]["light"])

    return {
        "theme": theme,
        "colors": theme_colors,
        "palettes": palettes,
        "rules": palettes["visualization"]["rules"],
    }


@app.get("/tables")
async def list_tables():
    """List all tables and views in warehouse."""
    try:
        wh = get_warehouse()
        tables = wh.list_tables()
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tables/{table_name}/schema")
async def get_table_schema(table_name: str):
    """Get schema for table."""
    try:
        wh = get_warehouse()
        schema = wh.describe(table_name)
        return {"table": table_name, "schema": schema.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns:
        Metrics in Prometheus text format
    """
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type=get_content_type())


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "kearney-platform-api",
        "version": "1.0.0",
    }


# Signed URL endpoint
@app.post("/api/sign")
async def sign_artifact_url(
    path: str = Query(..., description="Artifact path to sign"),
    ttl_minutes: int = Query(15, description="TTL in minutes", ge=1, le=1440),
    identity: Identity = Depends(require_auth),
    tenant_context: TenantContext = Depends(get_tenant_context),
    request: Request = None
):
    """
    Generate signed URL for artifact access.

    Requires authentication and tenant access.
    """
    # Check scope
    if not identity.has_scope(ScopeEnum.ARTIFACT_READ):
        audit_logger = get_audit_logger()
        audit_logger.log_access_denied(
            identity=identity,
            resource_type="artifact",
            resource_id=path,
            tenant=tenant_context.tenant,
            reason="insufficient_scope",
            ip_address=request.client.host if request and request.client else None,
            trace_id=get_current_trace_id()
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_permissions",
                "message": "Requires artifact:read scope"
            }
        )

    # Generate signed URL
    ip_address = request.client.host if request and request.client else None
    signed_url = create_signed_artifact_url(
        artifact_path=path,
        tenant=tenant_context.tenant,
        ttl_minutes=ttl_minutes,
        ip_address=ip_address
    )

    # Log event
    audit_logger = get_audit_logger()
    audit_logger.log_signed_url_issue(
        identity=identity,
        path=path,
        tenant=tenant_context.tenant,
        ttl_seconds=ttl_minutes * 60,
        ip_address=ip_address,
        trace_id=get_current_trace_id()
    )

    return {
        "signed_url": signed_url,
        "expires_in_seconds": ttl_minutes * 60,
        "path": path,
        "tenant": tenant_context.tenant
    }


# Exception handlers for security errors
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    """Handle 401 Unauthorized errors."""
    return JSONResponse(
        status_code=401,
        content={
            "error": "unauthorized",
            "message": "Authentication required. Provide X-API-Key or Authorization header.",
            "path": request.url.path
        }
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Handle 403 Forbidden errors."""
    return JSONResponse(
        status_code=403,
        content={
            "error": "forbidden",
            "message": "Access denied. Insufficient permissions.",
            "path": request.url.path
        }
    )


# Mangum adapter for Lambda
if Mangum:
    handler = Mangum(app)
else:
    # Stub handler if Mangum not installed
    def handler(event, context):
        return {"statusCode": 500, "body": json.dumps({"error": "Mangum not installed"})}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
