/**
 * API Scanner TypeScript Type Definitions
 */

// ===== Scan Types =====
export interface ScanRequest {
  target_url: string;
  js_path?: string;
  project_id?: string;
  scan_vulns?: boolean;
  ai_enabled?: boolean;
  bruteforce_enabled?: boolean;
  analysis_type: 'js_only' | 'full_scan';
}

export interface ScanResponse {
  scan_id: string;
  message: string;
  status: 'started' | 'running' | 'completed' | 'failed';
}

export interface ScanResult {
  scan_id: string;
  target_url: string;
  scan_date: string;
  total_endpoints: number;
  shadow_apis: number;
  vulnerabilities: Vulnerability[];
  endpoints: Endpoint[];
  statistics: ScanStatistics;
  status: 'completed' | 'running' | 'failed';
}

// ===== Endpoint Types =====
export interface Endpoint {
  id?: string;
  url: string;
  method: HTTPMethod;
  source: string;
  status_code?: number;
  response_example?: string;
  parameters?: Record<string, string>;
  headers?: Record<string, string>;
  body_example?: string;
  is_shadow?: boolean;
  vulnerabilities?: Vulnerability[];
  classification?: string;
  risk_score?: number;
}

export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

// ===== Vulnerability Types =====
export interface Vulnerability {
  id?: string;
  type: string;
  severity: VulnerabilitySeverity;
  description: string;
  evidence: string;
  recommendation: string;
  endpoint: string;
  method: HTTPMethod;
  poc_command?: string;
}

export type VulnerabilitySeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

// ===== Statistics Types =====
export interface ScanStatistics {
  total_endpoints: number;
  by_method: Record<HTTPMethod, number>;
  by_source: Record<string, number>;
  shadow_apis?: number;
  public_apis?: number;
  scan_duration?: number;
}

export interface DashboardStats {
  total_scans: number;
  total_endpoints: number;
  total_vulnerabilities: number;
  shadow_apis: number;
  recent_scans: ScanSummary[];
  vulnerability_by_severity: VulnerabilityStats[];
  endpoints_by_method: MethodStats[];
}

export interface VulnerabilityStats {
  severity: VulnerabilitySeverity;
  count: number;
}

export interface MethodStats {
  method: HTTPMethod;
  count: number;
}

export interface ScanSummary {
  scan_id: string;
  target_url: string;
  scan_date: string;
  total_endpoints: number;
  vulnerabilities: number;
  status: 'completed' | 'running' | 'failed';
}

// ===== Project Types =====
export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  total_scans: number;
  last_scan_date?: string;
}

export interface ProjectCreateRequest {
  name: string;
  description?: string;
}

export interface ProjectUpdateRequest {
  name?: string;
  description?: string;
}

// ===== History Types =====
export interface ScanHistory {
  scan_id: string;
  project_id?: string;
  target_url: string;
  scan_date: string;
  status: 'completed' | 'running' | 'failed';
  total_endpoints: number;
  vulnerabilities: number;
  ai_enabled: boolean;
  bruteforce_enabled: boolean;
}

// ===== UI State Types =====
export type TabType = 'scan' | 'dashboard' | 'history' | 'projects';

export interface FilterOptions {
  searchQuery: string;
  method: HTTPMethod | 'all';
  severity: VulnerabilitySeverity | 'all';
  source?: string;
}

// ===== API Response Types =====
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}
