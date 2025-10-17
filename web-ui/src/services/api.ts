import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  ScanRequest,
  ScanResponse,
  ScanResult,
  Project,
  ProjectCreateRequest,
  ProjectUpdateRequest,
  ScanHistory,
  DashboardStats,
  ApiResponse
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // 요청 인터셉터
    this.client.interceptors.request.use(
      (config) => {
        if (process.env.NODE_ENV === 'development') {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (process.env.NODE_ENV === 'development') {
          console.error('[API Error]', error.response?.data || error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  // ==================== Project APIs ====================

  async getProjects(): Promise<Project[]> {
    const response = await this.client.get<ApiResponse<{ projects: Project[] }>>('/api/projects');
    return response.data.data?.projects || [];
  }

  async createProject(data: ProjectCreateRequest): Promise<Project> {
    const response = await this.client.post<ApiResponse<{ project: Project }>>('/api/projects', data);
    return response.data.data!.project;
  }

  async updateProject(projectId: string, data: ProjectUpdateRequest): Promise<Project> {
    const response = await this.client.put<ApiResponse<{ project: Project }>>(
      `/api/projects/${projectId}`,
      data
    );
    return response.data.data!.project;
  }

  async deleteProject(projectId: string): Promise<void> {
    await this.client.delete(`/api/projects/${projectId}`);
  }

  async getProjectStatistics(projectId: string): Promise<DashboardStats> {
    const response = await this.client.get<ApiResponse<DashboardStats>>(
      `/api/projects/${projectId}/statistics`
    );
    return response.data.data!;
  }

  // ==================== Scan APIs ====================

  async startScan(data: ScanRequest): Promise<ScanResponse> {
    const response = await this.client.post<ApiResponse<ScanResponse>>('/api/scan/start', data);
    return response.data.data!;
  }

  async getScanStatus(scanId: string): Promise<ScanResponse> {
    const response = await this.client.get<ApiResponse<ScanResponse>>(`/api/scan/${scanId}/status`);
    return response.data.data!;
  }

  async getScanResult(scanId: string): Promise<ScanResult> {
    const response = await this.client.get<ApiResponse<ScanResult>>(`/api/scan/${scanId}`);
    return response.data.data!;
  }

  async stopScan(scanId: string): Promise<void> {
    await this.client.post(`/api/scan/${scanId}/stop`);
  }

  async deleteScan(scanId: string): Promise<void> {
    await this.client.delete(`/api/scan/${scanId}`);
  }

  // ==================== History APIs ====================

  async getProjectHistory(projectId: string): Promise<ScanHistory[]> {
    const response = await this.client.get<ApiResponse<{ scans: ScanHistory[] }>>(
      `/api/projects/${projectId}/scans`
    );
    return response.data.data?.scans || [];
  }

  async getAllHistory(): Promise<ScanHistory[]> {
    const response = await this.client.get<ApiResponse<{ scans: ScanHistory[] }>>('/api/scans');
    return response.data.data?.scans || [];
  }

  // ==================== Vulnerability APIs ====================

  async getEndpointVulnerabilities(scanId: string, endpoint: string): Promise<any[]> {
    const response = await this.client.get<ApiResponse<{ vulnerabilities: any[] }>>(
      `/api/scan/${scanId}/vulnerabilities`,
      { params: { endpoint } }
    );
    return response.data.data?.vulnerabilities || [];
  }

  // ==================== PoC Execution ====================

  async executePoc(data: { command: string }): Promise<any> {
    const response = await this.client.post('/api/execute-poc', data);
    return response.data;
  }

  // ==================== Export APIs ====================

  async exportJson(scanId: string): Promise<Blob> {
    const response = await this.client.get(`/api/scan/${scanId}/export/json`, {
      responseType: 'blob'
    });
    return response.data;
  }

  async exportCsv(scanId: string): Promise<Blob> {
    const response = await this.client.get(`/api/scan/${scanId}/export/csv`, {
      responseType: 'blob'
    });
    return response.data;
  }

  async exportHtml(scanId: string): Promise<Blob> {
    const response = await this.client.get(`/api/scan/${scanId}/export/html`, {
      responseType: 'blob'
    });
    return response.data;
  }

  // ==================== Health Check ====================

  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/health');
      return true;
    } catch {
      return false;
    }
  }

  // ==================== Generic Methods ====================

  async get<T = any>(url: string, params?: any): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, { params });
    return response.data;
  }

  async post<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data);
    return response.data;
  }

  async put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data);
    return response.data;
  }

  async delete<T = any>(url: string): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url);
    return response.data;
  }
}

// 싱글톤 인스턴스
export const apiService = new ApiService();

// 개별 export (하위 호환성)
export const api = {
  get: <T = any>(url: string, params?: any) => apiService.get<T>(url, params),
  post: <T = any>(url: string, data?: any) => apiService.post<T>(url, data),
  put: <T = any>(url: string, data?: any) => apiService.put<T>(url, data),
  delete: <T = any>(url: string) => apiService.delete<T>(url)
};

export default apiService;
