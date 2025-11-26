/**
 * Orchestrator Runs API Client
 *
 * TypeScript client for the 5-endpoint orchestrator runs API:
 * - POST /runs → create orchestrator run
 * - POST /runs/{id}/next → advance to next phase
 * - GET /runs/{id} → get run status and phases
 * - GET /runs/{id}/artifacts → list artifacts by phase
 * - GET /runs/{id}/metrics → governance, hygiene, timing, tokens
 */

import axios, { AxiosInstance } from 'axios';

// ---------------------------------------------------------------------------
// Type Definitions
// ---------------------------------------------------------------------------

export interface CreateRunRequest {
  profile: string;
  intake?: string;
  project_name?: string;
  metadata?: Record<string, unknown>;
}

export interface RunSummary {
  run_id: string;
  profile: string;
  project_name?: string;
  current_phase: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PhaseInfo {
  phase: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  agent_ids?: string[];
  artifacts_count?: number;
}

export interface RunDetail {
  run_id: string;
  profile: string;
  intake?: string;
  project_name?: string;
  current_phase: string;
  status: string;
  phases: PhaseInfo[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
  total_duration_seconds?: number;
  metadata?: Record<string, unknown>;
}

export interface ArtifactSummary {
  artifact_id: string;
  phase: string;
  path: string;
  name: string;
  description: string;
  artifact_type: string;
  size_bytes: number;
  created_at: string;
}

export interface ArtifactsResponse {
  run_id: string;
  artifacts_by_phase: Record<string, ArtifactSummary[]>;
  total_count: number;
}

export interface PhaseMetrics {
  phase: string;
  duration_seconds: number;
  token_usage: Record<string, number>;
  cost_usd: number;
  agents_executed: string[];
  artifacts_generated: number;
  governance_passed: boolean;
  governance_warnings: string[];
}

export interface MetricsSummary {
  run_id: string;
  total_duration_seconds: number;
  total_token_usage: Record<string, number>;
  total_cost_usd: number;
  phases_metrics: PhaseMetrics[];
  governance_score: number;
  hygiene_score: number;
  artifacts_total: number;
  errors_count: number;
}

export interface AdvanceRunRequest {
  skip_validation?: boolean;
}

export interface AdvanceRunResponse {
  run_id: string;
  previous_phase: string;
  current_phase: string;
  status: string;
  message: string;
}

export interface ListRunsParams {
  status?: string;
  profile?: string;
  limit?: number;
  offset?: number;
}

export interface ListRunsResponse {
  runs: RunSummary[];
  total: number;
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// Axios Instance Configuration
// ---------------------------------------------------------------------------

// Default configuration
const FALLBACK_API_URL = 'https://kup99hcmh5.us-east-2.awsapprunner.com';

const DEFAULT_BASE_URL =
  import.meta.env.VITE_ORCHESTRATOR_API_URL?.trim() || FALLBACK_API_URL;

const DEFAULT_USER_ID = import.meta.env.VITE_DEFAULT_USER_ID || 'dev-user';
const DEFAULT_USER_EMAIL = import.meta.env.VITE_DEFAULT_USER_EMAIL || 'dev@example.com';

// Storage keys
const STORAGE_KEYS = {
  baseUrl: 'orchestrator_api_url',
  userId: 'orchestrator_user_id',
  userEmail: 'orchestrator_user_email',
};

// Get stored config or defaults
function getStoredConfig() {
  return {
    baseUrl: localStorage.getItem(STORAGE_KEYS.baseUrl) || DEFAULT_BASE_URL,
    userId: localStorage.getItem(STORAGE_KEYS.userId) || DEFAULT_USER_ID,
    userEmail: localStorage.getItem(STORAGE_KEYS.userEmail) || DEFAULT_USER_EMAIL,
  };
}

// Create Axios instance
let axiosInstance: AxiosInstance = createAxiosInstance();

function createAxiosInstance(): AxiosInstance {
  const config = getStoredConfig();

  const instance = axios.create({
    baseURL: config.baseUrl,
    timeout: 60000, // 60s for long-running phase operations
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': config.userId,
      'X-User-Email': config.userEmail,
    },
  });

  // Add response interceptor for error handling
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      console.error('[Orchestrator API] Error:', error.response?.data || error.message);
      return Promise.reject(error);
    }
  );

  return instance;
}

// Update API configuration
export function updateApiConfig(baseUrl: string, userId: string, userEmail: string): void {
  localStorage.setItem(STORAGE_KEYS.baseUrl, baseUrl);
  localStorage.setItem(STORAGE_KEYS.userId, userId);
  localStorage.setItem(STORAGE_KEYS.userEmail, userEmail);

  // Recreate axios instance with new config
  axiosInstance = createAxiosInstance();
}

// Get current configuration
export function getApiConfig() {
  return getStoredConfig();
}

// ---------------------------------------------------------------------------
// Orchestrator Runs API Functions
// ---------------------------------------------------------------------------

/**
 * List orchestrator runs with filtering and pagination
 *
 * GET /runs
 *
 * @param params - Optional filters (status, profile, limit, offset)
 * @returns ListRunsResponse with array of runs and pagination info
 *
 * @example
 * // List all runs
 * const response = await listRuns({});
 *
 * // Filter by status
 * const completed = await listRuns({ status: 'completed' });
 *
 * // Filter and paginate
 * const page2 = await listRuns({ status: 'running', limit: 10, offset: 10 });
 */
export async function listRuns(params: ListRunsParams = {}): Promise<ListRunsResponse> {
  const queryParams = new URLSearchParams();

  if (params.status) queryParams.append('status', params.status);
  if (params.profile) queryParams.append('profile', params.profile);
  if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.append('offset', params.offset.toString());

  const queryString = queryParams.toString();
  const url = queryString ? `/runs?${queryString}` : '/runs';

  const response = await axiosInstance.get<ListRunsResponse>(url);
  return response.data;
}

/**
 * Create a new orchestrator run
 *
 * POST /runs
 *
 * @param request - Run creation parameters (profile, intake, project_name, metadata)
 * @returns RunSummary with run_id and basic info
 *
 * @example
 * const run = await createRun({
 *   profile: 'analytics_forecast_app',
 *   intake: 'Build a demand forecasting app',
 *   project_name: 'Forecast Project Q4'
 * });
 * console.log('Run ID:', run.run_id);
 */
export async function createRun(request: CreateRunRequest): Promise<RunSummary> {
  const response = await axiosInstance.post<RunSummary>('/runs', request);
  return response.data;
}

/**
 * Advance a run to the next phase
 *
 * POST /runs/{run_id}/next
 *
 * Executes the current phase and advances to the next phase in the workflow.
 *
 * @param runId - Run identifier
 * @param request - Optional request body (skip_validation)
 * @returns AdvanceRunResponse with previous/current phase info
 *
 * @example
 * const result = await advanceRun('abc123');
 * console.log(`Advanced from ${result.previous_phase} to ${result.current_phase}`);
 */
export async function advanceRun(
  runId: string,
  request?: AdvanceRunRequest
): Promise<AdvanceRunResponse> {
  const response = await axiosInstance.post<AdvanceRunResponse>(
    `/runs/${runId}/next`,
    request || {}
  );
  return response.data;
}

/**
 * Get detailed information about a run
 *
 * GET /runs/{run_id}
 *
 * Returns comprehensive information including all phases, status, and metadata.
 *
 * @param runId - Run identifier
 * @returns RunDetail with full run information including all phases
 *
 * @example
 * const run = await getRun('abc123');
 * console.log('Current phase:', run.current_phase);
 * console.log('Phases:', run.phases.map(p => p.phase));
 */
export async function getRun(runId: string): Promise<RunDetail> {
  const response = await axiosInstance.get<RunDetail>(`/runs/${runId}`);
  return response.data;
}

/**
 * List all artifacts for a run, grouped by phase
 *
 * GET /runs/{run_id}/artifacts
 *
 * Returns artifacts generated during each phase of the workflow.
 *
 * @param runId - Run identifier
 * @returns ArtifactsResponse with artifacts grouped by phase
 *
 * @example
 * const artifacts = await getRunArtifacts('abc123');
 * console.log('Total artifacts:', artifacts.total_count);
 * console.log('Planning artifacts:', artifacts.artifacts_by_phase['planning']);
 */
export async function getRunArtifacts(runId: string): Promise<ArtifactsResponse> {
  const response = await axiosInstance.get<ArtifactsResponse>(`/runs/${runId}/artifacts`);
  return response.data;
}

/**
 * Get comprehensive metrics for a run
 *
 * GET /runs/{run_id}/metrics
 *
 * Returns performance, governance, token usage, and cost metrics.
 *
 * @param runId - Run identifier
 * @returns MetricsSummary with all metrics
 *
 * @example
 * const metrics = await getRunMetrics('abc123');
 * console.log('Total cost:', metrics.total_cost_usd);
 * console.log('Governance score:', metrics.governance_score);
 * console.log('Total tokens:', metrics.total_token_usage.input + metrics.total_token_usage.output);
 */
export async function getRunMetrics(runId: string): Promise<MetricsSummary> {
  const response = await axiosInstance.get<MetricsSummary>(`/runs/${runId}/metrics`);
  return response.data;
}

// ---------------------------------------------------------------------------
// Utility Functions
// ---------------------------------------------------------------------------

/**
 * Get human-readable phase name
 */
export function getPhaseDisplayName(phase: string): string {
  const phaseNames: Record<string, string> = {
    planning: 'Planning',
    architecture: 'Architecture',
    data: 'Data Engineering',
    development: 'Development',
    qa: 'Quality Assurance',
    documentation: 'Documentation',
  };

  return phaseNames[phase.toLowerCase()] || phase;
}

/**
 * Get phase status badge color
 */
export function getPhaseStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'gray',
    in_progress: 'blue',
    completed: 'green',
    failed: 'red',
  };

  return colors[status.toLowerCase()] || 'gray';
}

/**
 * Format cost in USD
 */
export function formatCost(costUsd: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(costUsd);
}

/**
 * Format token count
 */
export function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(2)}M`;
  } else if (tokens >= 1_000) {
    return `${(tokens / 1_000).toFixed(2)}K`;
  } else {
    return tokens.toString();
  }
}

/**
 * Format duration in seconds to human-readable format
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

/**
 * Calculate percentage of phases completed
 */
export function calculateProgress(phases: PhaseInfo[]): number {
  if (phases.length === 0) return 0;

  const completedCount = phases.filter((p) => p.status === 'completed').length;
  return Math.round((completedCount / phases.length) * 100);
}

/**
 * Get next phase in workflow
 */
export function getNextPhase(currentPhase: string): string | null {
  const phaseOrder = ['planning', 'architecture', 'data', 'development', 'qa', 'documentation'];

  const currentIndex = phaseOrder.indexOf(currentPhase.toLowerCase());

  if (currentIndex === -1 || currentIndex === phaseOrder.length - 1) {
    return null;
  }

  return phaseOrder[currentIndex + 1];
}

/**
 * Check if run is completed
 */
export function isRunCompleted(run: RunDetail): boolean {
  return (
    run.status === 'completed' ||
    (run.current_phase === 'documentation' &&
      run.phases.find((p) => p.phase === 'documentation')?.status === 'completed')
  );
}

/**
 * Get artifact type icon/color
 */
export function getArtifactTypeInfo(artifactType: string): { icon: string; color: string } {
  const typeMap: Record<string, { icon: string; color: string }> = {
    prd: { icon: '📋', color: 'blue' },
    architecture: { icon: '🏗️', color: 'purple' },
    requirements: { icon: '📝', color: 'gray' },
    code: { icon: '💻', color: 'green' },
    test: { icon: '🧪', color: 'orange' },
    documentation: { icon: '📚', color: 'indigo' },
    data: { icon: '📊', color: 'cyan' },
  };

  return typeMap[artifactType.toLowerCase()] || { icon: '📄', color: 'gray' };
}
