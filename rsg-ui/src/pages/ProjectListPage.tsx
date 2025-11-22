import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProjects, createProject, listProjectTemplates } from '../api/client';
import { ProjectSummary, CreateProjectPayload, ProjectTemplate } from '../api/types';

const ProjectListPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState<CreateProjectPayload>({
    project_name: '',
    client: 'kearney-default',
    template_id: undefined,
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadProjects();
    loadTemplates();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      setError('Failed to load projects. Check your API connection in Settings.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const data = await listProjectTemplates();
      setTemplates(data);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  const handleCreateProject = async () => {
    if (!newProject.project_name.trim()) {
      return;
    }

    try {
      setCreating(true);
      const created = await createProject(newProject);
      setProjects([...projects, created]);
      setShowCreateModal(false);
      setNewProject({ project_name: '', client: 'kearney-default', template_id: undefined });
      navigate(`/projects/${created.project_id}`);
    } catch (err) {
      setError('Failed to create project');
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

  const getProjectTypeBadge = (type: string) => {
    switch (type) {
      case 'analytics_forecasting':
        return 'Analytics';
      case 'territory_poc':
        return 'Territory';
      case 'app_build':
        return 'App Build';
      case 'generic':
        return 'Blank';
      default:
        return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }
  };

  return (
    <div className="page project-list-page">
      <div className="page-header">
        <h2>Projects</h2>
        <button className="button-primary" onClick={() => setShowCreateModal(true)}>
          New Project
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={loadProjects}>Retry</button>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="empty-state">
          <p>No projects found.</p>
          <p>Create your first project to get started with Ready/Set/Go.</p>
          <div className="golden-path-hint">
            <h4>Quick Start</h4>
            <p>Click "New Project" and select a template to begin.</p>
            <p className="hint-text">Or run the Golden Path demo:</p>
            <code>python scripts/dev/run_golden_path_demo.py</code>
          </div>
        </div>
      ) : (
        <table className="project-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Client</th>
              <th>Current Phase</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <tr
                key={project.project_id}
                onClick={() => navigate(`/projects/${project.project_id}`)}
                className="clickable-row"
              >
                <td className="project-name">
                  {project.project_name}
                  {project.project_name.startsWith('Golden Path') && (
                    <span className="badge badge-demo">Demo</span>
                  )}
                </td>
                <td>
                  <span className="project-type-tag">
                    {getProjectTypeBadge(project.project_type)}
                  </span>
                </td>
                <td>{project.client}</td>
                <td>
                  <span className="phase-badge">{project.current_phase}</span>
                </td>
                <td>
                  <span className={`status-indicator status-${project.status}`}>
                    {project.status}
                  </span>
                </td>
                <td>{formatDate(project.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content new-project-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Project</h2>
              <button className="close-button" onClick={() => setShowCreateModal(false)}>
                &times;
              </button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="projectName">Project Name</label>
                <input
                  id="projectName"
                  type="text"
                  value={newProject.project_name}
                  onChange={(e) =>
                    setNewProject({ ...newProject, project_name: e.target.value })
                  }
                  placeholder="My New Project"
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label>Select Template</label>
                <div className="template-cards">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className={`template-card ${newProject.template_id === template.id ? 'selected' : ''}`}
                      onClick={() => setNewProject({ ...newProject, template_id: template.id })}
                    >
                      <div className="template-name">{template.name}</div>
                      <div className="template-description">{template.description}</div>
                      <div className="template-category">{template.category}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="client">Client</label>
                <input
                  id="client"
                  type="text"
                  value={newProject.client}
                  onChange={(e) =>
                    setNewProject({ ...newProject, client: e.target.value })
                  }
                  placeholder="kearney-default"
                />
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="button-secondary"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </button>
              <button
                className="button-primary"
                onClick={handleCreateProject}
                disabled={creating || !newProject.project_name.trim()}
              >
                {creating ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectListPage;
