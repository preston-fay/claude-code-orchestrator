# Performance Strategy & Tuning Guide

Guide for optimizing performance and interpreting CI performance test results.

## Table of Contents

1. [Performance Goals](#performance-goals)
2. [Measurement Strategy](#measurement-strategy)
3. [Threshold Definitions](#threshold-definitions)
4. [Reading CI Artifacts](#reading-ci-artifacts)
5. [Tuning Strategies](#tuning-strategies)
6. [Common Bottlenecks](#common-bottlenecks)
7. [Optimization Checklist](#optimization-checklist)

---

## Performance Goals

### API Performance

**Target Latency:**
- p50: < 100ms
- p95: < 400ms
- p99: < 1000ms

**Throughput:**
- Minimum: 10 req/s
- Target: 50 req/s
- Goal: 100+ req/s

**Error Rate:**
- Maximum: < 1%
- Target: < 0.1%

### Web Performance

**Lighthouse Scores:**
- Performance: ≥ 85
- Accessibility: ≥ 90
- Best Practices: ≥ 90
- SEO: ≥ 80

**Core Web Vitals:**
- First Contentful Paint (FCP): < 1.8s
- Largest Contentful Paint (LCP): < 2.5s
- Total Blocking Time (TBT): < 200ms
- Cumulative Layout Shift (CLS): < 0.1

### Database Performance

**Query Execution:**
- Simple SELECT: < 50ms
- Complex JOIN: < 500ms
- Aggregation: < 1000ms

**Cache Hit Ratio:**
- Minimum: > 50%
- Target: > 75%
- Goal: > 90%

---

## Measurement Strategy

### 1. Continuous Monitoring

**Prometheus Metrics:**
- Scraped every 15s
- Retained for 30 days
- Exported to Grafana for visualization

**Structured Logs:**
- All requests logged with latency
- Slow queries (>500ms) flagged
- Errors logged with trace IDs

**Distributed Traces:**
- Sampled at 10% for production
- 100% sampling for staging
- Retained for 7 days

### 2. Periodic Testing

**API Load Tests (k6):**
- Smoke test: Daily in CI
- Load test: Weekly scheduled run
- Stress test: Before major releases

**Web Performance (Lighthouse):**
- On every PR
- Daily for main branch
- Full audit before releases

### 3. Real User Monitoring (RUM)

**Client-Side Metrics:**
- Navigation timing API
- Resource timing API
- Long task detection

**Backend Correlation:**
- Trace IDs in client headers
- Server-side span correlation
- End-to-end request tracking

---

## Threshold Definitions

### API Thresholds

**File:** `perf/api/smoke_test.js`

```javascript
export const options = {
  thresholds: {
    // 95th percentile must be under 400ms
    http_req_duration: ['p(95)<400'],

    // Error rate must be under 1%
    errors: ['rate<0.01'],
    http_req_failed: ['rate<0.01'],

    // Minimum throughput
    http_reqs: ['rate>10'],
  },
};
```

**Interpretation:**
- `p(95)<400`: 95% of requests complete in under 400ms
- `rate<0.01`: Less than 1% of requests fail
- `rate>10`: At least 10 requests per second

### Web Thresholds

**File:** `perf/web/lighthouse.config.js`

```javascript
assertions: {
  'categories:performance': ['error', { minScore: 0.85 }],
  'categories:accessibility': ['error', { minScore: 0.90 }],
  'categories:best-practices': ['error', { minScore: 0.90 }],

  'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
  'total-blocking-time': ['error', { maxNumericValue: 200 }],
  'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
}
```

**Interpretation:**
- `minScore: 0.85`: Score must be at least 85/100
- `maxNumericValue: 2500`: Metric must be under 2500ms
- `error` vs `warn`: Errors fail the build, warnings just alert

### Database Thresholds

Monitored via Prometheus metrics:

```
# Alert if p95 query time exceeds 500ms
duckdb_query_seconds_bucket{query_type="SELECT",le="0.5"} /
duckdb_query_seconds_count{query_type="SELECT"} < 0.95
```

---

## Reading CI Artifacts

### k6 Results

**File:** `perf/api/results.json`

Sample output:
```json
{
  "type": "Point",
  "metric": "http_req_duration",
  "data": {
    "time": "2025-01-15T10:30:00Z",
    "value": 0.234,
    "tags": {
      "method": "GET",
      "route": "/api/registry/models",
      "status": "200"
    }
  }
}
```

**Key Metrics to Check:**

1. **http_req_duration**: Request latency distribution
   - Look for p50, p95, p99 values
   - Check if p95 < 400ms threshold

2. **http_req_failed**: Error rate
   - Should be < 1% (0.01)
   - Investigate if elevated

3. **http_reqs**: Throughput
   - Requests per second
   - Should be > 10 req/s

**Reading Summary:**
```bash
# Extract p95 from k6 JSON
jq '.metrics.http_req_duration | ."p(95)"' perf/api/results.json
```

### Lighthouse Reports

**File:** `perf/web/lighthouse-report.json`

Sample structure:
```json
{
  "categories": {
    "performance": {
      "score": 0.89,
      "title": "Performance"
    },
    "accessibility": {
      "score": 0.93,
      "title": "Accessibility"
    }
  },
  "audits": {
    "largest-contentful-paint": {
      "score": 0.91,
      "numericValue": 2245,
      "displayValue": "2.2 s"
    }
  }
}
```

**Key Scores to Check:**

1. **Performance Score** (0-100)
   - Weighted average of Core Web Vitals
   - Must be ≥ 85

2. **Accessibility Score** (0-100)
   - ARIA usage, contrast ratios, labels
   - Must be ≥ 90

3. **Core Web Vitals**:
   - LCP: Time to render largest content (< 2.5s)
   - TBT: Sum of blocking time (< 200ms)
   - CLS: Visual stability (< 0.1)

**Reading Report:**
```bash
# Extract performance score
jq '.categories.performance.score * 100' perf/web/lighthouse-report.json

# Extract LCP
jq '.audits."largest-contentful-paint".numericValue' perf/web/lighthouse-report.json
```

### CI Job Logs

**File:** `.github/workflows/ops-ci.yml`

**API Performance Job:**
```yaml
- name: Run k6 performance tests
  run: k6 run perf/api/smoke_test.js --out json=perf/api/results.json

- name: Check performance thresholds
  run: |
    # Parse results and assert thresholds
    python -c "..."
```

**Expected Output:**
```
✓ p95 latency: 387ms < 400ms
✓ error rate: 0.3% < 1.0%
✓ throughput: 16.7 req/s > 10 req/s
Performance test PASSED
```

**Failure Indicators:**
- `✗ p95 latency: 456ms > 400ms` - Latency threshold exceeded
- `✗ error rate: 1.2% > 1.0%` - Error rate too high
- `exit code 1` - Test failed

---

## Tuning Strategies

### 1. Cache Optimization

**Symptom:** High latency on repeated queries

**Diagnosis:**
```python
from src.data.cache import get_cache

cache = get_cache()
stats = cache.get_stats()
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
```

**Tuning:**

1. **Increase TTL** for stable data:
   ```yaml
   # configs/cache.yaml
   ttls:
     "SELECT * FROM models*": 7200  # 2 hours (was 1 hour)
   ```

2. **Increase cache size** limit:
   ```yaml
   query_cache:
     max_size_mb: 2000  # 2 GB (was 1 GB)
   ```

3. **Preload hot queries** at startup:
   ```python
   # src/server/app.py
   @app.on_event("startup")
   def warmup_cache():
       cache = get_cache()
       # Execute and cache hot queries
       cache.set("SELECT * FROM models", models_table)
   ```

**Expected Impact:**
- Cache hit ratio: +20-30%
- p95 latency: -50-70%

### 2. Database Query Optimization

**Symptom:** Slow database queries (>500ms)

**Diagnosis:**
```python
# Check slow query logs
grep "slow_query" logs/app.log | jq '.query, .duration_ms'
```

**Tuning:**

1. **Add indexes** on frequently queried columns:
   ```sql
   CREATE INDEX idx_models_name ON models(name);
   CREATE INDEX idx_datasets_created_at ON datasets(created_at);
   ```

2. **Optimize query structure**:
   ```python
   # Before: Multiple queries
   for model_id in model_ids:
       model = query(f"SELECT * FROM models WHERE id = {model_id}")

   # After: Single query with IN clause
   models = query(f"SELECT * FROM models WHERE id IN ({','.join(model_ids)})")
   ```

3. **Use columnar storage** (Parquet):
   ```python
   # Before: CSV
   warehouse.load("data/models.csv", table="models")

   # After: Parquet
   warehouse.load("data/models.parquet", table="models")
   ```

**Expected Impact:**
- Query time: -60-80%
- CPU usage: -30-40%

### 3. HTTP Response Optimization

**Symptom:** Large response payloads, slow transfers

**Diagnosis:**
```bash
# Check response sizes
curl -I http://localhost:8000/api/registry/models | grep Content-Length
```

**Tuning:**

1. **Enable compression**:
   ```python
   from fastapi.middleware.gzip import GZipMiddleware

   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

2. **Paginate large results**:
   ```python
   @app.get("/api/registry/models")
   def list_models(limit: int = 50, offset: int = 0):
       return models[offset:offset+limit]
   ```

3. **Add ETag caching**:
   ```python
   @app.get("/api/viz/palette")
   def get_palette(request: Request):
       etag = compute_etag(palette)
       if request.headers.get("If-None-Match") == etag:
           return Response(status_code=304)
       return Response(content=palette, headers={"ETag": etag})
   ```

**Expected Impact:**
- Response size: -60-80%
- Transfer time: -50-70%
- Bandwidth: -50-70%

### 4. Frontend Optimization

**Symptom:** Low Lighthouse performance score, slow LCP

**Diagnosis:**
```bash
./perf/web/run_lighthouse.sh http://localhost:5173
```

**Tuning:**

1. **Code splitting**:
   ```javascript
   // vite.config.js
   export default {
     build: {
       rollupOptions: {
         output: {
           manualChunks: {
             'vendor': ['react', 'react-dom'],
             'charts': ['@nivo/core', '@nivo/bar'],
           }
         }
       }
     }
   }
   ```

2. **Image optimization**:
   ```html
   <!-- Before -->
   <img src="logo.png" />

   <!-- After -->
   <img src="logo.webp" width="200" height="100" loading="lazy" />
   ```

3. **Defer non-critical JS**:
   ```html
   <script src="analytics.js" defer></script>
   ```

**Expected Impact:**
- LCP: -30-50%
- TBT: -40-60%
- Performance score: +10-15 points

---

## Common Bottlenecks

### 1. Unoptimized Database Queries

**Indicators:**
- High `duckdb_query_seconds` p95
- Logs show queries > 500ms
- Low cache hit ratio

**Solutions:**
- Add indexes
- Optimize JOIN operations
- Enable query result caching

### 2. Cold Cache

**Indicators:**
- High latency on first requests
- Low `cache_hits_total`
- Latency decreases over time

**Solutions:**
- Implement cache warmup on startup
- Increase TTL for stable data
- Preload hot queries

### 3. Large Payloads

**Indicators:**
- High network transfer times
- Large `Content-Length` headers
- Slow downloads

**Solutions:**
- Enable GZip compression
- Implement pagination
- Use field filtering

### 4. External API Latency

**Indicators:**
- High `isochrone_request_latency`
- Timeout errors
- Variable latency

**Solutions:**
- Implement retry with exponential backoff
- Cache isochrone results
- Use fallback providers

### 5. Blocking Operations

**Indicators:**
- High TBT in Lighthouse
- Browser freezes
- Slow interactivity

**Solutions:**
- Use web workers for heavy computation
- Implement virtual scrolling
- Defer non-critical rendering

---

## Optimization Checklist

### API

- [ ] Enable query result caching
- [ ] Add database indexes
- [ ] Enable GZip compression
- [ ] Implement pagination
- [ ] Add ETag caching for stable endpoints
- [ ] Use connection pooling
- [ ] Optimize query structure (avoid N+1)
- [ ] Implement rate limiting

### Web

- [ ] Enable code splitting
- [ ] Optimize images (WebP, lazy loading)
- [ ] Defer non-critical JS
- [ ] Minimize CSS
- [ ] Use CDN for static assets
- [ ] Implement service worker caching
- [ ] Optimize font loading
- [ ] Remove unused code

### Database

- [ ] Add indexes on frequently queried columns
- [ ] Use Parquet for large datasets
- [ ] Optimize JOIN operations
- [ ] Enable query caching
- [ ] Partition large tables
- [ ] Analyze query plans
- [ ] Set appropriate memory limits

### Monitoring

- [ ] Enable Prometheus metrics
- [ ] Configure structured logging
- [ ] Set up distributed tracing
- [ ] Create Grafana dashboards
- [ ] Set up alerting rules
- [ ] Monitor cache hit ratio
- [ ] Track slow queries

---

## Performance Regression Detection

### CI Thresholds

If CI fails with performance regression:

1. **Review PR changes**:
   - New database queries?
   - Unoptimized loops?
   - Large data structures?

2. **Compare metrics**:
   ```bash
   # Before PR
   k6 run perf/api/smoke_test.js --out json=before.json

   # After PR
   k6 run perf/api/smoke_test.js --out json=after.json

   # Compare
   diff <(jq '.metrics.http_req_duration' before.json) \
        <(jq '.metrics.http_req_duration' after.json)
   ```

3. **Profile hot paths**:
   ```python
   import cProfile

   profiler = cProfile.Profile()
   profiler.enable()
   # ... code under test ...
   profiler.disable()
   profiler.print_stats(sort='cumtime')
   ```

### Gradual Degradation

If performance degrades over time:

1. **Check cache growth**:
   ```python
   stats = cache.get_stats()
   if stats['total_size_mb'] > 900:  # Near limit
       # Increase limit or reduce TTLs
   ```

2. **Review query patterns**:
   ```bash
   # Analyze slow query trends
   grep "slow_query" logs/app.log | \
     jq -r '.timestamp, .duration_ms' | \
     awk '{print $1, $2}' | \
     sort
   ```

3. **Monitor resource usage**:
   - CPU: Should be < 70%
   - Memory: Should be < 80%
   - Disk I/O: Check for bottlenecks

---

## Benchmark Comparison

### Before Optimization

```
API Performance:
  p50 latency: 245ms
  p95 latency: 678ms
  Error rate: 0.5%
  Throughput: 12 req/s

Web Performance:
  Performance: 72
  LCP: 3.8s
  TBT: 450ms

Cache:
  Hit ratio: 35%
  Size: 250 MB
```

### After Optimization

```
API Performance:
  p50 latency: 85ms (-65%)
  p95 latency: 320ms (-53%)
  Error rate: 0.1% (-80%)
  Throughput: 45 req/s (+275%)

Web Performance:
  Performance: 91 (+19 points)
  LCP: 1.9s (-50%)
  TBT: 120ms (-73%)

Cache:
  Hit ratio: 82% (+134%)
  Size: 850 MB (+240%)
```

---

## References

- [Ops Overview](ops_overview.md)
- [k6 Documentation](https://k6.io/docs/)
- [Lighthouse Docs](https://developers.google.com/web/tools/lighthouse)
- [Web Vitals](https://web.dev/vitals/)
- [DuckDB Performance](https://duckdb.org/docs/guides/performance/)
