import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProjects, createProject } from '../api/client';
import { ProjectSummary, CreateProjectPayload } from '../api/types';

const ProjectListPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState<CreateProjectPayload>({
    project_name: '',
    client: 'kearney-default',
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadProjects();
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

  const handleCreateProject = async () => {
    if (!newProject.project_name.trim()) {
      return;
    }

    try {
      setCreating(true);
      const created = await createProject(newProject);
      setProjects([...projects, created]);
      setShowCreateModal(false);
      setNewProject({ project_name: '', client: 'kearney-default' });
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

  return (
    <div className="page project-list-page">
      <div className="page-header">
        <h2>Projects</h2>
        <button className="button-primary" onClick={() => setShowCreateModal(true)}>
          Create Project
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
        </div>
      ) : (
        <table className="project-table">
          <thead>
            <tr>
              <th>Name</th>
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
                <td className="project-name">{project.project_name}</td>
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
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
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
