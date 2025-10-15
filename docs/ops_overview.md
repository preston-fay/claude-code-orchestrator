# Ops Layer Overview

Comprehensive guide to the operational infrastructure of the Kearney Data Platform.

## Table of Contents

1. [Architecture](#architecture)
2. [Secrets Management](#secrets-management)
3. [Structured Logging](#structured-logging)
4. [Distributed Tracing](#distributed-tracing)
5. [Metrics & Monitoring](#metrics--monitoring)
6. [Caching Strategy](#caching-strategy)
7. [Performance Testing](#performance-testing)
8. [Runbooks](#runbooks)

---

## Architecture

The ops layer provides production-grade reliability, observability, and performance:

```
┌─────────────────────────────────────────────────┐
│  Application Layer                              │
│  - FastAPI (src/server/app.py)                  │
│  - Orchestrator CLI (src/orchestrator/cli.py)   │
│  - Data Warehouse (src/data/warehouse.py)       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Ops Layer (src/ops/)                           │
│  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Secrets   │  │  Logging   │  │  Tracing  │ │
│  └────────────┘  └────────────┘  └───────────┘ │
│  ┌────────────┐  ┌────────────┐                │
│  │  Metrics   │  │   Cache    │                │
│  └────────────┘  └────────────┘                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  External Services                              │
│  - AWS SSM / Secrets Manager                    │
│  - OpenTelemetry Collector (OTLP)               │
│  - Prometheus / Grafana                         │
└─────────────────────────────────────────────────┘
```

**Key Principles:**
- Graceful degradation (ops components optional)
- Zero-config local development (uses .env fallback)
- Production-ready with AWS integration
- Minimal performance overhead

---

## Secrets Management

**Module:** `src/ops/secrets.py`

### Overview

Multi-source secret resolution with precedence hierarchy:

```
Environment Variables  (highest priority)
      ↓
AWS SSM Parameter Store
      ↓
AWS Secrets Manager
      ↓
.env file  (lowest priority)
```

### Usage

```python
from src.ops.secrets import get_secret

# Get secret with fallback hierarchy
api_key = get_secret("MAPBOX_ACCESS_TOKEN")

# With default value
db_host = get_secret("DATABASE_HOST", default="localhost")

# Check secret source
from src.ops.secrets import get_secret_source, SecretSource

source = get_secret_source("API_KEY")
if source == SecretSource.ENV:
    print("Using environment variable")
```

### Configuration

**File:** `configs/secrets.yaml`

```yaml
secrets:
  mapbox_token:
    env_var: MAPBOX_ACCESS_TOKEN
    description: "Mapbox API token"
    required: false
    aws_path: /kearney-platform/prod/mapbox_token

  registry_api_key:
    env_var: REGISTRY_API_KEY
    description: "API key for registry writes"
    required: true
    aws_path: /kearney-platform/prod/registry_api_key
    default: "kearney-registry-key"
```

### TTL Caching

Secrets are cached in-process with configurable TTL (default: 300s):

```python
# Cache for 10 minutes
secret = get_secret("API_KEY", ttl_seconds=600)
```

Cache is automatically cleared on expiration.

### AWS Setup

**SSM Parameter Store:**
```bash
aws ssm put-parameter \
    --name /kearney-platform/prod/mapbox_token \
    --value "pk.ey..." \
    --type SecureString
```

**Secrets Manager:**
```bash
aws secretsmanager create-secret \
    --name kearney-platform/prod/registry_api_key \
    --secret-string "kearney-registry-key-prod"
```

### Environment Variables

Set environment variables for local development:

```bash
export MAPBOX_ACCESS_TOKEN="pk.ey..."
export REGISTRY_API_KEY="local-dev-key"
```

Or use `.env` file:
```
MAPBOX_ACCESS_TOKEN=pk.ey...
REGISTRY_API_KEY=local-dev-key
```

---

## Structured Logging

**Module:** `src/ops/logging.py`

### Overview

Structured logging with `structlog` for JSON output and context propagation.

### Configuration

```python
from src.ops.logging import configure_logging

# JSON mode (production)
configure_logging(json=True, level="INFO", service_name="api")

# Console mode (development)
configure_logging(json=False, level="DEBUG")
```

### Usage

```python
from src.ops.logging import get_logger, bind_context

logger = get_logger("my_module")

# Bind context (available to all subsequent log calls)
bind_context(request_id="req-123", user_id="user-456")

# Log with structured fields
logger.info("user_logged_in", username="alice", ip="192.168.1.1")
logger.warning("rate_limit_exceeded", limit=100, current=105)
logger.error("database_error", error="Connection timeout", query="SELECT ...")

# Unbind specific context
unbind_context("user_id")

# Clear all context
clear_context()
```

### Context Fields

Standard context fields included automatically:

- `timestamp`: ISO8601 UTC timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `logger`: Logger name
- `run_id`: Orchestrator run ID (if in run context)
- `phase`: Current orchestrator phase
- `request_id`: HTTP request ID
- `client`: Client slug (for multi-tenant)
- `trace_id`: OpenTelemetry trace ID

### Output Format

**JSON mode:**
```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "info",
  "logger": "api",
  "event": "request_completed",
  "request_id": "req-abc123",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "method": "GET",
  "path": "/api/registry/models",
  "status": 200,
  "latency_ms": 45
}
```

**Console mode:**
```
2025-01-15 10:30:00 [info     ] request_completed  method=GET path=/api/registry/models status=200 latency_ms=45
```

---

## Distributed Tracing

**Module:** `src/ops/tracing.py`

### Overview

OpenTelemetry integration for distributed tracing with OTLP export.

### Setup

```python
from src.ops.tracing import init_tracer, instrument_fastapi

# Initialize tracer
tracer = init_tracer(
    service_name="kearney-platform-api",
    otlp_endpoint="http://localhost:4318"
)

# Instrument FastAPI app
from fastapi import FastAPI
app = FastAPI()
instrument_fastapi(app)
```

### Usage

```python
from src.ops.tracing import create_span, get_current_trace_id

# Create span manually
with create_span("query_database", table="users", operation="SELECT") as span:
    result = execute_query("SELECT * FROM users")
    span.set_attribute("row_count", len(result))

# Get current trace ID (for logging)
trace_id = get_current_trace_id()
bind_context(trace_id=trace_id)
```

### FastAPI Integration

Trace IDs are automatically added to FastAPI requests via middleware:

```python
# In src/server/app.py
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    trace_id = get_current_trace_id()
    bind_context(trace_id=trace_id)
    # ... process request
```

### OTLP Collector

Configure OpenTelemetry Collector to receive traces:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

exporters:
  jaeger:
    endpoint: jaeger:14250
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [jaeger, logging]
```

Run collector:
```bash
docker run -p 4318:4318 \
    -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
    otel/opentelemetry-collector \
    --config=/etc/otel-collector-config.yaml
```

---

## Metrics & Monitoring

**Module:** `src/ops/metrics.py`

### Overview

Prometheus metrics for application and business monitoring.

### Metrics Catalog

**HTTP Metrics:**
- `http_requests_total{route, method, status}` - Total HTTP requests (Counter)
- `http_request_latency_seconds{route, method}` - Request latency (Histogram)

**Database Metrics:**
- `duckdb_query_seconds{query_type}` - Query execution time (Histogram)
- `duckdb_query_total{query_type}` - Total queries executed (Counter)

**Isochrone Metrics:**
- `isochrone_requests_total{provider, mode, status}` - Isochrone API calls (Counter)
- `isochrone_request_latency_seconds{provider, mode}` - API latency (Histogram)

**Orchestrator Metrics:**
- `orchestrator_phase_seconds{phase}` - Phase duration (Histogram)
- `orchestrator_agent_retries_total{agent, phase}` - Agent retry count (Counter)
- `orchestrator_runs_total{status}` - Total orchestrator runs (Counter)

**Cache Metrics:**
- `cache_hits_total{cache_type}` - Cache hit count (Counter)
- `cache_misses_total{cache_type}` - Cache miss count (Counter)
- `cache_size_bytes{cache_type}` - Cache size in bytes (Gauge)

**Registry Metrics:**
- `registry_models_total` - Total registered models (Gauge)
- `registry_datasets_total` - Total registered datasets (Gauge)

### Usage

```python
from src.ops.metrics import (
    http_requests_total,
    http_request_latency,
    duckdb_query_seconds,
)

# Record HTTP request
http_requests_total.labels(route="/api/users", method="GET", status=200).inc()
http_request_latency.labels(route="/api/users", method="GET").observe(0.123)

# Record database query
duckdb_query_seconds.labels(query_type="SELECT").observe(0.045)

# Record orchestrator phase
from src.ops.metrics import orchestrator_phase_seconds
orchestrator_phase_seconds.labels(phase="analyze").observe(12.5)
```

### Metrics Endpoint

Metrics are exposed at `/metrics` in Prometheus text format:

```bash
curl http://localhost:8000/metrics
```

Output:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{route="/api/users",method="GET",status="200"} 1234

# HELP http_request_latency_seconds HTTP request latency in seconds
# TYPE http_request_latency_seconds histogram
http_request_latency_seconds_bucket{route="/api/users",method="GET",le="0.1"} 950
http_request_latency_seconds_bucket{route="/api/users",method="GET",le="0.5"} 1200
http_request_latency_seconds_sum{route="/api/users",method="GET"} 145.2
http_request_latency_seconds_count{route="/api/users",method="GET"} 1234
```

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'kearney-platform'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana Dashboards

Import prebuilt dashboards or create custom:

**API Dashboard:**
- Request rate (req/s)
- p50, p95, p99 latency
- Error rate
- Top slow routes

**Orchestrator Dashboard:**
- Phase duration trends
- Agent retry rates
- Run success/failure ratio
- Queue depth

**Cache Dashboard:**
- Hit/miss ratio
- Cache size over time
- Eviction rate
- Top cached queries

---

## Caching Strategy

**Module:** `src/data/cache.py`
**Config:** `configs/cache.yaml`

### Overview

Two-tier caching strategy:
1. Query result caching (Parquet files)
2. HTTP caching (ETag/Cache-Control headers)

### Query Result Caching

Cache expensive DuckDB query results to Parquet files:

```python
from src.data.cache import get_cache, cached_query

cache = get_cache()

# Cache query result
table = execute_query("SELECT * FROM large_table")
cache.set("SELECT * FROM large_table", table, params={}, ttl_seconds=3600)

# Retrieve cached result
result = cache.get("SELECT * FROM large_table", params={})
if result:
    print("Cache hit!")
else:
    print("Cache miss - executing query...")
```

**Cache key generation:**
- SQL normalized (whitespace removed)
- Params sorted by key
- SHA256 hash computed

**TTL-based expiration:**
- Metadata file stores `created_at` and `ttl_seconds`
- Expired entries automatically removed on next access

### Cache Decorator

```python
from src.data.cache import cached_query

@cached_query(ttl_seconds=3600)
def get_user_stats(user_id: int):
    return warehouse.query(f"SELECT * FROM user_stats WHERE id = {user_id}")

# First call: cache miss, executes query
stats1 = get_user_stats(123)

# Second call: cache hit, returns cached result
stats2 = get_user_stats(123)
```

### Pattern-Based Invalidation

Invalidate cache entries matching a pattern:

```python
# Invalidate all user-related queries
cache.invalidate("*user*")

# Invalidate specific table
cache.invalidate("SELECT * FROM orders")

# Clear entire cache
cache.clear()
```

### Configuration

**File:** `configs/cache.yaml`

```yaml
query_cache:
  enabled: true
  default_ttl_seconds: 3600  # 1 hour
  max_size_mb: 1000  # 1 GB

  ttls:
    "SELECT * FROM data WHERE date = CURRENT_DATE": 300  # 5 min
    "SELECT * FROM models*": 3600  # 1 hour
    "*_aggregated": 7200  # 2 hours

http_cache:
  enabled: true
  static_max_age: 31536000  # 1 year
  stable_endpoints:
    - path: /api/viz/palette
      max_age: 86400  # 1 day
```

### HTTP Caching

Add Cache-Control headers to stable endpoints:

```python
from fastapi import Response

@app.get("/api/viz/palette")
def get_palette():
    palette = load_palette()
    return Response(
        content=palette,
        headers={
            "Cache-Control": "public, max-age=86400",
            "ETag": compute_etag(palette)
        }
    )
```

### Cache Statistics

```python
stats = cache.get_stats()
print(f"Entries: {stats['entries']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
```

---

## Performance Testing

### API Performance (k6)

**File:** `perf/api/smoke_test.js`

Run smoke test:
```bash
k6 run perf/api/smoke_test.js
```

**Thresholds:**
- p95 latency < 400ms
- Error rate < 1%
- Requests: 5 VUs, 60s duration

**CI Integration:**
```yaml
# .github/workflows/ops-ci.yml
- name: Run k6 performance tests
  run: |
    k6 run perf/api/smoke_test.js --out json=perf/api/results.json
```

### Web Performance (Lighthouse)

**File:** `perf/web/lighthouse.config.js`

Run Lighthouse:
```bash
./perf/web/run_lighthouse.sh http://localhost:5173
```

**Thresholds:**
- Performance ≥ 85
- Accessibility ≥ 90
- Best Practices ≥ 90

**Core Web Vitals:**
- FCP < 1.8s
- LCP < 2.5s
- TBT < 200ms
- CLS < 0.1

---

## Runbooks

### Issue: High API Latency

**Symptoms:**
- p95 latency > 500ms
- Admin dashboard shows spike in latency sparkline

**Diagnosis:**
1. Check metrics: `curl http://localhost:8000/metrics | grep latency`
2. Review slow query logs: `grep "slow_query" logs/app.log`
3. Check cache hit ratio: admin dashboard or metrics

**Resolution:**
- If cache miss rate high: review TTL settings in `configs/cache.yaml`
- If database queries slow: add indexes, optimize queries
- If external API slow: check isochrone provider status

### Issue: Cache Miss Rate Elevated

**Symptoms:**
- cache_hits_total / (cache_hits_total + cache_misses_total) < 0.5
- Admin dashboard shows low cache hit ratio

**Diagnosis:**
1. Check cache stats: `cache.get_stats()`
2. Review recent invalidations
3. Check TTL configuration

**Resolution:**
- Increase TTL for stable queries
- Review invalidation patterns (too aggressive?)
- Increase cache size limit in `configs/cache.yaml`

### Issue: Secrets Not Loading

**Symptoms:**
- `get_secret()` returns `None` or default
- Application fails with missing configuration

**Diagnosis:**
1. Check secret source: `get_secret_source("SECRET_NAME")`
2. Verify environment variables: `env | grep SECRET`
3. Check AWS credentials: `aws sts get-caller-identity`
4. Test SSM access: `aws ssm get-parameter --name /kearney-platform/prod/...`

**Resolution:**
- Set environment variable: `export SECRET_NAME=value`
- Or add to `.env` file
- Or configure AWS credentials: `aws configure`

### Issue: Traces Not Appearing

**Symptoms:**
- No traces in Jaeger/Zipkin
- `get_current_trace_id()` returns "no-trace"

**Diagnosis:**
1. Check OTLP endpoint: `curl http://localhost:4318/v1/traces`
2. Verify tracer initialization: check startup logs
3. Test instrumentation: `instrument_fastapi(app)` called?

**Resolution:**
- Start OTLP collector: see [OTLP Collector](#otlp-collector) section
- Verify endpoint in environment: `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
- Restart application to reinitialize tracer

### Issue: Metrics Endpoint Returns 404

**Symptoms:**
- `curl http://localhost:8000/metrics` returns 404

**Diagnosis:**
1. Check if metrics endpoint registered: review `src/server/app.py`
2. Verify prometheus_client installed: `pip list | grep prometheus`

**Resolution:**
- Install prometheus_client: `pip install prometheus_client`
- Ensure `/metrics` route registered in app.py
- Restart server

---

## Best Practices

1. **Secrets**: Never commit secrets to git. Use environment variables or AWS.

2. **Logging**: Use structured logging with context fields. Avoid string interpolation.

3. **Tracing**: Create spans for major operations (DB queries, API calls, phases).

4. **Metrics**: Use appropriate metric types (Counter, Histogram, Gauge). Add labels for dimensions.

5. **Caching**: Set TTLs based on data freshness requirements. Invalidate on writes.

6. **Performance**: Run tests in CI. Set failure thresholds. Monitor trends.

---

## References

- [Secrets Management](#secrets-management)
- [Structured Logging](#structured-logging)
- [Distributed Tracing](#distributed-tracing)
- [Metrics & Monitoring](#metrics--monitoring)
- [Caching Strategy](#caching-strategy)
- [Performance Testing](#performance-testing)
- [Performance Tuning Guide](perf_strategy.md)
