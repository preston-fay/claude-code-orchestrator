import React, { useState } from 'react'
import { useParams } from 'react-router-dom'

interface AppBuildPlan {
  plan_id: string
  app_name: string
  prd_summary: string
  architecture_decisions: string[]
  scaffolding_steps: string[]
  feature_list: string[]
  estimated_files: number
  created_at: string
}

interface AppBuildResult {
  success: boolean
  project_id: string
  plan_id: string
  files_created: string[]
  files_modified: string[]
  phases_completed: string[]
  commit_messages: string[]
  documentation: string
  errors: string[]
}

type BuildAction = 'scaffold' | 'feature' | 'endpoint'

const ProjectAppBuildPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [description, setDescription] = useState('')
  const [appName, setAppName] = useState('')
  const [selectedAction, setSelectedAction] = useState<BuildAction>('scaffold')
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState<AppBuildPlan | null>(null)
  const [result, setResult] = useState<AppBuildResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handlePlanBuild = async () => {
    if (!description.trim()) {
      setError('Please provide a description of what you want to build')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/app-builder/${projectId}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description,
          app_name: appName || undefined,
          stack: ['react', 'fastapi'],
        }),
      })

      if (!response.ok) {
        throw new Error(`Planning failed: ${response.statusText}`)
      }

      const data = await response.json()
      setPlan(data)
      setAppName(data.app_name)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Planning failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRunBuild = async () => {
    if (!plan) {
      setError('Please plan the build first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/app-builder/${projectId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_id: plan.plan_id,
          include_scaffolding: true,
        }),
      })

      if (!response.ok) {
        throw new Error(`Build failed: ${response.statusText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Build failed')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickAction = async () => {
    if (!description.trim()) {
      setError('Please provide a description')
      return
    }

    setLoading(true)
    setError(null)

    try {
      let endpoint = ''
      let body: Record<string, unknown> = {}

      switch (selectedAction) {
        case 'scaffold':
          endpoint = `/api/app-builder/${projectId}/scaffold`
          body = {
            app_name: appName || 'MyApp',
            style: 'kearney',
            include_api_client: true,
            initial_pages: ['Home', 'Settings'],
          }
          break
        case 'feature':
          endpoint = `/api/app-builder/${projectId}/feature`
          body = {
            feature_description: description,
            include_tests: true,
          }
          break
        case 'endpoint':
          endpoint = `/api/app-builder/${projectId}/endpoint`
          body = {
            endpoint_name: description.toLowerCase().replace(/\s+/g, '_'),
            summary: description,
            methods: ['GET', 'POST'],
          }
          break
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        throw new Error(`Action failed: ${response.statusText}`)
      }

      const data = await response.json()
      setResult({
        success: data.success,
        project_id: projectId || '',
        plan_id: '',
        files_created: data.files_created || [],
        files_modified: data.files_modified || [],
        phases_completed: [],
        commit_messages: [data.commit_message || ''],
        documentation: '',
        errors: data.errors || [],
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-build-page">
      <div className="page-header">
        <h2>App Builder</h2>
        <p className="page-subtitle">
          Build complete applications with agent-driven development
        </p>
      </div>

      {/* Build Configuration */}
      <div className="build-config card">
        <h3 className="card-title">Build Configuration</h3>

        <div className="form-group">
          <label className="form-label">What do you want to build?</label>
          <textarea
            className="form-input build-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe your application... e.g., 'Build a Territory Optimizer with map visualization and scenario management'"
            rows={4}
          />
        </div>

        <div className="form-group">
          <label className="form-label">App Name (optional)</label>
          <input
            type="text"
            className="form-input"
            value={appName}
            onChange={(e) => setAppName(e.target.value)}
            placeholder="MyApp"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Quick Action</label>
          <select
            className="form-input"
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value as BuildAction)}
          >
            <option value="scaffold">Scaffold App</option>
            <option value="feature">Add Feature</option>
            <option value="endpoint">Generate Backend Endpoint</option>
          </select>
        </div>

        <div className="button-group">
          <button
            className="btn btn-secondary"
            onClick={handleQuickAction}
            disabled={loading || !description.trim()}
          >
            {loading ? 'Processing...' : `Run ${selectedAction}`}
          </button>
          <button
            className="btn btn-primary"
            onClick={handlePlanBuild}
            disabled={loading || !description.trim()}
          >
            {loading ? 'Planning...' : 'Plan Build'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message card">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Plan Display */}
      {plan && (
        <div className="build-plan card">
          <h3 className="card-title">Build Plan: {plan.app_name}</h3>

          <div className="plan-section">
            <h4>PRD Summary</h4>
            <pre className="plan-content">{plan.prd_summary}</pre>
          </div>

          <div className="plan-section">
            <h4>Architecture Decisions</h4>
            <ul className="decision-list">
              {plan.architecture_decisions.map((decision, i) => (
                <li key={i}>{decision}</li>
              ))}
            </ul>
          </div>

          <div className="plan-section">
            <h4>Scaffolding Steps</h4>
            <ol className="step-list">
              {plan.scaffolding_steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="plan-section">
            <h4>Features to Generate</h4>
            <ul className="feature-list">
              {plan.feature_list.map((feature, i) => (
                <li key={i}>{feature}</li>
              ))}
            </ul>
          </div>

          <div className="plan-meta">
            <span>Estimated files: {plan.estimated_files}</span>
          </div>

          <button
            className="btn btn-primary run-build-btn"
            onClick={handleRunBuild}
            disabled={loading}
          >
            {loading ? 'Building...' : 'Run Build'}
          </button>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className={`build-result card ${result.success ? 'success' : 'failure'}`}>
          <h3 className="card-title">
            {result.success ? 'Build Successful' : 'Build Failed'}
          </h3>

          {result.files_created.length > 0 && (
            <div className="result-section">
              <h4>Files Created ({result.files_created.length})</h4>
              <ul className="file-list">
                {result.files_created.map((file, i) => (
                  <li key={i}><code>{file}</code></li>
                ))}
              </ul>
            </div>
          )}

          {result.files_modified.length > 0 && (
            <div className="result-section">
              <h4>Files Modified ({result.files_modified.length})</h4>
              <ul className="file-list">
                {result.files_modified.map((file, i) => (
                  <li key={i}><code>{file}</code></li>
                ))}
              </ul>
            </div>
          )}

          {result.phases_completed.length > 0 && (
            <div className="result-section">
              <h4>Phases Completed</h4>
              <div className="phase-badges">
                {result.phases_completed.map((phase, i) => (
                  <span key={i} className="phase-badge">{phase}</span>
                ))}
              </div>
            </div>
          )}

          {result.commit_messages.length > 0 && (
            <div className="result-section">
              <h4>Commit Messages</h4>
              <ul className="commit-list">
                {result.commit_messages.filter(Boolean).map((msg, i) => (
                  <li key={i}><code>{msg}</code></li>
                ))}
              </ul>
            </div>
          )}

          {result.errors.length > 0 && (
            <div className="result-section errors">
              <h4>Errors</h4>
              <ul className="error-list">
                {result.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ProjectAppBuildPage
