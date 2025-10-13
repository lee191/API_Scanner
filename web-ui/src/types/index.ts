export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

export type VulnerabilityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface APIEndpoint {
  url: string;
  method: HTTPMethod;
  parameters: Record<string, string>;
  headers?: Record<string, string>;
  body_example?: string;
  response_example?: string;
  status_code?: number;
  source: string;
  timestamp?: string;
}

export interface Vulnerability {
  type: string;
  level: VulnerabilityLevel;
  endpoint: string;
  method: HTTPMethod;
  description: string;
  evidence: string;
  recommendation: string;
  cwe_id?: string;
  timestamp?: string;
}

export interface ScanResult {
  target: string;
  scan_start: string;
  scan_end?: string;
  endpoints: APIEndpoint[];
  vulnerabilities: Vulnerability[];
  statistics: {
    total_endpoints: number;
    total_vulnerabilities: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export interface ScanRequest {
  target_url: string;
  js_path?: string;
  scan_vulns: boolean;
  analysis_type: 'js_only' | 'full_scan' | 'proxy';
}

export interface ScanStatus {
  scan_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: ScanResult;
}
