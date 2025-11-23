import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProjects, createProject, listProjectTemplates } from '../api/client';
import { ProjectSummary, CreateProjectPayload, ProjectTemplate } from '../api/types';

const LaunchpadPage: React.FC = () => {
  const navigate = useNavigate();
  const [recentProjects, setRecentProjects] = useState<ProjectSummary[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);
  const [newProject, setNewProject] = useState<CreateProjectPayload>({
    project_name: '',
    client: 'kearney-default',
    template_id: undefined,
    brief: '',
    capabilities: [],
    auto_create_repo: false,
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [projectsData, templatesData] = await Promise.all([
        listProjects(),
        listProjectTemplates(),
      ]);
      // Sort by created_at descending and take top 6
      const sorted = projectsData.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setRecentProjects(sorted.slice(0, 6));
      setTemplates(templatesData);
    } catch (err) {
      setError('Failed to load data. Check your API connection in Settings.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (template: ProjectTemplate) => {
    setSelectedTemplate(template);
    const now = new Date();
    const monthYear = now.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    setNewProject({
      project_name: `${template.title} (${monthYear})`,
      client: 'kearney-default',
      template_id: template.id,
      brief: template.suggested_brief,
      capabilities: template.default_capabilities,
      auto_create_repo: false,
    });
    setShowCreateModal(true);
  };

  const handleCreateProject = async () => {
    if (!newProject.project_name.trim()) {
      return;
    }

    try {
      setCreating(true);
      const created = await createProject(newProject);
      setShowCreateModal(false);
      setSelectedTemplate(null);
      setNewProject({
        project_name: '',
        client: 'kearney-default',
        template_id: undefined,
        brief: '',
        capabilities: [],
        auto_create_repo: false,
      });
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
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const getTemplateIcon = (icon: string) => {
    const icons: Record<string, string> = {
      analytics: '📊',
      classification: '🏷️',
      regression: '📈',
      optimization: '⚙️',
      webapp: '🌐',
      api: '🔌',
      dashboard: '📉',
      blank: '📄',
      default: '📁',
    };
    return icons[icon] || icons.default;
  };

  return (
    <div className="page launchpad-page">
      <div className="launchpad-header">
        <h1>RSC Launchpad</h1>
        <p className="launchpad-subtitle">Build smarter with Ready-Set-Code</p>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={loadData}>Retry</button>
        </div>
      )}

      {/* Quick Actions */}
      <section className="launchpad-section">
        <h2>Quick Actions</h2>
        <div className="quick-actions">
          <button
            className="button-primary quick-action-btn"
            onClick={() => {
              setSelectedTemplate(null);
              setNewProject({
                project_name: '',
                client: 'kearney-default',
                template_id: undefined,
                brief: '',
                capabilities: [],
                auto_create_repo: false,
              });
              setShowCreateModal(true);
            }}
          >
            Start New Project
          </button>
        </div>
      </section>

      {/* Template Catalog */}
      <section className="launchpad-section">
        <h2>Template Catalog</h2>
        {loading ? (
          <div className="loading">Loading templates...</div>
        ) : (
          <div className="launchpad-grid">
            {templates.map((template) => (
              <div key={template.id} className="template-card-v2">
                <div className="template-icon">{getTemplateIcon(template.icon)}</div>
                <div className="template-content">
                  <h3 className="template-title">{template.title}</h3>
                  <p className="template-desc">{template.description}</p>
                  <div className="template-capabilities">
                    {template.default_capabilities.slice(0, 3).map((cap) => (
                      <span key={cap} className="capability-chip">
                        {cap.replace(/_/g, ' ')}
                      </span>
                    ))}
                    {template.default_capabilities.length > 3 && (
                      <span className="capability-chip more">
                        +{template.default_capabilities.length - 3}
                      </span>
                    )}
                  </div>
                  <div className="template-best-for">
                    <span className="best-for-label">Best for:</span> {template.best_for}
                  </div>
                </div>
                <button
                  className="button-primary template-start-btn"
                  onClick={() => handleTemplateSelect(template)}
                >
                  Start Project
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Recent Projects */}
      <section className="launchpad-section">
        <div className="section-header">
          <h2>Recent Projects</h2>
          <button className="link-button" onClick={() => navigate('/projects')}>
            View all projects
          </button>
        </div>
        {loading ? (
          <div className="loading">Loading projects...</div>
        ) : recentProjects.length === 0 ? (
          <div className="empty-state">
            <p>No projects yet. Start by selecting a template above.</p>
          </div>
        ) : (
          <div className="recent-projects-grid">
            {recentProjects.map((project) => (
              <div
                key={project.project_id}
                className="recent-project-card"
                onClick={() => navigate(`/projects/${project.project_id}`)}
              >
                <div className="project-card-header">
                  <span className="project-name">{project.project_name}</span>
                  <span className={`status-indicator status-${project.status}`}>
                    {project.status}
                  </span>
                </div>
                <div className="project-card-body">
                  <div className="project-meta">
                    <span className="phase-badge">{project.current_phase}</span>
                    <span className="project-date">{formatDate(project.created_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content new-project-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {selectedTemplate
                  ? `Create ${selectedTemplate.title}`
                  : 'Create New Project'}
              </h2>
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

              {!selectedTemplate && (
                <div className="form-group">
                  <label>Select Template</label>
                  <div className="template-cards">
                    {templates.map((template) => (
                      <div
                        key={template.id}
                        className={`template-card ${newProject.template_id === template.id ? 'selected' : ''}`}
                        onClick={() =>
                          setNewProject({
                            ...newProject,
                            template_id: template.id,
                            capabilities: template.default_capabilities,
                            brief: template.suggested_brief || newProject.brief,
                          })
                        }
                      >
                        <div className="template-name">{template.name}</div>
                        <div className="template-description">{template.description}</div>
                        <div className="template-category">{template.category}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="brief">Project Brief</label>
                <textarea
                  id="brief"
                  value={newProject.brief || ''}
                  onChange={(e) =>
                    setNewProject({ ...newProject, brief: e.target.value })
                  }
                  placeholder="Describe what you want to build..."
                  rows={3}
                />
              </div>

              {selectedTemplate && (
                <div className="form-group">
                  <label>Capabilities</label>
                  <div className="capabilities-display">
                    {newProject.capabilities?.map((cap) => (
                      <span key={cap} className="capability-chip">
                        {cap.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

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

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newProject.auto_create_repo || false}
                    onChange={(e) =>
                      setNewProject({ ...newProject, auto_create_repo: e.target.checked })
                    }
                  />
                  Automatically create a GitHub repo for this project
                </label>
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

export default LaunchpadPage;
