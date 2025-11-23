import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getProject,
  listFeatures,
  createFeature,
  planFeature,
  buildFeature,
} from '../api/client';
import { Project, Feature } from '../api/types';

const ProjectFeaturesPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [operationLoading, setOperationLoading] = useState<string | null>(null);

  // New feature form
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');

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

      const [projectData, featuresData] = await Promise.all([
        getProject(projectId),
        listFeatures(projectId).catch(() => ({ features: [], total_count: 0 })),
      ]);

      setProject(projectData);
      setFeatures(featuresData.features || []);
    } catch (err) {
      setError('Failed to load features');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFeature = async () => {
    if (!projectId || !newTitle.trim()) return;

    try {
      setOperationLoading('create');
      setError(null);
      await createFeature(projectId, {
        title: newTitle.trim(),
        description: newDescription.trim(),
      });
      setNewTitle('');
      setNewDescription('');
      await loadData();
    } catch (err) {
      setError('Failed to create feature');
      console.error(err);
    } finally {
      setOperationLoading(null);
    }
  };

  const handlePlanFeature = async (featureId: string) => {
    if (!projectId) return;

    try {
      setOperationLoading(`plan-${featureId}`);
      setError(null);
      await planFeature(projectId, featureId);
      await loadData();
    } catch (err) {
      setError(`Failed to plan feature ${featureId}`);
      console.error(err);
    } finally {
      setOperationLoading(null);
    }
  };

  const handleBuildFeature = async (featureId: string) => {
    if (!projectId) return;

    try {
      setOperationLoading(`build-${featureId}`);
      setError(null);
      await buildFeature(projectId, featureId);
      await loadData();
    } catch (err) {
      setError(`Failed to build feature ${featureId}`);
      console.error(err);
    } finally {
      setOperationLoading(null);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'planned': case 'building': return 'status-running';
      case 'failed': return 'status-failed';
      default: return 'status-pending';
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div className="loading">Loading features...</div>
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
          <span>Features</span>
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

      {/* New Feature Form */}
      <section className="section">
        <h3>Create New Feature</h3>
        <div className="form-group">
          <label>Title</label>
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Feature title"
          />
        </div>
        <div className="form-group">
          <label>Description</label>
          <textarea
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            placeholder="Describe the feature..."
            rows={3}
          />
        </div>
        <button
          className="button-primary"
          onClick={handleCreateFeature}
          disabled={!newTitle.trim() || operationLoading === 'create'}
        >
          {operationLoading === 'create' ? 'Creating...' : 'Create Feature'}
        </button>
      </section>

      {/* Features List */}
      <section className="section">
        <h3>Features ({features.length})</h3>

        {features.length === 0 ? (
          <div className="diagnostics-empty">
            No features yet. Create one above or use <code>/new-feature "Title"</code> in the console.
          </div>
        ) : (
          <table className="project-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => (
                <tr key={feature.feature_id}>
                  <td><strong>{feature.feature_id}</strong></td>
                  <td>
                    <span className="project-name">{feature.title}</span>
                    {feature.description && (
                      <small style={{ display: 'block', color: 'var(--text-muted)' }}>
                        {feature.description.substring(0, 60)}
                        {feature.description.length > 60 ? '...' : ''}
                      </small>
                    )}
                  </td>
                  <td>
                    <span className={`status-indicator ${getStatusBadgeClass(feature.status)}`}>
                      {feature.status}
                    </span>
                  </td>
                  <td>{feature.priority}</td>
                  <td>{formatDate(feature.updated_at)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
                      {(feature.status === 'submitted') && (
                        <button
                          className="button-small"
                          onClick={() => handlePlanFeature(feature.feature_id)}
                          disabled={operationLoading === `plan-${feature.feature_id}`}
                        >
                          {operationLoading === `plan-${feature.feature_id}` ? '...' : 'Plan'}
                        </button>
                      )}
                      {(feature.status === 'planned' || feature.status === 'submitted') && (
                        <button
                          className="button-small"
                          onClick={() => handleBuildFeature(feature.feature_id)}
                          disabled={operationLoading === `build-${feature.feature_id}`}
                        >
                          {operationLoading === `build-${feature.feature_id}` ? '...' : 'Build'}
                        </button>
                      )}
                      {feature.artifact_count > 0 && (
                        <span className="pill">{feature.artifact_count} artifacts</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Console Tip */}
      <p className="console-helper">
        Tip: You can also manage features from the Project Console using commands like{' '}
        <code>/new-feature "Title"</code>, <code>/plan-feature F-001</code>, <code>/build-feature F-001</code>
      </p>
    </div>
  );
};

export default ProjectFeaturesPage;
