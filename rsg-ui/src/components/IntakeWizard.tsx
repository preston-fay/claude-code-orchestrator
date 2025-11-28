/**
 * IntakeWizard Component
 * 
 * Main wizard component for the intake template system that provides
 * structured, adaptive interviews for gathering project requirements.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  intakeApi,
  type TemplateDefinition,
  type SessionStatusResponse,
  type PhaseDefinition,
  type QuestionDefinition,
  type ValidationError,
  type TemplateListItem,
  type ResponseSubmissionResult,
  type ProjectCreationResult,
} from '../api/intake';
import './IntakeWizard.css';

// -----------------------------------------------------------------------------
// Component Interfaces
// -----------------------------------------------------------------------------

interface IntakeWizardProps {
  onComplete: (projectId: string) => void;
  onCancel: () => void;
  templateId?: string;
  clientSlug?: string;
}

interface TemplateSelectionProps {
  templates: TemplateListItem[];
  onSelect: (templateId: string) => void;
  onCancel: () => void;
  loading?: boolean;
}

interface PhaseFormProps {
  phase: PhaseDefinition;
  session: SessionStatusResponse;
  onSubmit: (responses: Record<string, any>) => void;
  onNavigate: (direction: 'next' | 'previous' | 'goto', targetPhaseId?: string) => void;
  loading?: boolean;
  validationErrors: ValidationError[];
}

interface QuestionRendererProps {
  question: QuestionDefinition;
  value: any;
  onChange: (value: any) => void;
  error?: ValidationError;
  touched: boolean;
  allResponses: Record<string, any>;
}

interface ProgressTrackerProps {
  session: SessionStatusResponse;
}

// -----------------------------------------------------------------------------
// Template Selection Component
// -----------------------------------------------------------------------------

const TemplateSelection: React.FC<TemplateSelectionProps> = ({ 
  templates, 
  onSelect, 
  onCancel,
  loading = false 
}) => {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedTemplateId) {
      onSelect(selectedTemplateId);
    }
  };

  return (
    <div className="intake-template-selection">
      <div className="intake-header">
        <h2>Select Project Template</h2>
        <p>Choose the type of project you want to create. This will determine the questions you'll be asked.</p>
      </div>

      <form onSubmit={handleSubmit} className="template-selection-form">
        <div className="template-grid">
          {templates.map((template) => (
            <div
              key={template.template_id}
              className={`template-card ${selectedTemplateId === template.template_id ? 'selected' : ''}`}
              onClick={() => setSelectedTemplateId(template.template_id)}
            >
              {/* NO ICONS - KDS compliant. Icons removed. */}
              <h3>{template.name}</h3>
              {template.description && (
                <p className="template-description">{template.description}</p>
              )}
              <div className="template-meta">
                {template.estimated_time_minutes && (
                  <span className="meta-item">
                    ~{template.estimated_time_minutes} min
                  </span>
                )}
                {template.question_count && (
                  <span className="meta-item">
                    {template.question_count} questions
                  </span>
                )}
                {template.phase_count && (
                  <span className="meta-item">
                    {template.phase_count} phases
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="form-actions">
          <button type="button" className="button-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button
            type="submit"
            className="button-primary"
            disabled={!selectedTemplateId || loading}
          >
            {loading ? 'Starting...' : 'Start Interview'}
          </button>
        </div>
      </form>
    </div>
  );
};

// -----------------------------------------------------------------------------
// Progress Tracker Component
// -----------------------------------------------------------------------------

const ProgressTracker: React.FC<ProgressTrackerProps> = ({ session }) => {
  return (
    <div className="intake-progress-tracker">
      <div className="progress-header">
        <h3>Progress</h3>
        <span className="progress-percent">{Math.round(session.progress_percent)}%</span>
      </div>
      
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${session.progress_percent}%` }}
        />
      </div>

      <div className="phase-list">
        {session.phases.map((phase, index) => (
          <div
            key={phase.phase_id}
            className={`phase-item ${phase.is_current ? 'current' : ''} ${phase.is_complete ? 'complete' : ''} ${!phase.is_available ? 'unavailable' : ''}`}
          >
            <div className="phase-indicator">
              {phase.is_complete ? '✓' : index + 1}
            </div>
            <span className="phase-name">{phase.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// -----------------------------------------------------------------------------
// Question Renderer Component
// -----------------------------------------------------------------------------

const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  question,
  value,
  onChange,
  error,
  touched,
  allResponses,
}) => {
  // Check if question should be visible based on conditions
  const isVisible = useCallback(() => {
    if (!question.condition) return true;
    
    // Simple condition evaluation - in production you'd want more robust logic
    const fieldValue = allResponses[question.condition.field];
    
    switch (question.condition.operator) {
      case 'equals':
        return fieldValue === question.condition.value;
      case 'not_equals':
        return fieldValue !== question.condition.value;
      case 'is_set':
        return fieldValue !== undefined && fieldValue !== null && fieldValue !== '';
      case 'is_not_set':
        return fieldValue === undefined || fieldValue === null || fieldValue === '';
      case 'in':
        return Array.isArray(question.condition.value) && question.condition.value.includes(fieldValue);
      case 'not_in':
        return !Array.isArray(question.condition.value) || !question.condition.value.includes(fieldValue);
      case 'contains':
        return String(fieldValue).includes(String(question.condition.value));
      case 'not_contains':
        return !String(fieldValue).includes(String(question.condition.value));
      default:
        return true;
    }
  }, [question.condition, allResponses]);

  const renderInput = () => {
    switch (question.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={question.placeholder}
            required={question.required}
            disabled={question.readonly}
            maxLength={question.validation?.max_length}
            className={error && touched ? 'error' : ''}
          />
        );

      case 'textarea':
        return (
          <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={question.placeholder}
            required={question.required}
            disabled={question.readonly}
            rows={4}
            maxLength={question.validation?.max_length}
            className={error && touched ? 'error' : ''}
          />
        );

      case 'number':
        return (
          <div className="number-input-container">
            <input
              type="number"
              value={value ?? ''}
              onChange={(e) => onChange(e.target.value ? parseFloat(e.target.value) : null)}
              placeholder={question.placeholder}
              required={question.required}
              disabled={question.readonly}
              min={question.min_value}
              max={question.max_value}
              step={question.step}
              className={error && touched ? 'error' : ''}
            />
            {question.unit && <span className="input-unit">{question.unit}</span>}
          </div>
        );

      case 'choice':
        return (
          <div className="radio-group" role="radiogroup">
            {question.options?.map((option) => (
              <label key={option.value} className="radio-option">
                <input
                  type="radio"
                  name={question.id}
                  value={option.value}
                  checked={value === option.value}
                  onChange={(e) => onChange(e.target.value)}
                  required={question.required}
                  disabled={question.readonly}
                />
                <div className="radio-content">
                  <span className="radio-label">{option.label}</span>
                  {option.description && (
                    <span className="radio-description">{option.description}</span>
                  )}
                </div>
              </label>
            ))}
          </div>
        );

      case 'multi_choice':
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="checkbox-group">
            {question.options?.map((option) => (
              <label key={option.value} className="checkbox-option">
                <input
                  type="checkbox"
                  value={option.value}
                  checked={selectedValues.includes(option.value)}
                  onChange={(e) => {
                    const newValues = e.target.checked
                      ? [...selectedValues, option.value]
                      : selectedValues.filter((v) => v !== option.value);
                    onChange(newValues);
                  }}
                  disabled={question.readonly}
                />
                <div className="checkbox-content">
                  <span className="checkbox-label">{option.label}</span>
                  {option.description && (
                    <span className="checkbox-description">{option.description}</span>
                  )}
                </div>
              </label>
            ))}
          </div>
        );

      case 'date':
        return (
          <input
            type="date"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            required={question.required}
            disabled={question.readonly}
            min={question.validation?.min_date}
            max={question.validation?.max_date}
            className={error && touched ? 'error' : ''}
          />
        );

      case 'list':
        const listValues = Array.isArray(value) ? value : [];
        return (
          <div className="list-input">
            {listValues.map((item, index) => (
              <div key={index} className="list-item">
                <input
                  type="text"
                  value={item || ''}
                  onChange={(e) => {
                    const newValues = [...listValues];
                    newValues[index] = e.target.value;
                    onChange(newValues);
                  }}
                  placeholder={`Item ${index + 1}`}
                />
                <button
                  type="button"
                  className="button-secondary small"
                  onClick={() => {
                    const newValues = listValues.filter((_, i) => i !== index);
                    onChange(newValues);
                  }}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className="button-secondary"
              onClick={() => onChange([...listValues, ''])}
              disabled={!!(question.max_items && listValues.length >= question.max_items)}
            >
              Add Item
            </button>
            {question.min_items && listValues.length < question.min_items && (
              <div className="field-hint">
                Minimum {question.min_items} items required
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="unsupported-type">
            Unsupported question type: {question.type}
          </div>
        );
    }
  };

  if (!isVisible()) {
    return null;
  }

  return (
    <div className={`question ${question.width}`}>
      {question.question && (
        <label className="question-label">
          {question.question}
          {question.required && <span className="required">*</span>}
        </label>
      )}
      
      {question.help_text && (
        <p className="help-text">{question.help_text}</p>
      )}
      
      <div className="question-input">
        {renderInput()}
      </div>
      
      {error && touched && (
        <div className="error-message">{error.message}</div>
      )}
    </div>
  );
};

// -----------------------------------------------------------------------------
// Phase Form Component
// -----------------------------------------------------------------------------

const PhaseForm: React.FC<PhaseFormProps> = ({
  phase,
  session,
  onSubmit,
  onNavigate,
  loading = false,
  validationErrors,
}) => {
  const [responses, setResponses] = useState<Record<string, any>>({});
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const autoSaveTimeoutRef = useRef<number | null>(null);

  // Load existing responses for this phase
  useEffect(() => {
    const phaseResponses = Object.fromEntries(
      Object.entries(session.responses).filter(([key]) =>
        phase.questions.some(q => q.id === key)
      )
    );
    setResponses(phaseResponses);
  }, [phase, session.responses]);

  // Auto-save responses
  useEffect(() => {
    if (autoSaveTimeoutRef.current) {
      window.clearTimeout(autoSaveTimeoutRef.current);
    }

    if (Object.keys(responses).length > 0) {
      autoSaveTimeoutRef.current = window.setTimeout(async () => {
        try {
          await intakeApi.autoSaveResponses(session.session_id, responses);
        } catch (err) {
          console.warn('Auto-save failed:', err);
        }
      }, 2000);
    }

    return () => {
      if (autoSaveTimeoutRef.current) {
        window.clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [responses, session.session_id]);

  const handleFieldChange = (questionId: string, value: any) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
    setTouched(prev => new Set(prev).add(questionId));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all visible fields as touched for validation display
    const visibleQuestionIds = phase.questions
      .filter(q => !q.hidden)
      .map(q => q.id);
    setTouched(new Set(visibleQuestionIds));
    
    // Submit responses
    onSubmit(responses);
  };

  const canGoBack = phase.allow_back;
  const isFirstPhase = session.phases.findIndex(p => p.phase_id === phase.id) === 0;

  return (
    <form onSubmit={handleSubmit} className="phase-form">
      <div className="phase-header">
        <h2>{phase.name}</h2>
        {phase.description && (
          <p className="phase-description">{phase.description}</p>
        )}
      </div>

      <div className="questions">
        {phase.questions
          .filter(q => !q.hidden)
          .map(question => (
            <QuestionRenderer
              key={question.id}
              question={question}
              value={responses[question.id]}
              onChange={(value) => handleFieldChange(question.id, value)}
              error={validationErrors.find(e => e.field_id === question.id)}
              touched={touched.has(question.id)}
              allResponses={{ ...session.responses, ...responses }}
            />
          ))}
      </div>

      <div className="form-actions">
        {canGoBack && !isFirstPhase && (
          <button
            type="button"
            className="button-secondary"
            onClick={() => onNavigate('previous')}
            disabled={loading}
          >
            Back
          </button>
        )}
        
        <button
          type="submit"
          className="button-primary"
          disabled={loading}
        >
          {loading ? 'Processing...' : (phase.next_phase_id ? 'Continue' : 'Complete')}
        </button>
      </div>
    </form>
  );
};

// -----------------------------------------------------------------------------
// Main IntakeWizard Component
// -----------------------------------------------------------------------------

const IntakeWizard: React.FC<IntakeWizardProps> = ({
  onComplete,
  onCancel,
  templateId,
  clientSlug = 'kearney-default'
}) => {
  const [step, setStep] = useState<'template' | 'interview' | 'complete'>('template');
  const [templates, setTemplates] = useState<TemplateListItem[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(templateId || '');
  const [template, setTemplate] = useState<TemplateDefinition | null>(null);
  const [session, setSession] = useState<SessionStatusResponse | null>(null);
  const [currentPhase, setCurrentPhase] = useState<PhaseDefinition | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

  // Load templates on mount if no template specified
  useEffect(() => {
    if (!templateId) {
      loadTemplates();
    } else {
      setStep('interview');
      initializeSession(templateId);
    }
  }, [templateId]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const templatesData = await intakeApi.listTemplates({ client_slug: clientSlug });
      setTemplates(templatesData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load templates';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const initializeSession = async (templateId: string) => {
    try {
      setLoading(true);
      setError(null);

      // Load template
      const templateData = await intakeApi.getTemplate(templateId, clientSlug);
      setTemplate(templateData);

      // Create session
      const sessionResponse = await intakeApi.createSession({
        template_id: templateId,
        client_slug: clientSlug
      });

      // Get session status
      const sessionStatus = await intakeApi.getSessionStatus(sessionResponse.session_id);
      setSession(sessionStatus);

      // Find current phase
      const currentPhaseData = templateData.phases.find(
        p => p.id === sessionStatus.current_phase_id
      );
      setCurrentPhase(currentPhaseData || null);

      setStep('interview');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to initialize session';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);
    initializeSession(templateId);
  };

  const handleResponseSubmit = async (responses: Record<string, any>) => {
    if (!session || !currentPhase) return;

    try {
      setLoading(true);
      setError(null);
      setValidationErrors([]);

      const result: ResponseSubmissionResult = await intakeApi.submitResponses(
        session.session_id,
        {
          phase_id: currentPhase.id,
          responses,
          auto_advance: true
        }
      );

      // Update validation errors
      setValidationErrors(result.validation_result.errors);

      if (result.validation_result.is_valid) {
        // Update session with new state
        const updatedSession = await intakeApi.getSessionStatus(session.session_id);
        setSession(updatedSession);

        // Check if intake is complete
        if (updatedSession.progress_percent >= 100 || !result.next_phase_id) {
          const completionResult: ProjectCreationResult = await intakeApi.completeSession(
            session.session_id,
            { final_validation: true, create_project: true }
          );

          if (completionResult.success && completionResult.project_id) {
            onComplete(completionResult.project_id);
          } else {
            setError('Failed to create project from intake');
          }
        } else if (result.next_phase_id) {
          // Load next phase
          const nextPhaseData = template?.phases.find(p => p.id === result.next_phase_id);
          setCurrentPhase(nextPhaseData || null);
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit responses';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigation = async (direction: 'next' | 'previous' | 'goto', targetPhaseId?: string) => {
    if (!session || !template) return;

    try {
      const result = await intakeApi.navigateSession(session.session_id, {
        action: direction,
        target_phase_id: targetPhaseId
      });

      if (result.success && result.current_phase_id) {
        const updatedSession = await intakeApi.getSessionStatus(session.session_id);
        setSession(updatedSession);

        const newPhase = template.phases.find(p => p.id === result.current_phase_id);
        setCurrentPhase(newPhase || null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to navigate';
      setError(message);
    }
  };

  // Render based on current step
  if (step === 'template') {
    return (
      <div className="intake-wizard">
        <div className="intake-container">
          {loading ? (
            <div className="intake-loading">
              <div className="loading-spinner" />
              <p>Loading templates...</p>
            </div>
          ) : error ? (
            <div className="intake-error">
              <h3>Error Loading Templates</h3>
              <p>{error}</p>
              <div className="error-actions">
                <button className="button-secondary" onClick={onCancel}>Cancel</button>
                <button className="button-primary" onClick={loadTemplates}>Retry</button>
              </div>
            </div>
          ) : (
            <TemplateSelection
              templates={templates}
              onSelect={handleTemplateSelect}
              onCancel={onCancel}
              loading={loading}
            />
          )}
        </div>
      </div>
    );
  }

  if (step === 'interview') {
    if (loading && !session) {
      return (
        <div className="intake-wizard">
          <div className="intake-container">
            <div className="intake-loading">
              <div className="loading-spinner" />
              <p>Initializing interview...</p>
            </div>
          </div>
        </div>
      );
    }

    if (error && !session) {
      return (
        <div className="intake-wizard">
          <div className="intake-container">
            <div className="intake-error">
              <h3>Error Starting Interview</h3>
              <p>{error}</p>
              <div className="error-actions">
                <button className="button-secondary" onClick={onCancel}>Cancel</button>
                <button className="button-primary" onClick={() => initializeSession(selectedTemplateId)}>
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (!session || !currentPhase || !template) {
      return (
        <div className="intake-wizard">
          <div className="intake-container">
            <div className="intake-error">
              <h3>Session Error</h3>
              <p>Unable to load interview session.</p>
              <button className="button-primary" onClick={onCancel}>Return</button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="intake-wizard">
        <div className="intake-container">
          <div className="intake-header">
            <h1>{template.template.name}</h1>
            {template.template.description && (
              <p className="intake-description">{template.template.description}</p>
            )}
            <button className="cancel-button" onClick={onCancel} title="Cancel Interview">
              ×
            </button>
          </div>

          {error && (
            <div className="error-banner">
              {error}
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          )}

          <div className="intake-content">
            <aside className="intake-sidebar">
              <ProgressTracker session={session} />
            </aside>

            <main className="intake-main">
              <PhaseForm
                phase={currentPhase}
                session={session}
                onSubmit={handleResponseSubmit}
                onNavigate={(direction: 'next' | 'previous' | 'goto', targetPhaseId?: string) => handleNavigation(direction, targetPhaseId)}
                loading={loading}
                validationErrors={validationErrors}
              />
            </main>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default IntakeWizard;