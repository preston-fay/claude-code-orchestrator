/**
 * Orchestrator Runs List Page
 *
 * Displays a list of all orchestrator runs with their status, phase, and metadata.
 * Includes filtering by status and profile, pagination, and navigation to run details.
 * Allows creating new runs via modal.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  listRuns,
  createRun,
  getPhaseDisplayName,
  type RunSummary,
  type CreateRunRequest,
  type ListRunsParams,
} from '../api/orchestrator';
import IntakeWizard from '../components/IntakeWizard';

const OrchestratorRunsPage: React.FC = () => {
  const navigate = useNavigate();

  // Runs list state
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [profileFilter, setProfileFilter] = useState<string>('');

  // Pagination state
  const [limit] = useState<number>(20);
  const [offset, setOffset] = useState<number>(0);
  const [total, setTotal] = useState<number>(0);

  // Create run modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showIntakeWizard, setShowIntakeWizard] = useState(false);
  const [newRun, setNewRun] = useState<CreateRunRequest>({
    profile: 'analytics_forecast_app',
    intake: '',
    project_name: '',
  });
  const [creating, setCreating] = useState(false);

  // Load runs effect
  useEffect(() => {
    loadRuns();
  }, [statusFilter, profileFilter, limit, offset]);

  const loadRuns = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: ListRunsParams = {
        limit,
        offset,
      };

      if (statusFilter) params.status = statusFilter;
      if (profileFilter.trim()) params.profile = profileFilter.trim();

      const response = await listRuns(params);

      setRuns(response.runs);
      setTotal(response.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load runs';
      setError(message);
      console.error('[OrchestratorRunsPage] Failed to load runs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRun = async () => {
    if (!newRun.profile.trim()) {
      setError('Profile is required');
      return;
    }

    try {
      setCreating(true);
      setError(null);

      const created = await createRun(newRun);

      // Close modal and reset form
      setShowCreateModal(false);
      setNewRun({ profile: 'analytics_forecast_app', intake: '', project_name: '' });

      // Navigate to the new run's detail page
      navigate(`/orchestrator/runs/${created.run_id}`);
    } catch (err) {
      setError(`Failed to create run: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error('[OrchestratorRunsPage] Failed to create run:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleIntakeWizardComplete = async (projectId: string) => {
    // Close the intake wizard
    setShowIntakeWizard(false);
    
    // Navigate to the newly created project
    navigate(`/projects/${projectId}`);
  };

  const handleIntakeWizardCancel = () => {
    setShowIntakeWizard(false);
  };

  const handleStartIntakeWizard = () => {
    setShowCreateModal(false);
    setShowIntakeWizard(true);
  };

  const handleResetFilters = () => {
    setStatusFilter('');
    setProfileFilter('');
    setOffset(0);
  };

  const handlePreviousPage = () => {
    setOffset(Math.max(0, offset - limit));
  };

  const handleNextPage = () => {
    if (offset + limit < total) {
      setOffset(offset + limit);
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

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);
  const hasFilters = statusFilter !== '' || profileFilter.trim() !== '';

  return (
    <div className="page orchestrator-runs-page">
      <div className="page-header">
        <h2>Orchestrator Runs</h2>
        <div className="header-actions">
          <button className="button-primary" onClick={() => setShowIntakeWizard(true)}>
            New Project (Guided)
          </button>
          <button className="button-secondary" onClick={() => setShowCreateModal(true)}>
            Quick Run
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Filters */}
      <div className="filters-bar">
        <div className="filter-group">
          <label htmlFor="status-filter">Status:</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setOffset(0); // Reset to first page when filtering
            }}
          >
            <option value="">All</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="profile-filter">Profile:</label>
          <input
            id="profile-filter"
            type="text"
            value={profileFilter}
            onChange={(e) => {
              setProfileFilter(e.target.value);
              setOffset(0); // Reset to first page when filtering
            }}
            placeholder="e.g., analytics_forecast_app"
          />
        </div>

        {hasFilters && (
          <button className="button-secondary" onClick={handleResetFilters}>
            Reset Filters
          </button>
        )}
      </div>

      {/* Loading state */}
      {loading ? (
        <div className="loading">Loading runs...</div>
      ) : runs.length === 0 ? (
        // Empty state
        <div className="empty-state">
          {hasFilters ? (
            <>
              <p>No runs match the current filters.</p>
              <button className="button-secondary" onClick={handleResetFilters}>
                Clear Filters
              </button>
            </>
          ) : (
            <>
              <p>No runs found.</p>
              <p>Create your first orchestrator run to get started.</p>
              <button className="button-primary" onClick={() => setShowCreateModal(true)}>
                Create Run
              </button>
            </>
          )}
        </div>
      ) : (
        // Runs table
        <>
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
                  <td className="run-id" title={run.run_id}>
                    {run.run_id.slice(0, 8)}...
                  </td>
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

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination-controls">
              <button
                className="button-secondary"
                onClick={handlePreviousPage}
                disabled={offset === 0}
              >
                &larr; Previous
              </button>

              <span className="pagination-info">
                Page {currentPage} of {totalPages} ({total} total runs)
              </span>

              <button
                className="button-secondary"
                onClick={handleNextPage}
                disabled={offset + limit >= total}
              >
                Next &rarr;
              </button>
            </div>
          )}
        </>
      )}

      {/* Create Run Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content new-project-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Quick Create Run</h2>
              <button className="close-button" onClick={() => setShowCreateModal(false)}>
                &times;
              </button>
            </div>

            <div className="modal-body">
              <div className="creation-options">
                <p>Choose how you'd like to create your project:</p>
                <div className="option-buttons">
                  <button 
                    className="option-button guided" 
                    onClick={handleStartIntakeWizard}
                  >
                    <div className="option-icon">🧙‍♂️</div>
                    <h3>Guided Interview</h3>
                    <p>Answer structured questions to build a comprehensive project specification</p>
                  </button>
                  <div className="option-divider">OR</div>
                </div>
              </div>

              <h3>Quick Manual Creation</h3>
              <div className="form-group">
                <label htmlFor="profile">Profile *</label>
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

      {/* Intake Wizard */}
      {showIntakeWizard && (
        <div className="modal-overlay" style={{ zIndex: 1000 }}>
          <IntakeWizard
            onComplete={handleIntakeWizardComplete}
            onCancel={handleIntakeWizardCancel}
            clientSlug="kearney-default"
          />
        </div>
      )}
    </div>
  );
};

export default OrchestratorRunsPage;
