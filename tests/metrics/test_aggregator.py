"""
Unit tests for metrics aggregator.

Tests weekly/monthly rollups and trend analysis.
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.orchestrator.metrics.aggregator import (
    MetricsAggregator,
    WeeklySummary,
    MonthlySummary,
    TrendAnalysis
)


class TestMetricsAggregator:
    """Test MetricsAggregator class"""

    def test_init(self, temp_metrics_dir):
        """Test aggregator initialization"""
        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)

        assert aggregator.metrics_dir == temp_metrics_dir
        assert aggregator.output_dir == temp_metrics_dir / "aggregated"
        assert aggregator.output_dir.exists()

    def test_load_json(self, temp_metrics_dir, sample_dora_deployments):
        """Test JSON file loading"""
        # Write sample file
        test_file = temp_metrics_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(sample_dora_deployments, f)

        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)
        data = aggregator._load_json(test_file)

        assert data is not None
        assert data["metric"] == "deployment_frequency"

    def test_load_json_missing_file(self, temp_metrics_dir):
        """Test loading non-existent file"""
        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)
        data = aggregator._load_json(temp_metrics_dir / "nonexistent.json")

        assert data is None

    def test_calculate_trend(self, temp_metrics_dir):
        """Test trend calculation"""
        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)

        # Test increase
        trend = aggregator._calculate_trend(150, 100)
        assert trend.change_percentage == 50.0
        assert trend.trend_direction == "up"

        # Test decrease
        trend = aggregator._calculate_trend(75, 100)
        assert trend.change_percentage == -25.0
        assert trend.trend_direction == "down"

        # Test stable
        trend = aggregator._calculate_trend(102, 100)
        assert abs(trend.change_percentage) < 5
        assert trend.trend_direction == "stable"

        # Test zero previous value
        trend = aggregator._calculate_trend(100, 0)
        assert trend.change_percentage == 100.0

    def test_calculate_trend_anomaly_detection(self, temp_metrics_dir):
        """Test anomaly detection in trends"""
        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)

        # Test anomaly (>10% change by default)
        trend = aggregator._calculate_trend(150, 100, threshold=10.0)
        assert trend.is_anomaly is True

        # Test non-anomaly
        trend = aggregator._calculate_trend(105, 100, threshold=10.0)
        assert trend.is_anomaly is False

        # Test with custom threshold
        trend = aggregator._calculate_trend(120, 100, threshold=30.0)
        assert trend.is_anomaly is False

    def test_detect_statistical_anomaly(self, temp_metrics_dir):
        """Test statistical anomaly detection"""
        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)

        # Test with stable values
        values = [100, 102, 98, 101, 99]
        is_anomaly = aggregator._detect_statistical_anomaly(values, 103)
        assert is_anomaly is False

        # Test with anomaly (far from mean)
        values = [100, 102, 98, 101, 99]
        is_anomaly = aggregator._detect_statistical_anomaly(values, 200)
        assert is_anomaly is True

        # Test with insufficient data
        values = [100, 102]
        is_anomaly = aggregator._detect_statistical_anomaly(values, 150)
        assert is_anomaly is False

        # Test with zero standard deviation
        values = [100, 100, 100, 100]
        is_anomaly = aggregator._detect_statistical_anomaly(values, 100)
        assert is_anomaly is False

    def test_aggregate_weekly(self, write_sample_metrics):
        """Test weekly aggregation"""
        metrics_dir = write_sample_metrics

        aggregator = MetricsAggregator(project_root=metrics_dir.parent.parent)
        weekly = aggregator.aggregate_weekly(weeks_back=2)

        assert len(weekly) == 2
        assert all(isinstance(w, WeeklySummary) for w in weekly)
        assert all("week_id" in w.__dict__ for w in weekly)
        assert all("metrics" in w.__dict__ for w in weekly)

        # Check JSON output
        output_file = metrics_dir / "aggregated" / "weekly_summary.json"
        assert output_file.exists()

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 2
        assert all("week_start" in w for w in data)
        assert all("week_end" in w for w in data)

    def test_aggregate_monthly(self, write_sample_metrics):
        """Test monthly aggregation"""
        metrics_dir = write_sample_metrics

        aggregator = MetricsAggregator(project_root=metrics_dir.parent.parent)
        monthly = aggregator.aggregate_monthly(months_back=2)

        assert len(monthly) == 2
        assert all(isinstance(m, MonthlySummary) for m in monthly)
        assert all("month_id" in m.__dict__ for m in monthly)
        assert all("metrics" in m.__dict__ for m in monthly)

        # Check JSON output
        output_file = metrics_dir / "aggregated" / "monthly_summary.json"
        assert output_file.exists()

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 2
        assert all("month_start" in m for m in data)
        assert all("month_end" in m for m in data)

    def test_analyze_trends(self, write_sample_metrics):
        """Test trend analysis"""
        metrics_dir = write_sample_metrics

        aggregator = MetricsAggregator(project_root=metrics_dir.parent.parent)

        # First create weekly summaries
        aggregator.aggregate_weekly(weeks_back=4)

        # Then analyze trends
        trends = aggregator.analyze_trends(weeks_back=4)

        assert isinstance(trends, dict)
        assert len(trends) > 0

        # Check JSON output
        output_file = metrics_dir / "aggregated" / "trends.json"
        assert output_file.exists()

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Validate trend structure
        for metric_path, trend_data in data.items():
            assert "current_value" in trend_data
            assert "previous_value" in trend_data
            assert "change_percentage" in trend_data
            assert "direction" in trend_data
            assert trend_data["direction"] in ["up", "down", "stable"]
            assert "is_anomaly" in trend_data
            assert "historical_values" in trend_data

    def test_aggregate_all(self, write_sample_metrics):
        """Test aggregating all metrics"""
        metrics_dir = write_sample_metrics

        aggregator = MetricsAggregator(project_root=metrics_dir.parent.parent)
        result = aggregator.aggregate_all(weeks_back=2, months_back=2)

        assert result["weekly_summaries"] == 2
        assert result["monthly_summaries"] == 2
        assert "trends_analyzed" in result

        # Check all output files exist
        assert (metrics_dir / "aggregated" / "weekly_summary.json").exists()
        assert (metrics_dir / "aggregated" / "monthly_summary.json").exists()
        assert (metrics_dir / "aggregated" / "trends.json").exists()

    def test_aggregate_dora_for_week(self, write_sample_metrics):
        """Test DORA metrics aggregation for a week"""
        metrics_dir = write_sample_metrics

        aggregator = MetricsAggregator(project_root=metrics_dir.parent.parent)
        week_start = datetime.now()
        week_end = week_start + timedelta(days=7)

        dora_summary = aggregator._aggregate_dora_for_week(week_start, week_end)

        assert isinstance(dora_summary, dict)
        assert "deployment_frequency" in dora_summary

    def test_aggregate_contributions_for_week(self, write_sample_metrics):
        """Test contribution metrics aggregation for a week"""
        metrics_dir = write_sample_metrics

        aggregator = MetricsAggregator(project_root=metrics_dir.parent.parent)
        week_start = datetime.now()
        week_end = week_start + timedelta(days=7)

        contrib_summary = aggregator._aggregate_contributions_for_week(week_start, week_end)

        assert isinstance(contrib_summary, dict)
        assert "human_percentage" in contrib_summary
        assert "ai_percentage" in contrib_summary
        assert "collaborative_percentage" in contrib_summary

    def test_calculate_weekly_trends(self, temp_metrics_dir):
        """Test weekly trend calculation"""
        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)

        current = {
            "dora": {"deployment_frequency": 1.5},
            "contributions": {"human_percentage": 40.0}
        }

        previous = {
            "dora": {"deployment_frequency": 1.0},
            "contributions": {"human_percentage": 50.0}
        }

        trends = aggregator._calculate_weekly_trends(current, previous)

        assert "dora.deployment_frequency" in trends
        assert "contributions.human_percentage" in trends

        # Check deployment frequency trend (increase)
        df_trend = trends["dora.deployment_frequency"]
        assert df_trend["change_percentage"] == 50.0
        assert df_trend["direction"] == "up"

        # Check human percentage trend (decrease)
        hp_trend = trends["contributions.human_percentage"]
        assert hp_trend["change_percentage"] == -20.0
        assert hp_trend["direction"] == "down"

    def test_edge_cases(self, temp_metrics_dir):
        """Test edge cases and error handling"""
        aggregator = MetricsAggregator(project_root=temp_metrics_dir.parent.parent)

        # Test with non-existent metrics files
        weekly = aggregator.aggregate_weekly(weeks_back=1)
        assert len(weekly) == 1

        # Test trends without weekly summaries
        trends = aggregator.analyze_trends(weeks_back=4)
        assert trends == {}

        # Test with invalid JSON
        invalid_file = temp_metrics_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("not valid json {")

        data = aggregator._load_json(invalid_file)
        assert data is None

    def test_metric_history_tracking(self, write_sample_metrics):
        """Test historical value tracking across weeks"""
        metrics_dir = write_sample_metrics

        aggregator = MetricsAggregator(project_root=metrics_dir.parent.parent)

        # Create weekly summaries
        aggregator.aggregate_weekly(weeks_back=4)

        # Analyze trends
        trends = aggregator.analyze_trends(weeks_back=4)

        # Check that historical values are tracked
        for metric_path, trend_data in trends.items():
            assert isinstance(trend_data["historical_values"], list)
            assert len(trend_data["historical_values"]) <= 4
