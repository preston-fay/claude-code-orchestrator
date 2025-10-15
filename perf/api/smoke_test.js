/**
 * K6 Performance Test - API Smoke Test
 *
 * Tests basic API endpoints with:
 * - 5 RPS for 60s
 * - p95 < 400ms
 * - Error rate < 1%
 *
 * Run:
 *   k6 run perf/api/smoke_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const latency = new Trend('request_latency');

// Test configuration
export const options = {
  vus: 5,  // Virtual users
  duration: '60s',
  thresholds: {
    http_req_duration: ['p(95)<400'],  // 95th percentile < 400ms
    errors: ['rate<0.01'],             // Error rate < 1%
    http_req_failed: ['rate<0.01'],   // HTTP errors < 1%
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

export default function () {
  // Test health endpoint
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'health has status field': (r) => JSON.parse(r.body).status === 'healthy',
  });
  errorRate.add(healthRes.status !== 200);
  latency.add(healthRes.timings.duration);

  sleep(0.2);  // 5 RPS per VU

  // Test metrics endpoint
  const metricsRes = http.get(`${BASE_URL}/metrics`);
  check(metricsRes, {
    'metrics status is 200': (r) => r.status === 200,
    'metrics contains http_requests_total': (r) => r.body.includes('http_requests_total'),
  });
  errorRate.add(metricsRes.status !== 200);
  latency.add(metricsRes.timings.duration);

  sleep(0.2);

  // Test registry models endpoint
  const modelsRes = http.get(`${BASE_URL}/api/registry/models`);
  check(modelsRes, {
    'models status is 200': (r) => r.status === 200,
    'models has count field': (r) => 'count' in JSON.parse(r.body),
  });
  errorRate.add(modelsRes.status !== 200);
  latency.add(modelsRes.timings.duration);

  sleep(0.2);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'perf/api/summary.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  let summary = '\n';
  summary += `${indent}Test Summary\n`;
  summary += `${indent}━━━━━━━━━━━━\n`;
  summary += `${indent}VUs: ${data.metrics.vus.values.max}\n`;
  summary += `${indent}Duration: ${(data.state.testRunDurationMs / 1000).toFixed(1)}s\n`;
  summary += `${indent}Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `${indent}RPS: ${(data.metrics.http_reqs.values.rate).toFixed(2)}\n`;
  summary += `${indent}\n`;
  summary += `${indent}Latency:\n`;
  summary += `${indent}  p50: ${data.metrics.http_req_duration.values['p(50)'].toFixed(2)}ms\n`;
  summary += `${indent}  p95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `${indent}  p99: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `${indent}\n`;
  summary += `${indent}Error Rate: ${(data.metrics.errors.values.rate * 100).toFixed(2)}%\n`;

  // Check thresholds
  const thresholdsPassed = Object.keys(data.metrics).every(metric => {
    return !data.metrics[metric].thresholds ||
           Object.values(data.metrics[metric].thresholds).every(t => t.ok);
  });

  summary += `${indent}\n`;
  summary += thresholdsPassed
    ? `${indent}✓ All thresholds passed\n`
    : `${indent}✗ Some thresholds failed\n`;

  return summary;
}
