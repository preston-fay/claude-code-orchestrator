import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, getProjectCheckpoints, startReady, startSet, startGo, deleteProject } from '../api/client';
import { Project, Checkpoint } from '../api/types';
import RsgStatus from '../components/RsgStatus';
import RunActivityPanel from '../components/RunActivityPanel';

const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rsgLoading, setRsgLoading] = useState(false);

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

  const handleStartReady = async () => {
    if (!projectId) return;
    try {
      setRsgLoading(true);
      setError(null);
      await startReady(projectId);
      await loadProject();
    } catch (err) {
      setError('Failed to start Ready phase');
      console.error(err);
    } finally {
      setRsgLoading(false);
    }
  };

  const handleStartSet = async () => {
    if (!projectId) return;
    try {
      setRsgLoading(true);
      setError(null);
      await startSet(projectId);
      await loadProject();
    } catch (err) {
      setError('Failed to start Set phase');
      console.error(err);
    } finally {
      setRsgLoading(false);
    }
  };

  const handleStartGo = async () => {
    if (!projectId) return;
    try {
      setRsgLoading(true);
      setError(null);
      await startGo(projectId);
      await loadProject();
    } catch (err) {
      setError('Failed to start Go phase');
      console.error(err);
    } finally {
      setRsgLoading(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!projectId || !project) return;
    if (!window.confirm(`Are you sure you want to delete "${project.project_name}"?`)) {
      return;
    }
    try {
      await deleteProject(projectId);
      navigate('/projects');
    } catch (err) {
      setError('Failed to delete project');
      console.error(err);
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

  // Determine RSG stage completion based on completed phases
  const getReadyCompleted = (): boolean => {
    if (!project) return false;
    return project.completed_phases.includes('planning') &&
           project.completed_phases.includes('architecture');
  };

  const getSetCompleted = (): boolean => {
    if (!project) return false;
    const hasData = !project.phases.includes('data') || project.completed_phases.includes('data');
    const hasDev = project.completed_phases.includes('development');
    return hasData && hasDev;
  };

  const getGoCompleted = (): boolean => {
    if (!project) return false;
    return project.completed_phases.includes('qa') &&
           project.completed_phases.includes('documentation');
  };

  const getCurrentStage = (): string => {
    if (!project) return 'ready';
    if (getGoCompleted()) return 'complete';
    if (getSetCompleted()) return 'go';
    if (getReadyCompleted()) return 'set';
    return 'ready';
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
          <button className="button-secondary" onClick={loadProject}>
            Refresh
          </button>
          <button className="button-danger" onClick={handleDeleteProject}>
            Delete
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Project Info */}
      <div className="project-info-card">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Type</span>
            <span className="info-value project-type-value">{project.project_type || 'generic'}</span>
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
        </div>

        {/* Capabilities Badges */}
        {project.capabilities && project.capabilities.length > 0 && (
          <div className="capabilities-section">
            <span className="info-label">Capabilities</span>
            <div className="capability-badges">
              {project.capabilities.map((cap) => (
                <span key={cap} className="capability-badge">{cap.replace(/_/g, ' ')}</span>
              ))}
            </div>
          </div>
        )}

        {/* Project Brief */}
        {project.brief && (
          <div className="brief-section">
            <span className="info-label">Project Brief</span>
            <p className="brief-text">{project.brief}</p>
          </div>
        )}

        {project.workspace_path && (
          <div className="workspace-path">
            <span className="info-label">Workspace</span>
            <code className="info-value">{project.workspace_path}</code>
          </div>
        )}

        {/* External Links */}
        {(project.app_repo_url || project.app_url) && (
          <div className="external-links-section">
            <span className="info-label">Deliverables</span>
            <div className="external-links">
              {project.app_repo_url && (
                <a href={project.app_repo_url} target="_blank" rel="noopener noreferrer" className="external-link">
                  Code Repository
                </a>
              )}
              {project.app_url && (
                <a href={project.app_url} target="_blank" rel="noopener noreferrer" className="external-link">
                  Live Application
                </a>
              )}
            </div>
          </div>
        )}
      </div>

      {/* RSG Macro Status */}
      <section className="section">
        <h3>Ready / Set / Go Status</h3>
        <RsgStatus
          currentStage={getCurrentStage()}
          readyCompleted={getReadyCompleted()}
          setCompleted={getSetCompleted()}
          goCompleted={getGoCompleted()}
          onStartReady={handleStartReady}
          onStartSet={handleStartSet}
          onStartGo={handleStartGo}
          loading={rsgLoading}
        />
      </section>

      {/* Phase List */}
      <section className="section">
        <h3>Phases</h3>
        <div className="phase-list">
          {project.phases.map((phase, index) => {
            const isCompleted = project.completed_phases.includes(phase);
            const isCurrent = project.current_phase === phase;
            const status = isCompleted ? 'completed' : isCurrent ? 'in_progress' : 'pending';

            return (
              <div key={phase} className={`phase-item phase-${status}`}>
                <div className="phase-number">{index + 1}</div>
                <div className="phase-info">
                  <span className="phase-name">{phase}</span>
                  <span className={`phase-status status-${status}`}>
                    {isCompleted ? 'Completed' : isCurrent ? 'Current' : 'Pending'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Run Activity */}
      {projectId && (
        <section className="section">
          <RunActivityPanel
            projectId={projectId}
            isRunning={rsgLoading}
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
