import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getProject,
  getAppBuildStatus,
  planAppBuild,
  runAppScaffold,
  getAppBuildArtifacts,
  getArtifactContent,
} from '../api/client';
import { Project, AppBuildStatus, ArtifactContent } from '../api/types';
import ArtifactViewerModal from '../components/ArtifactViewerModal';

const ProjectAppBuildPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [buildStatus, setBuildStatus] = useState<AppBuildStatus | null>(null);
  const [artifacts, setArtifacts] = useState<Array<{ id: string; name: string; path: string; artifact_type: string; created_at: string | null }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [operationLoading, setOperationLoading] = useState<string | null>(null);

  // Artifact viewer
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactContent | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadData();
    }
  }, [projectId]);

  const loadData = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);

      const [projectData, statusData, artifactsData] = await Promise.all([
        getProject(projectId),
        getAppBuildStatus(projectId).catch(() => null),
        getAppBuildArtifacts(projectId).catch(() => ({ artifacts: [], total_count: 0 })),
      ]);

      setProject(projectData);
      setBuildStatus(statusData);
      setArtifacts(artifactsData.artifacts || []);
    } catch (err) {
      setError('Failed to load app build data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanBuild = async () => {
    if (!projectId) return;

    try {
      setOperationLoading('plan');
      setError(null);
      await planAppBuild(projectId);
      await loadData();
    } catch (err) {
      setError('Failed to plan app build');
      console.error(err);
    } finally {
      setOperationLoading(null);
    }
  };

  const handleScaffold = async () => {
    if (!projectId) return;

    try {
      setOperationLoading('scaffold');
      setError(null);
      await runAppScaffold(projectId);
      await loadData();
    } catch (err) {
      setError('Failed to run scaffolding');
      console.error(err);
    } finally {
      setOperationLoading(null);
    }
  };

  const handleOpenArtifact = async (artifactId: string) => {
    if (!projectId) return;

    try {
      const content = await getArtifactContent(projectId, artifactId);
      setSelectedArtifact(content);
      setIsModalOpen(true);
    } catch (err) {
      setError('Failed to load artifact');
      console.error(err);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'planning': case 'scaffolding': return 'status-running';
      case 'failed': return 'status-failed';
      default: return 'status-pending';
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div className="loading">Loading app build...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="page">
        <div className="error-banner">
          Project not found
          <button onClick={() => navigate('/projects')}>Back to Projects</button>
        </div>
      </div>
    );
  }

  // Check if project has app_build capability
  const hasAppBuildCapability = project.capabilities?.includes('app_build') ||
                                project.capabilities?.includes('frontend_ui') ||
                                project.capabilities?.includes('backend_api');

  if (!hasAppBuildCapability) {
    return (
      <div className="page">
        <div className="page-header">
          <div className="breadcrumb">
            <button className="link-button" onClick={() => navigate('/projects')}>
              Projects
            </button>
            <span className="separator">/</span>
            <button className="link-button" onClick={() => navigate(`/projects/${projectId}`)}>
              {project.project_name}
            </button>
            <span className="separator">/</span>
            <span>App Build</span>
          </div>
        </div>
        <div className="empty-state">
          <p>This project doesn't have app building capabilities.</p>
          <p>Add the <code>app_build</code> capability to enable this feature.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="breadcrumb">
          <button className="link-button" onClick={() => navigate('/projects')}>
            Projects
          </button>
          <span className="separator">/</span>
          <button className="link-button" onClick={() => navigate(`/projects/${projectId}`)}>
            {project.project_name}
          </button>
          <span className="separator">/</span>
          <span>App Build</span>
        </div>
        <button className="button-secondary" onClick={loadData}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Build Status Section */}
      <div className="project-info-card">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Build Status</span>
            <span className={`status-indicator ${getStatusBadgeClass(buildStatus?.status || 'not_started')}`}>
              {buildStatus?.status?.replace('_', ' ') || 'Not Started'}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Artifacts</span>
            <span className="info-value">{buildStatus?.artifact_count || 0}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Target Stack</span>
            <span className="info-value">{buildStatus?.target_stack || 'React + FastAPI'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Last Updated</span>
            <span className="info-value">{formatDate(buildStatus?.last_updated_at || null)}</span>
          </div>
        </div>

        {buildStatus?.last_error && (
          <div className="section-alert" style={{ marginTop: 'var(--spacing-md)' }}>
            <strong>Error:</strong> {buildStatus.last_error}
          </div>
        )}
      </div>

      {/* Project Brief */}
      {project.brief && (
        <div className="project-info-card">
          <div className="brief-section">
            <span className="info-label">Project Brief</span>
            <p className="brief-text">{project.brief}</p>
          </div>
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
        </div>
      )}

      {/* External Links */}
      {(project.app_repo_url || project.app_url) && (
        <div className="project-info-card">
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
                  Live App
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <section className="section">
        <h3>Build Actions</h3>
        <div className="button-row">
          <button
            className="button-primary"
            onClick={handlePlanBuild}
            disabled={operationLoading !== null}
          >
            {operationLoading === 'plan' ? 'Planning...' : 'Plan App Build'}
          </button>
          <button
            className="button-primary"
            onClick={handleScaffold}
            disabled={operationLoading !== null}
          >
            {operationLoading === 'scaffold' ? 'Scaffolding...' : 'Run Scaffolding'}
          </button>
        </div>
        <p className="console-helper">
          Tip: You can also use <code>/app-plan</code> and <code>/app-scaffold</code> in the Project Console.
        </p>
      </section>

      {/* Artifacts */}
      <section className="section">
        <h3>Build Artifacts</h3>
        {artifacts.length === 0 ? (
          <div className="diagnostics-empty">
            No artifacts yet. Click "Plan App Build" to generate PRD and architecture.
          </div>
        ) : (
          <div className="artifacts-list">
            {artifacts.map((artifact) => (
              <div key={artifact.id} className="artifact-row">
                <div className="artifact-info">
                  <span className="artifact-name">{artifact.name}</span>
                  <span className="artifact-type">{artifact.artifact_type}</span>
                </div>
                <button
                  className="view-artifact-btn"
                  onClick={() => handleOpenArtifact(artifact.id)}
                >
                  View
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Artifact Viewer Modal */}
      {isModalOpen && selectedArtifact && (
        <ArtifactViewerModal
          artifact={selectedArtifact}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedArtifact(null);
          }}
        />
      )}
    </div>
  );
};

export default ProjectAppBuildPage;
