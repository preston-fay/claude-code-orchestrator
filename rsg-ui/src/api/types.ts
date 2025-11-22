// API Types for Orchestrator RSG

// Model name types for type-safe model selection
export type ModelName =
  | 'claude-sonnet-4-5-20250929'
  | 'claude-haiku-4-5-20251015';

// Model aliases that resolve to actual model names
export type ModelAlias = 'sonnet-latest' | 'haiku-fallback';

// Model tier for cost tracking
export type ModelTier = 'premium' | 'cost-efficient' | 'deprecated';

export interface ProjectSummary {
  project_id: string;
  project_name: string;
  client: string;
  project_type: string;
  workspace_path?: string | null;
  template_id?: string | null;
  current_phase: string;
  completed_phases: string[];
  created_at: string;
  status: string;
}

export interface Project extends ProjectSummary {
  run_id?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateProjectPayload {
  project_name: string;
  client?: string;
  project_type?: string;
  template_id?: string;
  description?: string;
  intake_path?: string;
  metadata?: Record<string, unknown>;
}

export interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  project_type: string;
  category: string;
}

export interface ReadyStatus {
  project_id: string;
  stage: string;
  status: string;
  planning_complete: boolean;
  architecture_complete: boolean;
  message?: string;
}

export interface SetStatus {
  project_id: string;
  stage: string;
  status: string;
  data_complete: boolean;
  development_complete: boolean;
  message?: string;
}

export interface GoStatus {
  project_id: string;
  stage: string;
  status: string;
  development_complete: boolean;
  qa_complete: boolean;
  documentation_complete: boolean;
  message?: string;
}

export interface RsgOverview {
  project_id: string;
  current_stage: string;
  ready: {
    status: string;
    planning_complete: boolean;
    architecture_complete: boolean;
  };
  set: {
    status: string;
    data_complete: boolean;
    development_complete: boolean;
  };
  go: {
    status: string;
    qa_complete: boolean;
    documentation_complete: boolean;
  };
}

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd?: number;
}

export interface ProjectStatus {
  project_id: string;
  run_id: string;
  current_phase: string;
  progress_percent: number;
  completed_phases: string[];
  pending_phases: string[];
  token_usage: TokenUsage;
  cost_usd: number;
}

export interface ApiConfig {
  baseUrl: string;
  userId: string;
  userEmail: string;
}

// User Profile Types
export interface UserTokenUsage {
  total_input_tokens: number;
  total_output_tokens: number;
  total_requests: number;
  last_reset: string;
}

export interface UserPublicProfile {
  user_id: string;
  email: string;
  name?: string | null;
  role: 'admin' | 'developer' | 'viewer';
  llm_provider: string;
  llm_key_set: boolean;
  llm_key_suffix?: string | null;
  default_model: string;
  model_entitlements: Record<string, string[]>;
  token_usage: UserTokenUsage;
  projects: string[];
}

export interface UpdateProviderSettingsPayload {
  llm_provider: string;
  api_key?: string;
  default_model?: string;
}

export interface ProviderTestResult {
  success: boolean;
  provider: string;
  model?: string | null;
  message: string;
}

export interface Checkpoint {
  checkpoint_id: string;
  phase: string;
  status: string;
  agent_id: string;
  created_at: string;
  artifacts?: string[];
}

// Event types
export interface OrchestratorEvent {
  id: string;
  event_type: string;
  timestamp: string;
  project_id: string;
  phase: string | null;
  agent_id: string | null;
  message: string;
  data: Record<string, unknown>;
}
