/**
 * Governance Dashboard
 *
 * Displays platform health metrics, scorecards, and governance insights.
 * Brand-compliant: no emojis, no gridlines, label-first visuals, spot color only.
 */

import React, { useEffect, useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';

interface ScorecardData {
  data_quality_index: number;
  model_performance_index: number;
  platform_reliability_index: number;
  security_compliance_index: number;
  timestamp: string;
}

interface TrendPoint {
  date: string;
  value: number;
}

interface TrendsData {
  data_quality: TrendPoint[];
  model_performance: TrendPoint[];
  platform_reliability: TrendPoint[];
  security_compliance: TrendPoint[];
}

interface Finding {
  kind: string;
  name: string;
  flags: string[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function Governance() {
  const { theme } = useTheme();
  const [scorecard, setScorecard] = useState<ScorecardData | null>(null);
  const [trends, setTrends] = useState<TrendsData | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchGovernanceData();
  }, []);

  const fetchGovernanceData = async () => {
    try {
      setLoading(true);

      // Fetch scorecard
      const scorecardRes = await fetch(`${API_BASE}/api/gov/scorecard`);
      if (scorecardRes.ok) {
        const scorecardData = await scorecardRes.json();
        setScorecard(scorecardData);
      }

      // Fetch trends (7 days)
      const trendsRes = await fetch(`${API_BASE}/api/gov/trends?days=7`);
      if (trendsRes.ok) {
        const trendsData = await trendsRes.json();
        setTrends(trendsData);
      }

      // Fetch recent findings from latest snapshot
      const snapshotRes = await fetch(`${API_BASE}/api/gov/snapshot/latest`);
      if (snapshotRes.ok) {
        const snapshot = await snapshotRes.json();
        setFindings(snapshot.drift_detected || []);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load governance data');
    } finally {
      setLoading(false);
    }
  };

  const getDirectional = (value: number, prevValue?: number): string => {
    if (!prevValue) return '─';
    if (value > prevValue) return '▲';
    if (value < prevValue) return '▼';
    return '─';
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return theme === 'dark' ? '#66BB6A' : '#2E7D32';
    if (score >= 75) return theme === 'dark' ? '#FFA726' : '#ED6C02';
    return theme === 'dark' ? '#EF5350' : '#D32F2F';
  };

  const renderMiniChart = (data: TrendPoint[], label: string) => {
    if (!data || data.length === 0) return null;

    const width = 200;
    const height = 60;
    const padding = 5;

    const maxValue = Math.max(...data.map(d => d.value), 100);
    const minValue = Math.min(...data.map(d => d.value), 0);
    const range = maxValue - minValue || 1;

    const points = data.map((point, i) => {
      const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((point.value - minValue) / range) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(' ');

    const spotColor = theme === 'dark' ? '#AF7DEB' : '#7823DC';
    const lineColor = theme === 'dark' ? '#A5A5A5' : '#787878';

    return (
      <div className="mini-chart">
        <svg width={width} height={height} style={{ display: 'block' }}>
          {/* No gridlines per brand requirements */}
          <polyline
            points={points}
            fill="none"
            stroke={spotColor}
            strokeWidth="2"
          />
          {/* Label-first: show current value */}
          <text
            x={width - padding}
            y={height - padding - ((data[data.length - 1].value - minValue) / range) * (height - 2 * padding)}
            fill={lineColor}
            fontSize="10"
            textAnchor="end"
            dy="-5"
          >
            {data[data.length - 1].value.toFixed(1)}
          </text>
        </svg>
        <div className="chart-label" style={{
          fontSize: '0.75rem',
          color: theme === 'dark' ? '#A5A5A5' : '#787878',
          marginTop: '0.25rem'
        }}>
          {label}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="governance-page" style={{
        padding: '2rem',
        color: theme === 'dark' ? '#FFFFFF' : '#1E1E1E',
        backgroundColor: theme === 'dark' ? '#000000' : '#FFFFFF',
      }}>
        <div>Loading governance data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="governance-page" style={{
        padding: '2rem',
        color: theme === 'dark' ? '#EF5350' : '#D32F2F',
        backgroundColor: theme === 'dark' ? '#000000' : '#FFFFFF',
      }}>
        <div>Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="governance-page" style={{
      padding: '2rem',
      color: theme === 'dark' ? '#FFFFFF' : '#1E1E1E',
      backgroundColor: theme === 'dark' ? '#000000' : '#FFFFFF',
      minHeight: '100vh',
    }}>
      <h1 style={{
        fontSize: '2rem',
        fontWeight: 700,
        marginBottom: '2rem',
        fontFamily: 'Inter, Arial, sans-serif',
      }}>
        Governance Dashboard
      </h1>

      {/* Scorecard Section */}
      {scorecard && (
        <div className="scorecard-section" style={{ marginBottom: '3rem' }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: 600,
            marginBottom: '1rem',
          }}>
            Platform Health Scorecard
          </h2>

          <div className="scorecard-tiles" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1rem',
          }}>
            {/* Data Quality */}
            <div className="scorecard-tile" style={{
              padding: '1.5rem',
              backgroundColor: theme === 'dark' ? '#1E1E1E' : '#F5F5F5',
              borderRadius: '0.25rem',
              border: `1px solid ${theme === 'dark' ? '#4B4B4B' : '#D2D2D2'}`,
            }}>
              <div style={{
                fontSize: '0.875rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
                marginBottom: '0.5rem',
              }}>
                Data Quality
              </div>
              <div style={{
                fontSize: '2.5rem',
                fontWeight: 700,
                color: getScoreColor(scorecard.data_quality_index),
                marginBottom: '0.25rem',
              }}>
                {scorecard.data_quality_index.toFixed(1)}
                <span style={{ fontSize: '1rem', marginLeft: '0.5rem' }}>
                  {getDirectional(scorecard.data_quality_index)}
                </span>
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
              }}>
                Profiling + Cleanliness
              </div>
            </div>

            {/* Model Performance */}
            <div className="scorecard-tile" style={{
              padding: '1.5rem',
              backgroundColor: theme === 'dark' ? '#1E1E1E' : '#F5F5F5',
              borderRadius: '0.25rem',
              border: `1px solid ${theme === 'dark' ? '#4B4B4B' : '#D2D2D2'}`,
            }}>
              <div style={{
                fontSize: '0.875rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
                marginBottom: '0.5rem',
              }}>
                Model Performance
              </div>
              <div style={{
                fontSize: '2.5rem',
                fontWeight: 700,
                color: getScoreColor(scorecard.model_performance_index),
                marginBottom: '0.25rem',
              }}>
                {scorecard.model_performance_index.toFixed(1)}
                <span style={{ fontSize: '1rem', marginLeft: '0.5rem' }}>
                  {getDirectional(scorecard.model_performance_index)}
                </span>
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
              }}>
                Metrics Trend + Registry
              </div>
            </div>

            {/* Platform Reliability */}
            <div className="scorecard-tile" style={{
              padding: '1.5rem',
              backgroundColor: theme === 'dark' ? '#1E1E1E' : '#F5F5F5',
              borderRadius: '0.25rem',
              border: `1px solid ${theme === 'dark' ? '#4B4B4B' : '#D2D2D2'}`,
            }}>
              <div style={{
                fontSize: '0.875rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
                marginBottom: '0.5rem',
              }}>
                Platform Reliability
              </div>
              <div style={{
                fontSize: '2.5rem',
                fontWeight: 700,
                color: getScoreColor(scorecard.platform_reliability_index),
                marginBottom: '0.25rem',
              }}>
                {scorecard.platform_reliability_index.toFixed(1)}
                <span style={{ fontSize: '1rem', marginLeft: '0.5rem' }}>
                  {getDirectional(scorecard.platform_reliability_index)}
                </span>
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
              }}>
                Latency + Error Rate + Cache
              </div>
            </div>

            {/* Security Compliance */}
            <div className="scorecard-tile" style={{
              padding: '1.5rem',
              backgroundColor: theme === 'dark' ? '#1E1E1E' : '#F5F5F5',
              borderRadius: '0.25rem',
              border: `1px solid ${theme === 'dark' ? '#4B4B4B' : '#D2D2D2'}`,
            }}>
              <div style={{
                fontSize: '0.875rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
                marginBottom: '0.5rem',
              }}>
                Security Compliance
              </div>
              <div style={{
                fontSize: '2.5rem',
                fontWeight: 700,
                color: getScoreColor(scorecard.security_compliance_index),
                marginBottom: '0.25rem',
              }}>
                {scorecard.security_compliance_index.toFixed(1)}
                <span style={{ fontSize: '1rem', marginLeft: '0.5rem' }}>
                  {getDirectional(scorecard.security_compliance_index)}
                </span>
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: theme === 'dark' ? '#A5A5A5' : '#787878',
              }}>
                Checks + Audit Anomalies
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trends Section */}
      {trends && (
        <div className="trends-section" style={{ marginBottom: '3rem' }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: 600,
            marginBottom: '1rem',
          }}>
            7-Day Trends
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1.5rem',
          }}>
            {renderMiniChart(trends.data_quality, 'Data Quality')}
            {renderMiniChart(trends.model_performance, 'Model Performance')}
            {renderMiniChart(trends.platform_reliability, 'Platform Reliability')}
            {renderMiniChart(trends.security_compliance, 'Security Compliance')}
          </div>
        </div>
      )}

      {/* Recent Findings */}
      <div className="findings-section">
        <h2 style={{
          fontSize: '1.25rem',
          fontWeight: 600,
          marginBottom: '1rem',
        }}>
          Recent Findings
        </h2>

        {findings.length === 0 ? (
          <div style={{
            padding: '1.5rem',
            backgroundColor: theme === 'dark' ? '#1E1E1E' : '#F5F5F5',
            borderRadius: '0.25rem',
            border: `1px solid ${theme === 'dark' ? '#4B4B4B' : '#D2D2D2'}`,
            color: theme === 'dark' ? '#A5A5A5' : '#787878',
          }}>
            No drift or quality issues detected.
          </div>
        ) : (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}>
            {findings.map((finding, idx) => (
              <div
                key={idx}
                style={{
                  padding: '1rem',
                  backgroundColor: theme === 'dark' ? '#1E1E1E' : '#F5F5F5',
                  borderRadius: '0.25rem',
                  border: `1px solid ${theme === 'dark' ? '#4B4B4B' : '#D2D2D2'}`,
                  borderLeft: `4px solid ${theme === 'dark' ? '#FFA726' : '#ED6C02'}`,
                }}
              >
                <div style={{
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  marginBottom: '0.25rem',
                }}>
                  {finding.kind}: {finding.name}
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: theme === 'dark' ? '#A5A5A5' : '#787878',
                }}>
                  Flags: {finding.flags.join(', ')}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Last Updated */}
      {scorecard && (
        <div style={{
          marginTop: '2rem',
          fontSize: '0.75rem',
          color: theme === 'dark' ? '#A5A5A5' : '#787878',
          textAlign: 'right',
        }}>
          Last updated: {new Date(scorecard.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
}
