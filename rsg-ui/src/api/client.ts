import axios, { AxiosInstance } from 'axios';
import {
  ProjectSummary,
  Project,
  CreateProjectPayload,
  ProjectTemplate,
  RsgOverview,
  ReadyStatus,
  SetStatus,
  GoStatus,
  ProjectStatus,
  UserPublicProfile,
  UpdateProviderSettingsPayload,
  ProviderTestResult,
  Checkpoint,
  OrchestratorEvent,
} from './types';

// Default configuration
const DEFAULT_BASE_URL = import.meta.env.VITE_ORCHESTRATOR_API_URL || 'http://localhost:8000';
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
    timeout: 30000,
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
      console.error('API Error:', error.response?.data || error.message);
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

// API Functions

export async function listProjects(): Promise<ProjectSummary[]> {
  const response = await axiosInstance.get<ProjectSummary[]>('/projects');
  return response.data;
}

export async function listProjectTemplates(): Promise<ProjectTemplate[]> {
  const response = await axiosInstance.get<ProjectTemplate[]>('/project-templates');
  return response.data;
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  const response = await axiosInstance.post<Project>('/projects', payload);
  return response.data;
}

export async function getProject(id: string): Promise<Project> {
  const response = await axiosInstance.get<Project>(`/projects/${id}`);
  return response.data;
}

export async function getProjectStatus(id: string): Promise<ProjectStatus> {
  const response = await axiosInstance.get<ProjectStatus>(`/projects/${id}/status`);
  return response.data;
}

export async function deleteProject(id: string): Promise<void> {
  await axiosInstance.delete(`/projects/${id}`);
}

// RSG Endpoints

export async function getRsgOverview(id: string): Promise<RsgOverview> {
  const response = await axiosInstance.get<RsgOverview>(`/rsg/${id}/overview`);
  return response.data;
}

export async function startReady(id: string): Promise<ReadyStatus> {
  const response = await axiosInstance.post<ReadyStatus>(`/rsg/${id}/ready/start`);
  return response.data;
}

export async function getReadyStatus(id: string): Promise<ReadyStatus> {
  const response = await axiosInstance.get<ReadyStatus>(`/rsg/${id}/ready/status`);
  return response.data;
}

export async function startSet(id: string): Promise<SetStatus> {
  const response = await axiosInstance.post<SetStatus>(`/rsg/${id}/set/start`);
  return response.data;
}

export async function getSetStatus(id: string): Promise<SetStatus> {
  const response = await axiosInstance.get<SetStatus>(`/rsg/${id}/set/status`);
  return response.data;
}

export async function startGo(id: string): Promise<GoStatus> {
  const response = await axiosInstance.post<GoStatus>(`/rsg/${id}/go/start`);
  return response.data;
}

export async function getGoStatus(id: string): Promise<GoStatus> {
  const response = await axiosInstance.get<GoStatus>(`/rsg/${id}/go/status`);
  return response.data;
}

// Health check
export async function healthCheck(): Promise<{ status: string }> {
  const response = await axiosInstance.get<{ status: string }>('/health');
  return response.data;
}

// User Profile & Provider Settings

export async function getCurrentUser(): Promise<UserPublicProfile> {
  const response = await axiosInstance.get<UserPublicProfile>('/users/me');
  return response.data;
}

export async function updateProviderSettings(
  payload: UpdateProviderSettingsPayload
): Promise<UserPublicProfile> {
  const response = await axiosInstance.post<UserPublicProfile>(
    '/users/me/provider-settings',
    payload
  );
  return response.data;
}

export async function testProviderConnection(
  payload?: UpdateProviderSettingsPayload
): Promise<ProviderTestResult> {
  const response = await axiosInstance.post<ProviderTestResult>(
    '/users/me/provider-test',
    payload ?? {}
  );
  return response.data;
}

// Checkpoints
export async function getProjectCheckpoints(projectId: string): Promise<Checkpoint[]> {
  const response = await axiosInstance.get<Checkpoint[]>(`/projects/${projectId}/checkpoints`);
  return response.data;
}

// Phase execution
export async function runPhase(projectId: string): Promise<void> {
  await axiosInstance.post(`/projects/${projectId}/advance`);
}

// Events
export async function getProjectEvents(
  projectId: string,
  limit: number = 50,
  eventType?: string
): Promise<OrchestratorEvent[]> {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  if (eventType) {
    params.append('event_type', eventType);
  }

  const response = await axiosInstance.get<OrchestratorEvent[]>(
    `/projects/${projectId}/events?${params.toString()}`
  );
  return response.data;
}

// Territory POC Endpoints

export interface TerritoryConfig {
  workspace_path: string;
  intake_config?: {
    territory?: {
      target_territories?: number;
      states?: string[];
    };
    scoring?: {
      weights?: {
        value_weight?: number;
        opportunity_weight?: number;
        workload_weight?: number;
      };
    };
  };
}

export interface TerritoryResult {
  success: boolean;
  skill_id: string;
  artifacts: Array<{
    name: string;
    path: string;
    type: string;
    description: string;
  }>;
  metadata: Record<string, unknown>;
  error?: string;
}

export interface TerritoryAssignment {
  retail_id: string;
  retail_name: string;
  state: string;
  territory_id: string;
  rvs: number;
  ros: number;
  rws: number;
  composite_score: number;
  latitude: number | null;
  longitude: number | null;
}

export interface TerritoryKpi {
  territory_id: string;
  retailer_count: number;
  total_revenue: number;
  avg_rvs: number;
  avg_ros: number;
  avg_rws: number;
  avg_composite: number;
  centroid_lat: number;
  centroid_lon: number;
  coverage_km: number;
}

export async function runTerritoryScoring(config: TerritoryConfig): Promise<TerritoryResult> {
  const response = await axiosInstance.post<TerritoryResult>('/territory/score', config);
  return response.data;
}

export async function runTerritoryClustering(config: TerritoryConfig): Promise<TerritoryResult> {
  const response = await axiosInstance.post<TerritoryResult>('/territory/cluster', config);
  return response.data;
}

export interface TerritoryRunFullResult {
  success: boolean;
  scoring: TerritoryResult;
  clustering: TerritoryResult | null;
  error?: string;
}

export async function runTerritoryFullPipeline(config: TerritoryConfig): Promise<TerritoryRunFullResult> {
  const response = await axiosInstance.post<TerritoryRunFullResult>('/territory/run-full', config);
  return response.data;
}

export async function getTerritoryAssignments(
  workspacePath: string
): Promise<{ assignments: TerritoryAssignment[]; count: number }> {
  const response = await axiosInstance.get('/territory/assignments', {
    params: { workspace_path: workspacePath },
  });
  return response.data;
}

export async function getTerritoryKpis(
  workspacePath: string
): Promise<{ kpis: TerritoryKpi[]; territory_count: number }> {
  const response = await axiosInstance.get('/territory/kpis', {
    params: { workspace_path: workspacePath },
  });
  return response.data;
}
