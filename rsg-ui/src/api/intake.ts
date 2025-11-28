/**
 * Intake System API Client
 * 
 * Provides TypeScript client for the intake template system API,
 * enabling structured requirement gathering through adaptive interviews.
 */

import axios from 'axios';
import { getApiConfig } from './client';

// -----------------------------------------------------------------------------
// TypeScript Interfaces
// -----------------------------------------------------------------------------

export type QuestionType = 'text' | 'textarea' | 'number' | 'choice' | 'multi_choice' | 'date' | 'list' | 'object' | 'derived';

export type ConditionOperator = 
  | 'equals' | 'not_equals' | 'in' | 'not_in' | 'contains' | 'not_contains'
  | 'greater_than' | 'less_than' | 'greater_equal' | 'less_equal'
  | 'is_set' | 'is_not_set' | 'regex_match';

export interface ConditionDefinition {
  field: string;
  operator: ConditionOperator;
  value: any;
  and_conditions?: ConditionDefinition[];
  or_conditions?: ConditionDefinition[];
}

export interface ValidationRules {
  min_length?: number;
  max_length?: number;
  pattern?: string;
  min_value?: number;
  max_value?: number;
  min_date?: string;
  max_date?: string;
  required_fields?: string[];
}

export interface OptionDefinition {
  value: string;
  label: string;
  description?: string;
  icon?: string;
}

export interface ItemSchema {
  type: QuestionType;
  properties?: Record<string, any>;
  validation?: ValidationRules;
  max_length?: number;
  options?: OptionDefinition[];
}

export interface QuestionDefinition {
  id: string;
  question?: string;
  type: QuestionType;
  required: boolean;
  default?: any;
  placeholder?: string;
  help_text?: string;
  validation?: ValidationRules;
  condition?: ConditionDefinition;
  conditional_next?: Record<string, string>;
  conditional_phases?: Record<string, string[]>;
  options?: OptionDefinition[];
  item_schema?: ItemSchema;
  properties?: Record<string, QuestionDefinition>;
  min_items?: number;
  max_items?: number;
  min_value?: number;
  max_value?: number;
  step?: number;
  unit?: string;
  hidden: boolean;
  readonly: boolean;
  width: 'full' | 'half' | 'third';
  derived_from?: string;
  transform?: string;
}

export interface PhaseDefinition {
  id: string;
  name: string;
  description?: string;
  order: number;
  required: boolean;
  condition?: ConditionDefinition;
  questions: QuestionDefinition[];
  next_phase_id?: string;
  conditional_next?: Record<string, string>;
  show_progress: boolean;
  allow_back: boolean;
  auto_advance: boolean;
}

export interface TemplateMetadata {
  id: string;
  name: string;
  description?: string;
  version: string;
  category?: string;
  estimated_time_minutes?: number;
  extends?: string;
  icon?: string;
  color?: string;
}

export interface TemplateDefinition {
  template: TemplateMetadata;
  phases: PhaseDefinition[];
  brand_constraints?: any;
  ad_hoc?: any;
  governance?: any;
  output?: any;
  phase_map?: Record<string, PhaseDefinition>;
  question_map?: Record<string, QuestionDefinition>;
  dependency_graph?: Record<string, string[]>;
}

export interface ValidationError {
  field_id: string;
  error_type: string;
  message: string;
  details?: Record<string, any>;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: ValidationError[];
  warnings?: ValidationError[];
}

export interface IntakeSession {
  session_id: string;
  user_id?: string;
  template_id: string;
  client_slug: string;
  current_phase_id?: string;
  phase_order: string[];
  completed_phases: string[];
  responses: Record<string, any>;
  derived_responses: Record<string, any>;
  governance_data: Record<string, any>;
  validation_errors: ValidationError[];
  is_complete: boolean;
  project_id?: string;
  created_at: string;
  updated_at: string;
  last_activity: string;
  metadata: Record<string, any>;
  auto_save_enabled: boolean;
  save_interval_seconds: number;
}

export interface PhaseStatus {
  phase_id: string;
  name: string;
  is_current: boolean;
  is_complete: boolean;
  is_available: boolean;
}

export interface SessionResponse {
  session_id: string;
  template_id: string;
  client_slug: string;
  current_phase_id?: string;
  progress_percent: number;
  is_complete: boolean;
  created_at: string;
  governance_notices?: string[];
}

export interface SessionStatusResponse {
  session_id: string;
  template_id: string;
  current_phase_id?: string;
  progress_percent: number;
  phases: PhaseStatus[];
  current_questions: QuestionDefinition[];
  responses: Record<string, any>;
  validation_errors: ValidationError[];
}

export interface ResponseSubmissionResult {
  success: boolean;
  validation_result: ValidationResult;
  next_phase_id?: string;
  advanced: boolean;
  progress_percent: number;
}

export interface NavigationResult {
  success: boolean;
  current_phase_id?: string;
  target_phase_id?: string;
  message?: string;
}

export interface ProjectCreationResult {
  success: boolean;
  project_id?: string;
  validation_result: ValidationResult;
  intake_summary: {
    total_responses: number;
    governance_applied: boolean;
    project_type: string;
  };
  next_steps: {
    redirect_url: string;
    workflow_status: string;
  };
}

export interface TemplateListItem {
  template_id: string;
  name: string;
  description?: string;
  category?: string;
  estimated_time_minutes?: number;
  question_count?: number;
  phase_count?: number;
  icon?: string;
  color?: string;
}

// Request interfaces
export interface CreateSessionRequest {
  template_id: string;
  client_slug?: string;
  user_id?: string;
  metadata?: Record<string, any>;
}

export interface SubmitResponsesRequest {
  phase_id: string;
  responses: Record<string, any>;
  auto_advance?: boolean;
}

export interface NavigationRequest {
  action: 'next' | 'previous' | 'goto';
  target_phase_id?: string;
}

export interface CompleteSessionRequest {
  final_validation?: boolean;
  create_project?: boolean;
}

export interface ValidateRequest {
  template_id: string;
  client_slug?: string;
  responses: Record<string, any>;
}

// -----------------------------------------------------------------------------
// API Client Class
// -----------------------------------------------------------------------------

class IntakeApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = '';
    this.updateBaseUrl();
  }

  private updateBaseUrl() {
    const config = getApiConfig();
    this.baseUrl = `${config.baseUrl}/api/intake`;
  }

  private async makeRequest<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    path: string,
    data?: any,
    params?: Record<string, string>
  ): Promise<T> {
    this.updateBaseUrl(); // Ensure we have the latest base URL
    const config = getApiConfig();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-User-Id': config.userId,
      'X-User-Email': config.userEmail,
    };

    // Include LLM API key if available
    if (config.llmApiKey) {
      headers['X-LLM-Api-Key'] = config.llmApiKey;
    }

    try {
      const response = await axios.request<T>({
        method,
        url: `${this.baseUrl}${path}`,
        data,
        params,
        headers,
        timeout: 120000, // 2 minutes for complex operations
      });
      
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const message = error.response?.data?.detail || error.message;
        throw new Error(message);
      }
      throw error;
    }
  }

  // Session Management
  async createSession(request: CreateSessionRequest): Promise<SessionResponse> {
    return this.makeRequest<SessionResponse>('POST', '/sessions', request);
  }

  async getSessionStatus(sessionId: string): Promise<SessionStatusResponse> {
    return this.makeRequest<SessionStatusResponse>('GET', `/sessions/${sessionId}`);
  }

  async submitResponses(
    sessionId: string, 
    request: SubmitResponsesRequest
  ): Promise<ResponseSubmissionResult> {
    return this.makeRequest<ResponseSubmissionResult>('PUT', `/sessions/${sessionId}/responses`, request);
  }

  async navigateSession(
    sessionId: string, 
    request: NavigationRequest
  ): Promise<NavigationResult> {
    return this.makeRequest<NavigationResult>('POST', `/sessions/${sessionId}/navigate`, request);
  }

  async completeSession(
    sessionId: string, 
    request: CompleteSessionRequest = {}
  ): Promise<ProjectCreationResult> {
    return this.makeRequest<ProjectCreationResult>('POST', `/sessions/${sessionId}/complete`, request);
  }

  async deleteSession(sessionId: string): Promise<{ status: string; session_id: string }> {
    return this.makeRequest<{ status: string; session_id: string }>('DELETE', `/sessions/${sessionId}`);
  }

  // Template Operations
  async listTemplates(params?: {
    client_slug?: string;
    category?: string;
    include_abstract?: boolean;
  }): Promise<TemplateListItem[]> {
    const queryParams: Record<string, string> = {};
    if (params?.client_slug) queryParams.client_slug = params.client_slug;
    if (params?.category) queryParams.category = params.category;
    if (params?.include_abstract) queryParams.include_abstract = params.include_abstract.toString();
    
    return this.makeRequest<TemplateListItem[]>('GET', '/templates', undefined, queryParams);
  }

  async getTemplate(templateId: string, clientSlug?: string): Promise<TemplateDefinition> {
    const params = clientSlug ? { client_slug: clientSlug } : undefined;
    return this.makeRequest<TemplateDefinition>('GET', `/templates/${templateId}`, undefined, params);
  }

  // Utility Operations
  async validateResponses(request: ValidateRequest): Promise<ValidationResult> {
    return this.makeRequest<ValidationResult>('POST', '/validate', request);
  }

  async previewTemplate(templateId: string): Promise<any> {
    return this.makeRequest<any>('GET', `/preview/${templateId}`);
  }

  async healthCheck(): Promise<{ status: string; service: string; timestamp: string }> {
    return this.makeRequest<{ status: string; service: string; timestamp: string }>('GET', '/health');
  }

  // Auto-save functionality for session persistence
  async autoSaveResponses(sessionId: string, responses: Record<string, any>): Promise<void> {
    // This is a lightweight save operation that doesn't trigger validation
    // We'll use the submit responses endpoint with auto_advance disabled
    try {
      await this.makeRequest<ResponseSubmissionResult>(
        'PUT', 
        `/sessions/${sessionId}/responses`, 
        {
          phase_id: '', // Will be determined by the backend from session state
          responses,
          auto_advance: false
        }
      );
    } catch (error) {
      // Auto-save failures should be silent to not disrupt user experience
      console.warn('Auto-save failed:', error);
    }
  }
}

// -----------------------------------------------------------------------------
// Export singleton instance
// -----------------------------------------------------------------------------

export const intakeApi = new IntakeApiClient();

// Export convenience functions for cleaner imports
export const {
  createSession,
  getSessionStatus,
  submitResponses,
  navigateSession,
  completeSession,
  deleteSession,
  listTemplates,
  getTemplate,
  validateResponses,
  previewTemplate,
  healthCheck,
  autoSaveResponses,
} = intakeApi;

export default intakeApi;