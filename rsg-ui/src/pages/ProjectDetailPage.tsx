import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getProject, runPhase, getProjectCheckpoints } from '../api/client';
import { Project, Checkpoint } from '../api/types';
import RsgStatus from '../components/RsgStatus';
import RunActivityPanel from '../components/RunActivityPanel';
import LlmSettings from '../components/LlmSettings';

// Standard phases for different project types
const STANDARD_PHASES = ['planning', 'architecture', 'data', 'development', 'qa', 'documentation'];
const APP_BUILD_PHASES = ['scaffolding', 'development', 'qa', 'documentation'];
const TERRITORY_PHASES = ['planning', 'data', 'development', 'qa'];

function getPhasesForProjectType(projectType: string): string[] {
  switch (projectType) {
    case 'app_build':
      return APP_BUILD_PHASES;
    case 'territory_poc':
      return TERRITORY_PHASES;
    default:
      return STANDARD_PHASES;
  }
}

const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningPhase, setRunningPhase] = useState<string | null>(null);

  // Derive phases from project type
  const phases = project ? getPhasesForProjectType(project.project_type) : [];

  useEffect(() => {
    if (projectId) {
      loadProject();
    }
  }, [projectId]);

  const loadProject = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);
      const [projectData, checkpointData] = await Promise.all([
        getProject(projectId),
        getProjectCheckpoints(projectId),
      ]);
      setProject(projectData);
      setCheckpoints(checkpointData);
    } catch (err) {
      setError('Failed to load project details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPhase = async (phaseName: string) => {
    if (!projectId) return;

    try {
      setRunningPhase(phaseName);
      setError(null);
      await runPhase(projectId, phaseName);
      // Reload project to get updated state
      await loadProject();
    } catch (err) {
      setError(`Failed to run phase: ${phaseName}`);
      console.error(err);
    } finally {
      setRunningPhase(null);
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

  const getPhaseStatus = (phaseName: string): 'pending' | 'in_progress' | 'completed' | 'failed' => {
    if (!project) return 'pending';

    // Check if phase is in completed_phases
    const completedPhases = project.completed_phases || [];
    if (completedPhases.includes(phaseName)) {
      return 'completed';
    }

    // Check if it's the current phase
    if (phaseName === project.current_phase) {
      if (project.status === 'running') return 'in_progress';
      if (project.status === 'failed') return 'failed';
      return 'in_progress'; // Current phase but not running = ready to run
    }

    return 'pending';
  };

  const canRunPhase = (phaseName: string): boolean => {
    if (!project || runningPhase) return false;
    if (project.status === 'running') return false;

    const completedPhases = project.completed_phases || [];

    // Can run if it's current phase or already completed (re-run)
    return phaseName === project.current_phase || completedPhases.includes(phaseName);
  };

  if (loading) {
    return (
      <div className="page project-detail-page">
        <div className="loading">Loading project...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="page project-detail-page">
        <div className="error-banner">
          Project not found
          <button onClick={() => navigate('/projects')}>Back to Projects</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page project-detail-page">
      <div className="page-header">
        <div className="breadcrumb">
          <button className="link-button" onClick={() => navigate('/projects')}>
            Projects
          </button>
          <span className="separator">/</span>
          <span>{project.project_name}</span>
        </div>
        <div className="header-actions">
          <Link to={`/projects/${projectId}/features`} className="feature-link">
            Features
          </Link>
          {project.project_type === 'app_build' && (
            <Link to={`/projects/${projectId}/build`} className="app-build-link">
              App Build
            </Link>
          )}
          <button className="button-secondary" onClick={loadProject}>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Project Info & Settings */}
      <div className="project-settings-row">
        <div className="project-info-card">
          <h4>Project Info</h4>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Type</span>
              <span className="info-value">
                <span className="project-type-badge">{project.project_type || 'generic'}</span>
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Client</span>
              <span className="info-value">{project.client}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Status</span>
              <span className={`status-indicator status-${project.status}`}>
                {project.status}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Created</span>
              <span className="info-value">{formatDate(project.created_at)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Current Phase</span>
              <span className="info-value phase-badge">{project.current_phase}</span>
            </div>
          </div>
          {project.workspace_path && (
            <div className="workspace-path">
              <span className="info-label">Workspace</span>
              <div className="workspace-value">
                <code>{project.workspace_path}</code>
                <button
                  className="copy-btn"
                  onClick={() => {
                    navigator.clipboard.writeText(project.workspace_path || '');
                  }}
                  title="Copy to clipboard"
                >
                  Copy
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="llm-settings-card">
          <LlmSettings compact />
        </div>
      </div>

      {/* RSG Macro Status */}
      <section className="section">
        <h3>Ready / Set / Go Status</h3>
        <RsgStatus
          currentStage={
            (project.completed_phases || []).includes('qa') ? 'go' :
            (project.completed_phases || []).includes('development') ? 'go' :
            (project.completed_phases || []).includes('data') ? 'set' :
            (project.completed_phases || []).includes('architecture') ? 'set' :
            'ready'
          }
          readyCompleted={(project.completed_phases || []).some(p =>
            ['planning', 'architecture'].includes(p)
          )}
          setCompleted={(project.completed_phases || []).some(p =>
            ['data', 'development'].includes(p)
          )}
          goCompleted={(project.completed_phases || []).some(p =>
            ['qa', 'documentation'].includes(p)
          )}
        />
      </section>

      {/* Phase List */}
      <section className="section">
        <h3>Phases</h3>
        {phases.length === 0 ? (
          <div className="empty-state">
            <p>No phases defined for this project type.</p>
          </div>
        ) : (
        <div className="phase-list">
          {phases.map((phase, index) => {
            const status = getPhaseStatus(phase);
            const canRun = canRunPhase(phase);
            const isRunning = runningPhase === phase;

            return (
              <div key={phase} className={`phase-item phase-${status}`}>
                <div className="phase-number">{index + 1}</div>
                <div className="phase-info">
                  <span className="phase-name">{phase}</span>
                  <span className={`phase-status status-${status}`}>
                    {isRunning ? 'Running...' : status}
                  </span>
                </div>
                <div className="phase-actions">
                  {canRun && (
                    <button
                      className="button-small"
                      onClick={() => handleRunPhase(phase)}
                      disabled={isRunning}
                    >
                      {status === 'completed' ? 'Re-run' : 'Run'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        )}
      </section>

      {/* Run Activity */}
      {projectId && (
        <section className="section">
          <RunActivityPanel
            projectId={projectId}
            isRunning={runningPhase !== null}
          />
        </section>
      )}

      {/* Checkpoints */}
      <section className="section">
        <h3>Checkpoints</h3>
        {checkpoints.length === 0 ? (
          <div className="empty-state">
            <p>No checkpoints yet. Run a phase to create checkpoints.</p>
          </div>
        ) : (
          <div className="checkpoint-list">
            {checkpoints.map((checkpoint) => (
              <div key={checkpoint.checkpoint_id} className="checkpoint-item">
                <div className="checkpoint-header">
                  <span className="checkpoint-phase">{checkpoint.phase}</span>
                  <span className={`checkpoint-status status-${checkpoint.status}`}>
                    {checkpoint.status}
                  </span>
                </div>
                <div className="checkpoint-meta">
                  <span className="checkpoint-agent">Agent: {checkpoint.agent_id}</span>
                  <span className="checkpoint-time">{formatDate(checkpoint.created_at)}</span>
                </div>
                {checkpoint.artifacts && checkpoint.artifacts.length > 0 && (
                  <div className="checkpoint-artifacts">
                    <span className="artifacts-label">Artifacts:</span>
                    <ul>
                      {checkpoint.artifacts.map((artifact, i) => (
                        <li key={i}>{artifact}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default ProjectDetailPage;
