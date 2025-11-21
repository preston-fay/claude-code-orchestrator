import axios, { AxiosInstance } from 'axios';
import {
  ProjectSummary,
  Project,
  CreateProjectPayload,
  RsgOverview,
  ReadyStatus,
  SetStatus,
  GoStatus,
  ProjectStatus,
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
