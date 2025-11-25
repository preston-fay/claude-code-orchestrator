/**
 * Orchestrator Run Detail Page
 *
 * Displays detailed information about a specific orchestrator run including:
 * - Run metadata and status
 * - Phase execution details
 * - Artifacts grouped by phase
 * - Performance metrics and governance scores
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  getRun,
  advanceRun,
  getRunArtifacts,
  getRunMetrics,
  formatCost,
  formatTokens,
  formatDuration,
  getPhaseDisplayName,
  getPhaseStatusColor,
  getArtifactTypeInfo,
} from '../api/orchestrator';
import type { RunDetail, ArtifactsResponse, MetricsSummary } from '../api/orchestrator';

const OrchestratorRunDetailPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactsResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [advancing, setAdvancing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'phases' | 'artifacts' | 'metrics'>('phases');

  useEffect(() => {
    if (runId) {
      loadRun();
      loadArtifacts();
      loadMetrics();
    }
  }, [runId]);

  const loadRun = async () => {
    if (!runId) return;
    try {
      setLoading(true);
      const data = await getRun(runId);
      setRun(data);
    } catch (err) {
      setError(`Failed to load run: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const loadArtifacts = async () => {
    if (!runId) return;
    try {
      const data = await getRunArtifacts(runId);
      setArtifacts(data);
    } catch (err) {
      console.error('Failed to load artifacts:', err);
    }
  };

  const loadMetrics = async () => {
    if (!runId) return;
    try {
      const data = await getRunMetrics(runId);
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    }
  };

  const handleAdvanceRun = async () => {
    if (!runId) return;
    try {
      setAdvancing(true);
      setError(null);
      await advanceRun(runId);
      await loadRun();
      await loadArtifacts();
      await loadMetrics();
    } catch (err) {
      setError(`Failed to advance run: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setAdvancing(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading run details...</div>;
  }

  if (!run) {
    return <div className="error-banner">Run not found</div>;
  }

  return (
    <div className="page orchestrator-run-detail-page">
      <div className="page-header">
        <div>
          <h2>{run.project_name || 'Untitled Run'}</h2>
          <p className="run-id">Run ID: {run.run_id}</p>
        </div>
        <button
          className="button-primary"
          onClick={handleAdvanceRun}
          disabled={advancing || run.status === 'completed'}
        >
          {advancing ? 'Advancing...' : 'Advance to Next Phase'}
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="run-summary">
        <div className="summary-item">
          <span className="label">Profile:</span>
          <span>{run.profile}</span>
        </div>
        <div className="summary-item">
          <span className="label">Current Phase:</span>
          <span className="phase-badge">{getPhaseDisplayName(run.current_phase)}</span>
        </div>
        <div className="summary-item">
          <span className="label">Status:</span>
          <span className={`status-indicator status-${run.status}`}>{run.status}</span>
        </div>
        {run.total_duration_seconds && (
          <div className="summary-item">
            <span className="label">Duration:</span>
            <span>{formatDuration(run.total_duration_seconds)}</span>
          </div>
        )}
      </div>

      <div className="tabs">
        <button
          className={activeTab === 'phases' ? 'active' : ''}
          onClick={() => setActiveTab('phases')}
        >
          Phases ({run.phases.length})
        </button>
        <button
          className={activeTab === 'artifacts' ? 'active' : ''}
          onClick={() => setActiveTab('artifacts')}
        >
          Artifacts ({artifacts?.total_count || 0})
        </button>
        <button
          className={activeTab === 'metrics' ? 'active' : ''}
          onClick={() => setActiveTab('metrics')}
        >
          Metrics
        </button>
      </div>

      {activeTab === 'phases' && (
        <div className="phases-section">
          {run.phases.map((phase) => (
            <div key={phase.phase} className="phase-card">
              <div className="phase-header">
                <h3>{getPhaseDisplayName(phase.phase)}</h3>
                <span className={`status-badge status-${getPhaseStatusColor(phase.status)}`}>
                  {phase.status}
                </span>
              </div>
              <div className="phase-details">
                {phase.duration_seconds && <p>Duration: {formatDuration(phase.duration_seconds)}</p>}
                {phase.artifacts_count !== undefined && <p>Artifacts: {phase.artifacts_count}</p>}
                {phase.agent_ids && phase.agent_ids.length > 0 && (
                  <p>Agents: {phase.agent_ids.join(', ')}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'artifacts' && (
        <div className="artifacts-section">
          {artifacts && Object.keys(artifacts.artifacts_by_phase).length > 0 ? (
            Object.entries(artifacts.artifacts_by_phase).map(([phase, phaseArtifacts]) => (
              <div key={phase} className="artifacts-group">
                <h3>{getPhaseDisplayName(phase)} Artifacts</h3>
                <ul>
                  {phaseArtifacts.map((artifact) => {
                    const typeInfo = getArtifactTypeInfo(artifact.artifact_type);
                    return (
                      <li key={artifact.artifact_id}>
                        <span className="artifact-icon">{typeInfo.icon}</span>
                        <span className="artifact-name">{artifact.name}</span>
                        <span className="artifact-type">{artifact.artifact_type}</span>
                        <span className="artifact-size">
                          {(artifact.size_bytes / 1024).toFixed(2)} KB
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))
          ) : (
            <p>No artifacts generated yet.</p>
          )}
        </div>
      )}

      {activeTab === 'metrics' && (
        <div className="metrics-section">
          {metrics ? (
            <>
              <div className="metrics-summary">
                <div className="metric-card">
                  <h4>Total Cost</h4>
                  <p className="metric-value">{formatCost(metrics.total_cost_usd)}</p>
                </div>
                <div className="metric-card">
                  <h4>Total Tokens</h4>
                  <p className="metric-value">
                    {formatTokens(metrics.total_token_usage.input + metrics.total_token_usage.output)}
                  </p>
                  <p className="metric-detail">
                    In: {formatTokens(metrics.total_token_usage.input)} | Out:{' '}
                    {formatTokens(metrics.total_token_usage.output)}
                  </p>
                </div>
                <div className="metric-card">
                  <h4>Governance Score</h4>
                  <p className="metric-value">{(metrics.governance_score * 100).toFixed(0)}%</p>
                </div>
                <div className="metric-card">
                  <h4>Hygiene Score</h4>
                  <p className="metric-value">{(metrics.hygiene_score * 100).toFixed(0)}%</p>
                </div>
              </div>

              <h3>Phase Metrics</h3>
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Phase</th>
                    <th>Duration</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                    <th>Governance</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.phases_metrics.map((pm) => (
                    <tr key={pm.phase}>
                      <td>{getPhaseDisplayName(pm.phase)}</td>
                      <td>{formatDuration(pm.duration_seconds)}</td>
                      <td>{formatTokens(pm.token_usage.input + pm.token_usage.output)}</td>
                      <td>{formatCost(pm.cost_usd)}</td>
                      <td>{pm.governance_passed ? '✓' : '✗'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p>No metrics available yet.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default OrchestratorRunDetailPage;
