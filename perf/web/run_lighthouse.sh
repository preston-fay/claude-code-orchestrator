#!/bin/bash
# Run Lighthouse performance tests on web app
#
# Usage:
#   ./perf/web/run_lighthouse.sh [url]
#
# Default URL: http://localhost:5173

set -e

URL="${1:-http://localhost:5173}"
OUTPUT_DIR="perf/web"
REPORT_JSON="$OUTPUT_DIR/lighthouse-report.json"
REPORT_HTML="$OUTPUT_DIR/lighthouse-report.html"

echo "Running Lighthouse on $URL..."

# Check if lighthouse is installed
if ! command -v lighthouse &> /dev/null; then
    echo "Lighthouse not found. Installing..."
    npm install -g lighthouse
fi

# Run Lighthouse
lighthouse "$URL" \
    --config-path=perf/web/lighthouse.config.js \
    --output=json \
    --output=html \
    --output-path="$OUTPUT_DIR/lighthouse-report" \
    --chrome-flags="--headless --no-sandbox --disable-dev-shm-usage" \
    --quiet

echo "Lighthouse report saved to:"
echo "  JSON: $REPORT_JSON"
echo "  HTML: $REPORT_HTML"

# Parse and display key metrics
if [ -f "$REPORT_JSON" ]; then
    echo ""
    echo "Key Metrics:"
    echo "------------"

    # Extract scores using Python
    python3 << EOF
import json
import sys

try:
    with open("$REPORT_JSON", "r") as f:
        report = json.load(f)

    categories = report.get("categories", {})

    print(f"Performance:     {categories.get('performance', {}).get('score', 0) * 100:.0f}%")
    print(f"Accessibility:   {categories.get('accessibility', {}).get('score', 0) * 100:.0f}%")
    print(f"Best Practices:  {categories.get('best-practices', {}).get('score', 0) * 100:.0f}%")
    print(f"SEO:             {categories.get('seo', {}).get('score', 0) * 100:.0f}%")

    print("")
    print("Core Web Vitals:")
    print("----------------")

    audits = report.get("audits", {})

    fcp = audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000
    lcp = audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000
    tbt = audits.get("total-blocking-time", {}).get("numericValue", 0)
    cls = audits.get("cumulative-layout-shift", {}).get("numericValue", 0)

    print(f"FCP: {fcp:.2f}s")
    print(f"LCP: {lcp:.2f}s")
    print(f"TBT: {tbt:.0f}ms")
    print(f"CLS: {cls:.3f}")

    # Check thresholds
    print("")
    print("Threshold Check:")
    print("----------------")

    perf_score = categories.get('performance', {}).get('score', 0)
    a11y_score = categories.get('accessibility', {}).get('score', 0)
    bp_score = categories.get('best-practices', {}).get('score', 0)

    passed = True

    if perf_score < 0.85:
        print(f"FAIL: Performance {perf_score * 100:.0f}% < 85%")
        passed = False
    else:
        print(f"PASS: Performance {perf_score * 100:.0f}% >= 85%")

    if a11y_score < 0.90:
        print(f"FAIL: Accessibility {a11y_score * 100:.0f}% < 90%")
        passed = False
    else:
        print(f"PASS: Accessibility {a11y_score * 100:.0f}% >= 90%")

    if bp_score < 0.90:
        print(f"FAIL: Best Practices {bp_score * 100:.0f}% < 90%")
        passed = False
    else:
        print(f"PASS: Best Practices {bp_score * 100:.0f}% >= 90%")

    sys.exit(0 if passed else 1)

except Exception as e:
    print(f"Error parsing report: {e}", file=sys.stderr)
    sys.exit(1)
EOF
fi
