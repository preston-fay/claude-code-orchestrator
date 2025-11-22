import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProjects, createProject, listProjectTemplates } from '../api/client';
import { ProjectSummary, CreateProjectPayload, ProjectTemplate, CAPABILITIES, getCapabilityLabel } from '../api/types';

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
    capabilities: [],
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
      setNewProject({ project_name: '', client: 'kearney-default', template_id: undefined, capabilities: [] });
      navigate(`/projects/${created.project_id}`);
    } catch (err) {
      setError('Failed to create project');
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const handleTemplateSelect = (template: ProjectTemplate) => {
    setNewProject({
      ...newProject,
      template_id: template.id,
      capabilities: [...template.default_capabilities],
    });
  };

  const handleCapabilityToggle = (capabilityId: string) => {
    const currentCapabilities = newProject.capabilities || [];
    const isSelected = currentCapabilities.includes(capabilityId);

    if (isSelected) {
      setNewProject({
        ...newProject,
        capabilities: currentCapabilities.filter(c => c !== capabilityId),
      });
    } else {
      setNewProject({
        ...newProject,
        capabilities: [...currentCapabilities, capabilityId],
      });
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
      case 'application':
        return 'App';
      case 'service':
        return 'API';
      case 'ml_classification':
        return 'ML';
      case 'ml_regression':
        return 'ML';
      case 'optimization':
        return 'Optimization';
      case 'data_engineering':
        return 'Data Eng';
      default:
        return type;
    }
  };

  const getCapabilitiesSummary = (capabilities: string[]) => {
    if (!capabilities || capabilities.length === 0) {
      return null;
    }
    // Show first 2 capabilities, then "+N more" if needed
    const labels = capabilities.slice(0, 2).map(c => {
      // Short labels for compact display
      const cap = CAPABILITIES.find(cap => cap.id === c);
      if (!cap) return c;
      // Shorten labels for badges
      return cap.label
        .replace(' (Forecasting)', '')
        .replace(' (BI Dashboard)', '')
        .replace(' (Classification)', '')
        .replace(' (Regression)', '')
        .replace(' / UI', '')
        .replace(' / API', '');
    });
    const more = capabilities.length > 2 ? ` +${capabilities.length - 2}` : '';
    return labels.join(' · ') + more;
  };

  const selectedTemplate = templates.find(t => t.id === newProject.template_id);
  const canOverrideCapabilities = selectedTemplate?.allow_capability_override !== false;

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
          </div>
        </div>
      ) : (
        <table className="project-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Capabilities</th>
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
                </td>
                <td>
                  <span className="project-type-tag">
                    {getProjectTypeBadge(project.project_type)}
                  </span>
                </td>
                <td>
                  {project.capabilities && project.capabilities.length > 0 ? (
                    <span className="capabilities-badge">
                      {getCapabilitiesSummary(project.capabilities)}
                    </span>
                  ) : (
                    <span className="no-capabilities">—</span>
                  )}
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
                      onClick={() => handleTemplateSelect(template)}
                    >
                      <div className="template-name">{template.name}</div>
                      <div className="template-description">{template.description}</div>
                      <div className="template-category">{template.category}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Capabilities for this project</label>
                {!canOverrideCapabilities && selectedTemplate && (
                  <p className="hint-text">This template has fixed capabilities.</p>
                )}
                <div className="capabilities-grid">
                  {CAPABILITIES.map((capability) => {
                    const isSelected = (newProject.capabilities || []).includes(capability.id);
                    return (
                      <label
                        key={capability.id}
                        className={`capability-checkbox ${isSelected ? 'selected' : ''} ${!canOverrideCapabilities ? 'disabled' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleCapabilityToggle(capability.id)}
                          disabled={!canOverrideCapabilities}
                        />
                        <span className="capability-label">{capability.label}</span>
                      </label>
                    );
                  })}
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
