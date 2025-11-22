import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, runPhase, getProjectCheckpoints } from '../api/client';
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
  const [runningPhase, setRunningPhase] = useState<string | null>(null);

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

  // Derive phases from project or use default RSG phases
  const phases = project?.phases ?? ['planning', 'architecture', 'data', 'development', 'qa', 'documentation'];

  const getPhaseStatus = (phaseName: string): 'pending' | 'in_progress' | 'completed' | 'failed' => {
    if (!project) return 'pending';

    const phaseIndex = phases.indexOf(phaseName);
    const currentIndex = phases.indexOf(project.current_phase);

    if (phaseIndex < currentIndex) return 'completed';
    if (phaseIndex === currentIndex) {
      if (project.status === 'running') return 'in_progress';
      if (project.status === 'failed') return 'failed';
      return 'pending';
    }
    return 'pending';
  };

  const canRunPhase = (phaseName: string): boolean => {
    if (!project || runningPhase) return false;
    if (project.status === 'running') return false;

    const phaseIndex = phases.indexOf(phaseName);
    const currentIndex = phases.indexOf(project.current_phase);

    // Can run current phase or any completed phase (re-run)
    return phaseIndex <= currentIndex;
  };

  // Determine RSG stage completion based on completed_phases
  const getReadyCompleted = (): boolean => {
    if (!project) return false;
    const readyPhases = ['planning', 'architecture'];
    return readyPhases.every(p => project.completed_phases?.includes(p));
  };

  const getSetCompleted = (): boolean => {
    if (!project) return false;
    const setPhases = ['data', 'development'];
    return setPhases.every(p => project.completed_phases?.includes(p));
  };

  const getGoCompleted = (): boolean => {
    if (!project) return false;
    const goPhases = ['qa', 'documentation'];
    return goPhases.every(p => project.completed_phases?.includes(p));
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
        <button className="button-secondary" onClick={loadProject}>
          Refresh
        </button>
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
        {project.workspace_path && (
          <div className="workspace-path">
            <span className="info-label">Workspace</span>
            <code className="info-value">{project.workspace_path}</code>
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
        />
      </section>

      {/* Phase List */}
      <section className="section">
        <h3>Phases</h3>
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
