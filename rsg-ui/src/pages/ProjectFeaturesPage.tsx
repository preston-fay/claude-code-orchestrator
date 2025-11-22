import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'

interface FeatureRequest {
  id: string
  project_id: string
  title: string
  description: string
  status: string
  created_at: string
  created_by: string
}

interface FeaturePlan {
  feature_id: string
  prd: string
  acceptance_criteria: string[]
  adr_summaries: string[]
  risks: string[]
  estimated_effort: string
}

interface FeatureBuildPlan {
  feature_id: string
  steps: string[]
  repo_changes: { file_path: string; action: string; description: string }[]
  required_agents: string[]
  required_tests: string[]
}

interface FeatureBuildResult {
  feature_id: string
  status: string
  branch_name: string
  diff_summary: string[]
  created_files: string[]
  updated_files: string[]
  test_results: { test_name: string; passed: boolean; output: string }[]
  governance_results: string
  pr_url: string | null
  error_message: string | null
}

interface FeatureDetail {
  request: FeatureRequest
  plan: FeaturePlan | null
  build_plan: FeatureBuildPlan | null
  result: FeatureBuildResult | null
}

type ModalTab = 'summary' | 'plan' | 'build_plan' | 'results' | 'actions'

const ProjectFeaturesPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [features, setFeatures] = useState<FeatureRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // New feature form
  const [showNewForm, setShowNewForm] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Feature detail modal
  const [selectedFeature, setSelectedFeature] = useState<FeatureDetail | null>(null)
  const [modalTab, setModalTab] = useState<ModalTab>('summary')
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    if (projectId) {
      loadFeatures()
    }
  }, [projectId])

  const loadFeatures = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/projects/${projectId}/features`)
      if (!response.ok) throw new Error('Failed to load features')
      const data = await response.json()
      setFeatures(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load features')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateFeature = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim() || !newDescription.trim()) return

    setSubmitting(true)
    try {
      const response = await fetch(`/api/projects/${projectId}/features`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle, description: newDescription }),
      })

      if (!response.ok) throw new Error('Failed to create feature')

      setNewTitle('')
      setNewDescription('')
      setShowNewForm(false)
      loadFeatures()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create feature')
    } finally {
      setSubmitting(false)
    }
  }

  const openFeatureDetail = async (featureId: string) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/features/${featureId}`)
      if (!response.ok) throw new Error('Failed to load feature detail')
      const data = await response.json()
      setSelectedFeature(data)
      setModalTab('summary')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feature')
    }
  }

  const handleGeneratePlan = async () => {
    if (!selectedFeature) return
    setActionLoading(true)
    try {
      const response = await fetch(
        `/api/projects/${projectId}/features/${selectedFeature.request.id}/plan`,
        { method: 'POST' }
      )
      if (!response.ok) throw new Error('Failed to generate plan')

      // Reload feature detail
      await openFeatureDetail(selectedFeature.request.id)
      loadFeatures()
      setModalTab('plan')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate plan')
    } finally {
      setActionLoading(false)
    }
  }

  const handleGenerateBuildPlan = async () => {
    if (!selectedFeature) return
    setActionLoading(true)
    try {
      const response = await fetch(
        `/api/projects/${projectId}/features/${selectedFeature.request.id}/build-plan`,
        { method: 'POST' }
      )
      if (!response.ok) throw new Error('Failed to generate build plan')

      await openFeatureDetail(selectedFeature.request.id)
      setModalTab('build_plan')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate build plan')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRunBuild = async () => {
    if (!selectedFeature) return
    setActionLoading(true)
    try {
      const response = await fetch(
        `/api/projects/${projectId}/features/${selectedFeature.request.id}/build`,
        { method: 'POST' }
      )
      if (!response.ok) throw new Error('Failed to run build')

      await openFeatureDetail(selectedFeature.request.id)
      loadFeatures()
      setModalTab('results')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run build')
    } finally {
      setActionLoading(false)
    }
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'completed': return 'status-completed'
      case 'building': return 'status-building'
      case 'planned': return 'status-planned'
      case 'failed': return 'status-failed'
      default: return 'status-submitted'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <div className="page features-page">
        <div className="loading">Loading features...</div>
      </div>
    )
  }

  return (
    <div className="page features-page">
      <div className="page-header">
        <div className="breadcrumb">
          <Link to="/projects" className="link-button">Projects</Link>
          <span className="separator">/</span>
          <Link to={`/projects/${projectId}`} className="link-button">Project</Link>
          <span className="separator">/</span>
          <span>Features</span>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNewForm(true)}>
          New Feature
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* New Feature Form */}
      {showNewForm && (
        <div className="card new-feature-form">
          <h3 className="card-title">New Feature Request</h3>
          <form onSubmit={handleCreateFeature}>
            <div className="form-group">
              <label className="form-label">Title</label>
              <input
                type="text"
                className="form-input"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g., Add Scenario Comparison View"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea
                className="form-input"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Describe what the feature should do, why it's needed, and any specific requirements..."
                rows={4}
                required
              />
            </div>
            <div className="button-group">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowNewForm(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={submitting}
              >
                {submitting ? 'Creating...' : 'Create Feature'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Features List */}
      <div className="card">
        <h3 className="card-title">Features ({features.length})</h3>
        {features.length === 0 ? (
          <div className="empty-state">
            <p>No features yet. Create your first feature request to get started.</p>
          </div>
        ) : (
          <table className="features-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Created By</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => (
                <tr key={feature.id}>
                  <td><code>{feature.id}</code></td>
                  <td>{feature.title}</td>
                  <td>
                    <span className={`status-badge ${getStatusClass(feature.status)}`}>
                      {feature.status}
                    </span>
                  </td>
                  <td>{feature.created_by}</td>
                  <td>{formatDate(feature.created_at)}</td>
                  <td>
                    <button
                      className="btn btn-small"
                      onClick={() => openFeatureDetail(feature.id)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Feature Detail Modal */}
      {selectedFeature && (
        <div className="modal-overlay" onClick={() => setSelectedFeature(null)}>
          <div className="modal feature-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedFeature.request.title}</h2>
              <button className="close-btn" onClick={() => setSelectedFeature(null)}>
                &times;
              </button>
            </div>

            <div className="modal-tabs">
              <button
                className={`tab ${modalTab === 'summary' ? 'active' : ''}`}
                onClick={() => setModalTab('summary')}
              >
                Summary
              </button>
              <button
                className={`tab ${modalTab === 'plan' ? 'active' : ''}`}
                onClick={() => setModalTab('plan')}
                disabled={!selectedFeature.plan}
              >
                Plan
              </button>
              <button
                className={`tab ${modalTab === 'build_plan' ? 'active' : ''}`}
                onClick={() => setModalTab('build_plan')}
                disabled={!selectedFeature.build_plan}
              >
                Build Plan
              </button>
              <button
                className={`tab ${modalTab === 'results' ? 'active' : ''}`}
                onClick={() => setModalTab('results')}
                disabled={!selectedFeature.result}
              >
                Results
              </button>
              <button
                className={`tab ${modalTab === 'actions' ? 'active' : ''}`}
                onClick={() => setModalTab('actions')}
              >
                Actions
              </button>
            </div>

            <div className="modal-content">
              {modalTab === 'summary' && (
                <div className="tab-content">
                  <div className="detail-row">
                    <span className="label">ID:</span>
                    <code>{selectedFeature.request.id}</code>
                  </div>
                  <div className="detail-row">
                    <span className="label">Status:</span>
                    <span className={`status-badge ${getStatusClass(selectedFeature.request.status)}`}>
                      {selectedFeature.request.status}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Created:</span>
                    <span>{formatDate(selectedFeature.request.created_at)}</span>
                  </div>
                  <div className="detail-section">
                    <h4>Description</h4>
                    <p>{selectedFeature.request.description}</p>
                  </div>
                </div>
              )}

              {modalTab === 'plan' && selectedFeature.plan && (
                <div className="tab-content">
                  <div className="detail-section">
                    <h4>PRD</h4>
                    <pre className="prd-content">{selectedFeature.plan.prd}</pre>
                  </div>
                  <div className="detail-section">
                    <h4>Acceptance Criteria</h4>
                    <ul>
                      {selectedFeature.plan.acceptance_criteria.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="detail-section">
                    <h4>ADR Summaries</h4>
                    <ul>
                      {selectedFeature.plan.adr_summaries.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="detail-section">
                    <h4>Risks</h4>
                    <ul>
                      {selectedFeature.plan.risks.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="detail-row">
                    <span className="label">Estimated Effort:</span>
                    <span>{selectedFeature.plan.estimated_effort}</span>
                  </div>
                </div>
              )}

              {modalTab === 'build_plan' && selectedFeature.build_plan && (
                <div className="tab-content">
                  <div className="detail-section">
                    <h4>Build Steps</h4>
                    <ol>
                      {selectedFeature.build_plan.steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  </div>
                  <div className="detail-section">
                    <h4>Repository Changes</h4>
                    <table className="changes-table">
                      <thead>
                        <tr>
                          <th>File</th>
                          <th>Action</th>
                          <th>Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedFeature.build_plan.repo_changes.map((c, i) => (
                          <tr key={i}>
                            <td><code>{c.file_path}</code></td>
                            <td>{c.action}</td>
                            <td>{c.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="detail-row">
                    <span className="label">Required Agents:</span>
                    <span>{selectedFeature.build_plan.required_agents.join(', ')}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Required Tests:</span>
                    <span>{selectedFeature.build_plan.required_tests.join(', ')}</span>
                  </div>
                </div>
              )}

              {modalTab === 'results' && selectedFeature.result && (
                <div className="tab-content">
                  <div className="detail-row">
                    <span className="label">Build Status:</span>
                    <span className={`status-badge ${selectedFeature.result.status === 'success' ? 'status-completed' : 'status-failed'}`}>
                      {selectedFeature.result.status}
                    </span>
                  </div>
                  {selectedFeature.result.branch_name && (
                    <div className="detail-row">
                      <span className="label">Branch:</span>
                      <code>{selectedFeature.result.branch_name}</code>
                    </div>
                  )}
                  {selectedFeature.result.pr_url && (
                    <div className="detail-row">
                      <span className="label">PR:</span>
                      <a href={selectedFeature.result.pr_url} target="_blank" rel="noopener noreferrer">
                        {selectedFeature.result.pr_url}
                      </a>
                    </div>
                  )}
                  <div className="detail-section">
                    <h4>Diff Summary</h4>
                    <ul>
                      {selectedFeature.result.diff_summary.map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  </div>
                  {selectedFeature.result.created_files.length > 0 && (
                    <div className="detail-section">
                      <h4>Created Files</h4>
                      <ul>
                        {selectedFeature.result.created_files.map((f, i) => (
                          <li key={i}><code>{f}</code></li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedFeature.result.error_message && (
                    <div className="detail-section error">
                      <h4>Error</h4>
                      <p>{selectedFeature.result.error_message}</p>
                    </div>
                  )}
                </div>
              )}

              {modalTab === 'actions' && (
                <div className="tab-content actions-tab">
                  <div className="action-buttons">
                    <button
                      className="btn btn-primary action-btn"
                      onClick={handleGeneratePlan}
                      disabled={actionLoading || selectedFeature.request.status !== 'submitted'}
                    >
                      {actionLoading ? 'Generating...' : 'Generate Plan'}
                    </button>
                    <p className="action-description">
                      Generate PRD and acceptance criteria using the Architect agent.
                    </p>
                  </div>
                  <div className="action-buttons">
                    <button
                      className="btn btn-primary action-btn"
                      onClick={handleGenerateBuildPlan}
                      disabled={actionLoading || !selectedFeature.plan}
                    >
                      {actionLoading ? 'Generating...' : 'Generate Build Plan'}
                    </button>
                    <p className="action-description">
                      Generate detailed build steps and file changes.
                    </p>
                  </div>
                  <div className="action-buttons">
                    <button
                      className="btn btn-primary action-btn"
                      onClick={handleRunBuild}
                      disabled={actionLoading || selectedFeature.request.status === 'building'}
                    >
                      {actionLoading ? 'Building...' : 'Run Build'}
                    </button>
                    <p className="action-description">
                      Execute the build plan, run tests, and create a PR.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectFeaturesPage
