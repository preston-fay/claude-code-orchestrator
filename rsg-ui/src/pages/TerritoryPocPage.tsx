import React, { useState } from 'react';
import {
  runTerritoryScoring,
  runTerritoryClustering,
  getTerritoryAssignments,
  getTerritoryKpis,
  TerritoryAssignment,
  TerritoryKpi,
  TerritoryConfig,
} from '../api/client';

const TerritoryPocPage: React.FC = () => {
  // Configuration state
  const [workspacePath, setWorkspacePath] = useState('/home/user/workspaces/territory_poc');
  const [territoryCount, setTerritoryCount] = useState(12);
  const [valueWeight, setValueWeight] = useState(0.5);
  const [opportunityWeight, setOpportunityWeight] = useState(0.3);
  const [workloadWeight, setWorkloadWeight] = useState(0.2);

  // Results state
  const [assignments, setAssignments] = useState<TerritoryAssignment[]>([]);
  const [kpis, setKpis] = useState<TerritoryKpi[]>([]);
  const [selectedTerritory, setSelectedTerritory] = useState<string | null>(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');

  const buildConfig = (): TerritoryConfig => ({
    workspace_path: workspacePath,
    intake_config: {
      territory: {
        target_territories: territoryCount,
        states: ['IA', 'IL', 'IN'],
      },
      scoring: {
        weights: {
          value_weight: valueWeight,
          opportunity_weight: opportunityWeight,
          workload_weight: workloadWeight,
        },
      },
    },
  });

  const handleRunScoring = async () => {
    setLoading(true);
    setError(null);
    setStatus('Running scoring...');

    try {
      const result = await runTerritoryScoring(buildConfig());
      if (result.success) {
        setStatus(`Scoring complete. ${result.metadata.retailer_count} retailers scored.`);
      } else {
        setError(result.error || 'Scoring failed');
      }
    } catch (err) {
      setError(`Scoring failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunClustering = async () => {
    setLoading(true);
    setError(null);
    setStatus('Running clustering...');

    try {
      const result = await runTerritoryClustering(buildConfig());
      if (result.success) {
        setStatus(`Clustering complete. ${result.metadata.territory_count} territories created.`);
        // Load results
        await loadResults();
      } else {
        setError(result.error || 'Clustering failed');
      }
    } catch (err) {
      setError(`Clustering failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunBoth = async () => {
    await handleRunScoring();
    if (!error) {
      await handleRunClustering();
    }
  };

  const loadResults = async () => {
    try {
      const [assignmentsData, kpisData] = await Promise.all([
        getTerritoryAssignments(workspacePath),
        getTerritoryKpis(workspacePath),
      ]);
      setAssignments(assignmentsData.assignments);
      setKpis(kpisData.kpis);
    } catch (err) {
      setError(`Failed to load results: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const filteredAssignments = selectedTerritory
    ? assignments.filter((a) => a.territory_id === selectedTerritory)
    : assignments;

  const exportToCsv = () => {
    if (assignments.length === 0) return;

    const headers = [
      'retail_id',
      'retail_name',
      'state',
      'territory_id',
      'rvs',
      'ros',
      'rws',
      'composite_score',
    ];
    const rows = assignments.map((a) =>
      [a.retail_id, a.retail_name, a.state, a.territory_id, a.rvs, a.ros, a.rws, a.composite_score].join(',')
    );
    const csv = [headers.join(','), ...rows].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'territory_assignments.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page territory-poc-page">
      <div className="page-header">
        <h2>Territory POC - IA/IL/IN Retail Realignment</h2>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="territory-layout">
        {/* Control Panel */}
        <div className="territory-controls">
          <h3>Configuration</h3>

          <div className="form-group">
            <label>Workspace Path</label>
            <input
              type="text"
              value={workspacePath}
              onChange={(e) => setWorkspacePath(e.target.value)}
              placeholder="/home/user/workspaces/territory_poc"
            />
          </div>

          <div className="form-group">
            <label>Number of Territories</label>
            <input
              type="number"
              min="2"
              max="50"
              value={territoryCount}
              onChange={(e) => setTerritoryCount(parseInt(e.target.value) || 12)}
            />
          </div>

          <h4>Score Weights</h4>
          <div className="weight-controls">
            <div className="form-group">
              <label>Value (RVS): {valueWeight.toFixed(2)}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={valueWeight}
                onChange={(e) => setValueWeight(parseFloat(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Opportunity (ROS): {opportunityWeight.toFixed(2)}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={opportunityWeight}
                onChange={(e) => setOpportunityWeight(parseFloat(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Workload (RWS): {workloadWeight.toFixed(2)}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={workloadWeight}
                onChange={(e) => setWorkloadWeight(parseFloat(e.target.value))}
              />
            </div>
          </div>

          <div className="control-buttons">
            <button className="button-primary" onClick={handleRunBoth} disabled={loading}>
              {loading ? 'Running...' : 'Run Full Pipeline'}
            </button>
            <button className="button-secondary" onClick={handleRunScoring} disabled={loading}>
              Score Only
            </button>
            <button className="button-secondary" onClick={handleRunClustering} disabled={loading}>
              Cluster Only
            </button>
          </div>

          {status && <div className="status-message">{status}</div>}
        </div>

        {/* Results Panel */}
        <div className="territory-results">
          {/* KPI Summary */}
          {kpis.length > 0 && (
            <div className="kpi-section">
              <div className="section-header">
                <h3>Territory KPIs</h3>
                <button className="button-secondary" onClick={exportToCsv}>
                  Export CSV
                </button>
              </div>
              <table className="kpi-table">
                <thead>
                  <tr>
                    <th>Territory</th>
                    <th>Retailers</th>
                    <th>Revenue</th>
                    <th>Avg RVS</th>
                    <th>Avg ROS</th>
                    <th>Avg RWS</th>
                    <th>Coverage (km)</th>
                  </tr>
                </thead>
                <tbody>
                  {kpis.map((kpi) => (
                    <tr
                      key={kpi.territory_id}
                      className={selectedTerritory === kpi.territory_id ? 'selected' : ''}
                      onClick={() =>
                        setSelectedTerritory(
                          selectedTerritory === kpi.territory_id ? null : kpi.territory_id
                        )
                      }
                    >
                      <td className="territory-id">{kpi.territory_id}</td>
                      <td>{kpi.retailer_count}</td>
                      <td>${kpi.total_revenue.toLocaleString()}</td>
                      <td>{kpi.avg_rvs.toFixed(3)}</td>
                      <td>{kpi.avg_ros.toFixed(3)}</td>
                      <td>{kpi.avg_rws.toFixed(3)}</td>
                      <td>{kpi.coverage_km.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Assignments Table */}
          {assignments.length > 0 && (
            <div className="assignments-section">
              <h3>
                Retailer Assignments
                {selectedTerritory && ` - ${selectedTerritory}`}
                <span className="count">({filteredAssignments.length} retailers)</span>
              </h3>
              <div className="assignments-table-wrapper">
                <table className="assignments-table">
                  <thead>
                    <tr>
                      <th>Retailer</th>
                      <th>State</th>
                      <th>Territory</th>
                      <th>RVS</th>
                      <th>ROS</th>
                      <th>RWS</th>
                      <th>Composite</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAssignments.slice(0, 100).map((assignment, idx) => (
                      <tr key={`${assignment.retail_id}-${idx}`}>
                        <td className="retailer-name">{assignment.retail_name || assignment.retail_id}</td>
                        <td>{assignment.state}</td>
                        <td className="territory-id">{assignment.territory_id}</td>
                        <td>{assignment.rvs.toFixed(3)}</td>
                        <td>{assignment.ros.toFixed(3)}</td>
                        <td>{assignment.rws.toFixed(3)}</td>
                        <td>{assignment.composite_score.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredAssignments.length > 100 && (
                  <div className="truncation-notice">
                    Showing first 100 of {filteredAssignments.length} retailers
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Empty state */}
          {assignments.length === 0 && !loading && (
            <div className="empty-state">
              <p>No territory assignments yet.</p>
              <p>Configure parameters and click "Run Full Pipeline" to generate territories.</p>
              <div className="setup-hint">
                <h4>Setup Instructions</h4>
                <ol>
                  <li>
                    Place <code>Retailer_Segmentation_CROP.xlsx</code> in:
                    <br />
                    <code>{workspacePath}/data/</code>
                  </li>
                  <li>Adjust territory count and score weights as needed</li>
                  <li>Click "Run Full Pipeline" to score and cluster retailers</li>
                </ol>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TerritoryPocPage;
