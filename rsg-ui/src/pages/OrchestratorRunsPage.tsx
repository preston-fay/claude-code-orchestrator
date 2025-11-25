/**
 * Orchestrator Runs List Page
 *
 * Displays a list of all orchestrator runs with their status, phase, and metadata.
 * Allows creating new runs and navigating to run detail pages.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createRun, getPhaseDisplayName } from '../api/orchestrator';
import type { RunSummary, CreateRunRequest } from '../api/orchestrator';

const OrchestratorRunsPage: React.FC = () => {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRun, setNewRun] = useState<CreateRunRequest>({
    profile: 'analytics_forecast_app',
    intake: '',
    project_name: '',
  });
  const [creating, setCreating] = useState(false);

  const handleCreateRun = async () => {
    if (!newRun.profile.trim()) {
      setError('Profile is required');
      return;
    }

    try {
      setCreating(true);
      setError(null);
      const created = await createRun(newRun);
      setRuns([created, ...runs]);
      setShowCreateModal(false);
      setNewRun({ profile: 'analytics_forecast_app', intake: '', project_name: '' });
      navigate(`/orchestrator/runs/${created.run_id}`);
    } catch (err) {
      setError(`Failed to create run: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="page orchestrator-runs-page">
      <div className="page-header">
        <h2>Orchestrator Runs</h2>
        <button className="button-primary" onClick={() => setShowCreateModal(true)}>
          New Run
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading runs...</div>
      ) : runs.length === 0 ? (
        <div className="empty-state">
          <p>No runs found.</p>
          <p>Create your first orchestrator run to get started.</p>
          <button className="button-primary" onClick={() => setShowCreateModal(true)}>
            Create Run
          </button>
        </div>
      ) : (
        <table className="project-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Profile</th>
              <th>Project Name</th>
              <th>Current Phase</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr
                key={run.run_id}
                onClick={() => navigate(`/orchestrator/runs/${run.run_id}`)}
                className="clickable-row"
              >
                <td className="run-id">{run.run_id.slice(0, 8)}...</td>
                <td>{run.profile}</td>
                <td>{run.project_name || <em>Untitled</em>}</td>
                <td>
                  <span className="phase-badge">{getPhaseDisplayName(run.current_phase)}</span>
                </td>
                <td>
                  <span className={`status-indicator status-${run.status}`}>{run.status}</span>
                </td>
                <td>{formatDate(run.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content new-project-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Run</h2>
              <button className="close-button" onClick={() => setShowCreateModal(false)}>
                &times;
              </button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="profile">Profile</label>
                <select
                  id="profile"
                  value={newRun.profile}
                  onChange={(e) => setNewRun({ ...newRun, profile: e.target.value })}
                >
                  <option value="analytics_forecast_app">Analytics Forecast App</option>
                  <option value="ml_classification">ML Classification</option>
                  <option value="optimization">Optimization</option>
                  <option value="data_engineering">Data Engineering</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="projectName">Project Name (Optional)</label>
                <input
                  id="projectName"
                  type="text"
                  value={newRun.project_name || ''}
                  onChange={(e) => setNewRun({ ...newRun, project_name: e.target.value })}
                  placeholder="My Orchestrator Project"
                />
              </div>

              <div className="form-group">
                <label htmlFor="intake">Intake (Optional)</label>
                <textarea
                  id="intake"
                  value={newRun.intake || ''}
                  onChange={(e) => setNewRun({ ...newRun, intake: e.target.value })}
                  placeholder="Describe your project requirements..."
                  rows={4}
                />
              </div>
            </div>

            <div className="modal-footer">
              <button className="button-secondary" onClick={() => setShowCreateModal(false)}>
                Cancel
              </button>
              <button
                className="button-primary"
                onClick={handleCreateRun}
                disabled={creating || !newRun.profile.trim()}
              >
                {creating ? 'Creating...' : 'Create Run'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrchestratorRunsPage;
