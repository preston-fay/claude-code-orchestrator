import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, runPhase, getProjectCheckpoints, getProjectArtifacts } from '../api/client';
import { Project, Checkpoint, ArtifactsResponse } from '../api/types';
import RsgStatus from '../components/RsgStatus';
import RunActivityPanel from '../components/RunActivityPanel';

// Default phases for capability-driven projects
const DEFAULT_PHASES = ['planning', 'architecture', 'data', 'development', 'qa', 'documentation'];

const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningPhase, setRunningPhase] = useState<string | null>(null);

  // Get phases - use API response or derive from default
  const getProjectPhases = (): string[] => {
    if (project?.phases && project.phases.length > 0) {
      return project.phases;
    }
    // Use default phases based on completed phases
    return DEFAULT_PHASES;
  };

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
      const [projectData, checkpointData, artifactsData] = await Promise.all([
        getProject(projectId),
        getProjectCheckpoints(projectId),
        getProjectArtifacts(projectId).catch(() => null),
      ]);
      setProject(projectData);
      setCheckpoints(checkpointData);
      setArtifacts(artifactsData);
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

    const phases = getProjectPhases();
    const phaseIndex = phases.indexOf(phaseName);
    const currentIndex = phases.indexOf(project.current_phase);

    // Check if in completed phases
    if (project.completed_phases?.includes(phaseName)) return 'completed';

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

    const phases = getProjectPhases();
    const phaseIndex = phases.indexOf(phaseName);
    const currentIndex = phases.indexOf(project.current_phase);

    // Can run current phase or any completed phase (re-run)
    return phaseIndex <= currentIndex;
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

      {/* Brief & Capabilities */}
      {(project.brief || (project.capabilities && project.capabilities.length > 0)) && (
        <div className="project-info-card">
          {project.brief && (
            <div className="brief-section">
              <span className="info-label">Brief</span>
              <p className="brief-text">{project.brief}</p>
            </div>
          )}
          {project.capabilities && project.capabilities.length > 0 && (
            <div className="capabilities-section">
              <span className="info-label">Capabilities</span>
              <div className="capability-badges">
                {project.capabilities.map((cap) => (
                  <span key={cap} className="capability-badge">{cap}</span>
                ))}
              </div>
            </div>
          )}
          {project.app_repo_url && (
            <div className="external-links">
              <span className="info-label">External Links</span>
              <div className="link-list">
                {project.app_repo_url && (
                  <a href={project.app_repo_url} target="_blank" rel="noopener noreferrer">
                    Repository
                  </a>
                )}
                {project.app_url && (
                  <a href={project.app_url} target="_blank" rel="noopener noreferrer">
                    App
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* RSG Macro Status */}
      <section className="section">
        <h3>Ready / Set / Go Status</h3>
        <RsgStatus
          currentPhase={project.current_phase}
          phases={getProjectPhases()}
          status={project.status}
        />
      </section>

      {/* Phase List */}
      <section className="section">
        <h3>Phases</h3>
        <div className="phase-list">
          {getProjectPhases().map((phase, index) => {
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

      {/* Artifacts */}
      {artifacts && artifacts.total_count > 0 && (
        <section className="section">
          <h3>Planning & Architecture Artifacts</h3>
          <div className="artifacts-panel">
            {Object.entries(artifacts.artifacts_by_phase).map(([phase, phaseArtifacts]) => (
              <div key={phase} className="artifact-phase-group">
                <h4 className="phase-name capitalize">{phase}</h4>
                <ul className="artifact-list">
                  {phaseArtifacts.map((artifact) => (
                    <li key={artifact.id} className="artifact-item">
                      <span className="artifact-name">{artifact.name}</span>
                      <span className="artifact-type">{artifact.artifact_type}</span>
                      <span className="artifact-size">
                        {(artifact.size_bytes / 1024).toFixed(1)} KB
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
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
