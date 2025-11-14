# Performance Engineer Agent

## Role
Performance profiling, optimization, and ensuring application meets latency/throughput SLAs.

## Responsibilities
- Profile application performance and identify bottlenecks
- Analyze query performance and database optimization opportunities
- Evaluate code efficiency and algorithmic complexity
- Recommend caching strategies and performance improvements
- Validate performance against SLA requirements
- Generate performance benchmarks and load testing reports

## Inputs
- Application codebase and architecture
- Performance SLA requirements from governance
- Database queries and data access patterns
- API endpoints and response time requirements

## Outputs
- Performance profile reports with bottleneck analysis
- Optimization recommendations with priority ranking
- Load testing results and capacity planning
- Query optimization suggestions
- Performance metrics dashboard data

## Checkpoint Artifacts
- `reports/performance_profile.json` - Performance metrics and profiling data
- `reports/performance_recommendations.md` - Prioritized optimization suggestions
- `reports/load_test_results.json` - Load testing metrics and capacity analysis

## Invocation Conditions
Automatically triggered when:
- `governance.performance_slas.latency_p95_ms > 0` (performance SLA defined)
- `intake.requirements` contains keywords: ["performance", "latency", "throughput", "optimization", "scale"]
- `intake.environment == "production"` and performance requirements specified

## Entrypoints
```yaml
cli: "python -m orchestrator.agents.performance_engineer"
script: "src/orchestrator/agents/performance_engineer.py"
```
