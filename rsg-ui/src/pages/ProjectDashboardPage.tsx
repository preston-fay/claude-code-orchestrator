import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  getProject,
  getRsgOverview,
  getProjectArtifacts,
  listFeatures,
  getAppBuildStatus,
  getPhaseDiagnostics,
} from '../api/client';
import {
  Project,
  RsgOverview,
  ArtifactsResponse,
  Feature,
  AppBuildStatus,
  PhaseDiagnostics,
} from '../api/types';

const ProjectDashboardPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [rsgOverview, setRsgOverview] = useState<RsgOverview | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactsResponse | null>(null);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [appBuildStatus, setAppBuildStatus] = useState<AppBuildStatus | null>(null);
  const [diagnostics, setDiagnostics] = useState<PhaseDiagnostics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (projectId) {
      loadDashboardData();
    }
  }, [projectId]);

  const loadDashboardData = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);

      // Load all dashboard data in parallel
      const [projectData, rsgData, artifactsData, featuresData, appBuildData] =
        await Promise.all([
          getProject(projectId),
          getRsgOverview(projectId).catch(() => null),
          getProjectArtifacts(projectId).catch(() => null),
          listFeatures(projectId).catch(() => ({ features: [] })),
          getAppBuildStatus(projectId).catch(() => null),
        ]);

      setProject(projectData);
      setRsgOverview(rsgData);
      setArtifacts(artifactsData);
      setFeatures(featuresData.features || []);
      setAppBuildStatus(appBuildData);

      // Load diagnostics for completed phases
      const completedPhases = projectData.completed_phases || [];
      const diagnosticsData = await Promise.all(
        completedPhases.map((phase) =>
          getPhaseDiagnostics(projectId, phase).catch(() => null)
        )
      );
      setDiagnostics(diagnosticsData.filter((d): d is PhaseDiagnostics => d !== null));
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getTotalTokens = () => {
    return diagnostics.reduce((total, diag) => {
      return total + (diag.token_usage?.total || 0);
    }, 0);
  };

  const getTotalErrors = () => {
    return diagnostics.reduce((total, diag) => {
      return total + (diag.errors?.length || 0);
    }, 0);
  };

  const getFeaturesByStatus = () => {
    const statusCounts: Record<string, number> = {};
    features.forEach((f) => {
      statusCounts[f.status] = (statusCounts[f.status] || 0) + 1;
    });
    return statusCounts;
  };

  const getArtifactCountByPhase = () => {
    if (!artifacts) return {};
    const counts: Record<string, number> = {};
    Object.entries(artifacts.artifacts_by_phase).forEach(([phase, arts]) => {
      counts[phase] = arts.length;
    });
    return counts;
  };

  const getRsgStageStatus = () => {
    if (!rsgOverview) return 'Not Started';
    if (rsgOverview.go.status === 'completed') return 'Complete';
    if (rsgOverview.go.status === 'in_progress') return 'Go';
    if (rsgOverview.set.status === 'in_progress') return 'Set';
    if (rsgOverview.ready.status === 'in_progress') return 'Ready';
    if (rsgOverview.ready.status === 'completed') return 'Ready Complete';
    return rsgOverview.current_stage || 'Not Started';
  };

  if (loading) {
    return (
      <div className="page dashboard-page">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="page dashboard-page">
        <div className="error-banner">
          {error || 'Project not found'}
          <button onClick={() => navigate('/projects')}>Back to Projects</button>
        </div>
      </div>
    );
  }

  const artifactCounts = getArtifactCountByPhase();
  const featureCounts = getFeaturesByStatus();

  return (
    <div className="page dashboard-page">
      {/* Breadcrumb and Navigation */}
      <div className="dashboard-header">
        <div className="breadcrumb">
          <Link to="/projects">Projects</Link> / {project.project_name} / Dashboard
        </div>
        <div className="dashboard-tabs">
          <Link to={`/projects/${projectId}`} className="tab-link">
            Overview
          </Link>
          <Link to={`/projects/${projectId}/dashboard`} className="tab-link active">
            Dashboard
          </Link>
          <Link to={`/projects/${projectId}/features`} className="tab-link">
            Features
          </Link>
          <Link to={`/projects/${projectId}/app-build`} className="tab-link">
            App Build
          </Link>
        </div>
      </div>

      <h1>Project Dashboard</h1>

      {/* Capabilities */}
      <section className="dashboard-section">
        <h2>Capabilities</h2>
        <div className="capabilities-display dashboard-capabilities">
          {project.capabilities?.map((cap) => (
            <span key={cap} className="capability-chip">
              {cap.replace(/_/g, ' ')}
            </span>
          )) || <span className="empty-text">No capabilities defined</span>}
        </div>
      </section>

      {/* Key Metrics Grid */}
      <div className="dashboard-grid">
        {/* RSG Stage */}
        <div className="dashboard-card">
          <h3>RSG Stage</h3>
          <div className="metric-value">{getRsgStageStatus()}</div>
          <div className="metric-detail">
            {rsgOverview && (
              <div className="rsg-progress-mini">
                <span className={rsgOverview.ready.status === 'completed' ? 'complete' : ''}>
                  Ready {rsgOverview.ready.planning_complete && rsgOverview.ready.architecture_complete ? '✓' : '○'}
                </span>
                <span className={rsgOverview.set.status === 'completed' ? 'complete' : ''}>
                  Set {rsgOverview.set.data_complete && rsgOverview.set.development_complete ? '✓' : '○'}
                </span>
                <span className={rsgOverview.go.status === 'completed' ? 'complete' : ''}>
                  Go {rsgOverview.go.qa_complete && rsgOverview.go.documentation_complete ? '✓' : '○'}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Total Artifacts */}
        <div className="dashboard-card">
          <h3>Total Artifacts</h3>
          <div className="metric-value">{artifacts?.total_count || 0}</div>
          <div className="metric-detail">
            {Object.entries(artifactCounts).slice(0, 3).map(([phase, count]) => (
              <span key={phase} className="phase-count">
                {phase}: {count}
              </span>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="dashboard-card">
          <h3>Features</h3>
          <div className="metric-value">{features.length}</div>
          <div className="metric-detail">
            {Object.entries(featureCounts).map(([status, count]) => (
              <span key={status} className={`status-count status-${status}`}>
                {status}: {count}
              </span>
            ))}
          </div>
        </div>

        {/* App Build Status */}
        <div className="dashboard-card">
          <h3>App Build</h3>
          <div className="metric-value">
            {appBuildStatus?.status || 'not_started'}
          </div>
          <div className="metric-detail">
            {appBuildStatus && (
              <>
                <span>Artifacts: {appBuildStatus.artifact_count}</span>
                {appBuildStatus.target_stack && (
                  <span>Stack: {appBuildStatus.target_stack}</span>
                )}
              </>
            )}
          </div>
        </div>

        {/* Token Usage */}
        <div className="dashboard-card">
          <h3>LLM Tokens Used</h3>
          <div className="metric-value">{getTotalTokens().toLocaleString()}</div>
          <div className="metric-detail">
            Across {diagnostics.length} phases
          </div>
        </div>

        {/* Errors */}
        <div className="dashboard-card">
          <h3>Errors</h3>
          <div className={`metric-value ${getTotalErrors() > 0 ? 'error-count' : ''}`}>
            {getTotalErrors()}
          </div>
          <div className="metric-detail">
            {getTotalErrors() === 0 ? 'No errors' : 'Review diagnostics'}
          </div>
        </div>
      </div>

      {/* Artifacts by Phase */}
      <section className="dashboard-section">
        <h2>Artifacts by Phase</h2>
        <div className="artifacts-by-phase">
          {Object.entries(artifactCounts).length > 0 ? (
            Object.entries(artifactCounts).map(([phase, count]) => (
              <div key={phase} className="phase-artifact-row">
                <span className="phase-name">{phase}</span>
                <div className="artifact-bar">
                  <div
                    className="artifact-bar-fill"
                    style={{
                      width: `${Math.min(100, (count / (artifacts?.total_count || 1)) * 100 * 3)}%`,
                    }}
                  />
                </div>
                <span className="artifact-count">{count}</span>
              </div>
            ))
          ) : (
            <div className="empty-text">No artifacts yet</div>
          )}
        </div>
      </section>

      {/* Latest Errors */}
      {getTotalErrors() > 0 && (
        <section className="dashboard-section">
          <h2>Latest Errors</h2>
          <div className="error-list">
            {diagnostics
              .flatMap((d) =>
                d.errors.map((err, i) => ({
                  phase: d.phase,
                  error: err,
                  key: `${d.phase}-${i}`,
                }))
              )
              .slice(0, 5)
              .map(({ phase, error, key }) => (
                <div key={key} className="error-item">
                  <span className="error-phase">{phase}</span>
                  <span className="error-message">{error}</span>
                </div>
              ))}
          </div>
        </section>
      )}

      {/* Project Info */}
      <section className="dashboard-section">
        <h2>Project Info</h2>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Type</span>
            <span className="info-value">{project.project_type}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Client</span>
            <span className="info-value">{project.client}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Current Phase</span>
            <span className="info-value">{project.current_phase}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Status</span>
            <span className={`status-indicator status-${project.status}`}>
              {project.status}
            </span>
          </div>
          {project.app_repo_url && (
            <div className="info-item">
              <span className="info-label">Repository</span>
              <a
                href={project.app_repo_url}
                target="_blank"
                rel="noopener noreferrer"
                className="info-link"
              >
                View on GitHub
              </a>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default ProjectDashboardPage;
