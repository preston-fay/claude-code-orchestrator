import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getProject,
  runPhase,
  getProjectCheckpoints,
  getProjectArtifacts,
  getArtifactContent,
  getPhaseDiagnostics
} from '../api/client';
import { Project, Checkpoint, ArtifactsResponse, ArtifactContent, PhaseDiagnostics } from '../api/types';
import RsgStatus from '../components/RsgStatus';
import RunActivityPanel from '../components/RunActivityPanel';
import ArtifactViewerModal from '../components/ArtifactViewerModal';

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

  // Artifact viewer state
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactContent | null>(null);
  const [isArtifactModalOpen, setIsArtifactModalOpen] = useState(false);
  const [artifactLoadingId, setArtifactLoadingId] = useState<string | null>(null);

  // Diagnostics state
  const [selectedDiagnosticsPhase, setSelectedDiagnosticsPhase] = useState<string | null>(null);
  const [phaseDiagnostics, setPhaseDiagnostics] = useState<PhaseDiagnostics | null>(null);
  const [isDiagnosticsLoading, setIsDiagnosticsLoading] = useState(false);
  const [diagnosticsError, setDiagnosticsError] = useState<string | null>(null);

  // Collapsed phases in artifacts
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  // Get phases - use API response or derive from default
  const getProjectPhases = (): string[] => {
    if (project?.phases && project.phases.length > 0) {
      return project.phases;
    }
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
      await loadProject();
    } catch (err) {
      setError(`Failed to run phase: ${phaseName}`);
      console.error(err);
    } finally {
      setRunningPhase(null);
    }
  };

  const handleOpenArtifact = async (artifactId: string) => {
    if (!projectId) return;

    try {
      setArtifactLoadingId(artifactId);
      const content = await getArtifactContent(projectId, artifactId);
      setSelectedArtifact(content);
      setIsArtifactModalOpen(true);
    } catch (err) {
      console.error('Failed to open artifact', err);
      setError('Unable to load artifact content');
    } finally {
      setArtifactLoadingId(null);
    }
  };

  const handleLoadDiagnostics = async (phase: string) => {
    if (!projectId) return;

    setSelectedDiagnosticsPhase(phase);
    setIsDiagnosticsLoading(true);
    setDiagnosticsError(null);

    try {
      const diag = await getPhaseDiagnostics(projectId, phase);
      setPhaseDiagnostics(diag);
    } catch (err) {
      console.error('Failed to load diagnostics', err);
      setDiagnosticsError(`Unable to load diagnostics for phase ${phase}`);
    } finally {
      setIsDiagnosticsLoading(false);
    }
  };

  const togglePhaseExpanded = (phase: string) => {
    setExpandedPhases(prev => {
      const next = new Set(prev);
      if (next.has(phase)) {
        next.delete(phase);
      } else {
        next.add(phase);
      }
      return next;
    });
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

    return phaseIndex <= currentIndex;
  };

  // RSG stage helpers
  const getRsgStage = (currentPhase: string): string => {
    const readyPhases = ['planning', 'architecture'];
    const setPhases = ['data', 'development'];
    const goPhases = ['qa', 'documentation'];

    if (readyPhases.includes(currentPhase)) return 'ready';
    if (setPhases.includes(currentPhase)) return 'set';
    if (goPhases.includes(currentPhase)) return 'go';
    return 'ready';
  };

  const isRsgStageCompleted = (stage: 'ready' | 'set' | 'go'): boolean => {
    if (!project?.completed_phases) return false;

    const stagePhases = {
      ready: ['planning', 'architecture'],
      set: ['data', 'development'],
      go: ['qa', 'documentation'],
    };

    return stagePhases[stage].every(phase =>
      project.completed_phases?.includes(phase)
    );
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
          currentStage={getRsgStage(project.current_phase)}
          readyCompleted={isRsgStageCompleted('ready')}
          setCompleted={isRsgStageCompleted('set')}
          goCompleted={isRsgStageCompleted('go')}
        />
      </section>

      {/* Phase List with Diagnostics */}
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
                  {status === 'completed' && (
                    <button
                      className="link-button phase-link"
                      onClick={() => handleLoadDiagnostics(phase)}
                    >
                      Diagnostics
                    </button>
                  )}
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

      {/* Phase Diagnostics Panel */}
      <section className="section">
        <div className="diagnostics-panel">
          <h3>Phase Diagnostics</h3>

          {!selectedDiagnosticsPhase && (
            <div className="diagnostics-empty">
              Select a completed phase above and click <span className="pill">Diagnostics</span> to see execution details.
            </div>
          )}

          {selectedDiagnosticsPhase && isDiagnosticsLoading && (
            <div className="diagnostics-empty">
              Loading diagnostics for {selectedDiagnosticsPhase}...
            </div>
          )}

          {diagnosticsError && (
            <div className="section-alert">
              {diagnosticsError}
            </div>
          )}

          {selectedDiagnosticsPhase && phaseDiagnostics && !isDiagnosticsLoading && !diagnosticsError && (
            <div className="diagnostics-grid">
              <div className="diagnostics-card">
                <h4>Agents</h4>
                {phaseDiagnostics.agents?.length ? (
                  <ul className="diagnostics-list">
                    {phaseDiagnostics.agents.map((agent, i) => (
                      <li key={i}>{agent}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="diagnostics-empty">No agent data</p>
                )}
              </div>

              <div className="diagnostics-card">
                <h4>Skills</h4>
                {phaseDiagnostics.skills?.length ? (
                  <ul className="diagnostics-list">
                    {phaseDiagnostics.skills.map((skill, i) => (
                      <li key={i}>{skill}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="diagnostics-empty">No skills invoked</p>
                )}
              </div>

              <div className="diagnostics-card">
                <h4>Artifacts</h4>
                {phaseDiagnostics.artifacts?.length ? (
                  <ul className="diagnostics-list">
                    {phaseDiagnostics.artifacts.map((artifact, i) => (
                      <li key={i}>{artifact}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="diagnostics-empty">No artifacts</p>
                )}
              </div>

              <div className="diagnostics-card">
                <h4>Token Usage</h4>
                {phaseDiagnostics.token_usage && Object.keys(phaseDiagnostics.token_usage).length > 0 ? (
                  <ul className="diagnostics-list">
                    {phaseDiagnostics.token_usage.input !== undefined && (
                      <li>Input: <span className="diagnostics-value">{phaseDiagnostics.token_usage.input}</span></li>
                    )}
                    {phaseDiagnostics.token_usage.output !== undefined && (
                      <li>Output: <span className="diagnostics-value">{phaseDiagnostics.token_usage.output}</span></li>
                    )}
                    {phaseDiagnostics.token_usage.total !== undefined && (
                      <li>Total: <span className="diagnostics-value">{phaseDiagnostics.token_usage.total}</span></li>
                    )}
                  </ul>
                ) : (
                  <p className="diagnostics-empty">No token data</p>
                )}
              </div>

              <div className="diagnostics-card">
                <h4>Governance</h4>
                {phaseDiagnostics.governance ? (
                  <div className="diagnostics-value">
                    {phaseDiagnostics.governance.passed !== undefined
                      ? (phaseDiagnostics.governance.passed ? 'Passed' : 'Failed')
                      : 'Unknown'}
                  </div>
                ) : (
                  <p className="diagnostics-empty">No governance data</p>
                )}
              </div>

              {phaseDiagnostics.timestamp && (
                <div className="diagnostics-card">
                  <h4>Timestamp</h4>
                  <div className="diagnostics-value">
                    {formatDate(phaseDiagnostics.timestamp)}
                  </div>
                </div>
              )}
            </div>
          )}
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
      <section className="section">
        <div className="artifacts-panel">
          <h3>Artifacts</h3>

          {!artifacts || artifacts.total_count === 0 ? (
            <div className="diagnostics-empty">
              No artifacts yet. Run a phase or use the console to generate outputs.
            </div>
          ) : (
            Object.entries(artifacts.artifacts_by_phase).map(([phase, phaseArtifacts]) => (
              <div key={phase} className="artifacts-phase-group">
                <button
                  className="artifacts-phase-header"
                  onClick={() => togglePhaseExpanded(phase)}
                >
                  <span>{phase}</span>
                  <span className="artifacts-phase-count">({phaseArtifacts.length})</span>
                  <span className="expand-icon">{expandedPhases.has(phase) ? '▼' : '▶'}</span>
                </button>

                {expandedPhases.has(phase) && (
                  <div className="artifacts-list">
                    {phaseArtifacts.map((artifact) => (
                      <div key={artifact.id} className="artifact-row">
                        <div className="artifact-info">
                          <span className="artifact-name">{artifact.name}</span>
                          <span className="artifact-type">{artifact.artifact_type}</span>
                        </div>
                        <button
                          className="view-artifact-btn"
                          onClick={() => handleOpenArtifact(artifact.id)}
                          disabled={artifactLoadingId === artifact.id}
                        >
                          {artifactLoadingId === artifact.id ? 'Loading...' : 'View'}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </section>

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

      {/* Artifact Viewer Modal */}
      {isArtifactModalOpen && selectedArtifact && (
        <ArtifactViewerModal
          artifact={selectedArtifact}
          onClose={() => setIsArtifactModalOpen(false)}
        />
      )}
    </div>
  );
};

export default ProjectDetailPage;
