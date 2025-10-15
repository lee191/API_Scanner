'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axios from 'axios';
import { 
  ArrowLeft, 
  Globe, 
  Calendar, 
  Activity,
  Shield,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileCode,
  Terminal,
  Copy,
  Check,
  Download
} from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

const api = axios.create({
  baseURL: API_BASE_URL,
});

interface Statistics {
  total_endpoints?: number;
  shadow_apis?: number;
  public_apis?: number;
  total_vulnerabilities?: number;
  discovered_paths?: number;
  critical?: number;
  high?: number;
  medium?: number;
  low?: number;
}

interface ScanDetail {
  scan_id: string;
  target_url: string;
  status: string;
  progress: number;
  message: string;
  created_at: string;
  completed_at?: string;
  result?: {
    statistics: Statistics;
    shadow_apis: any[];
    public_apis: any[];
    endpoints: any[];
    vulnerabilities: any[];
    discovered_paths: any[];
  };
}

export default function ScanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scanId = params.id as string;

  const [scanData, setScanData] = useState<ScanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedEndpoints, setExpandedEndpoints] = useState<Set<string>>(new Set());
  const [expandedVulns, setExpandedVulns] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<'overview' | 'endpoints' | 'vulnerabilities' | 'paths'>('overview');
  const [generatingPoc, setGeneratingPoc] = useState<Set<number>>(new Set());
  const [generatingAllPocs, setGeneratingAllPocs] = useState(false);
  const [showCurl, setShowCurl] = useState<Set<string>>(new Set());
  const [curlData, setCurlData] = useState<{[key: string]: any}>({});
  const [loadingCurl, setLoadingCurl] = useState<Set<string>>(new Set());
  const [copiedCurl, setCopiedCurl] = useState<string>('');
  const [curlFormat, setCurlFormat] = useState<'powershell' | 'cmd' | 'bash'>('powershell');

  useEffect(() => {
    loadScanDetail();
  }, [scanId]);

  const loadScanDetail = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/status/${scanId}`);
      setScanData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || '스캔 정보를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const toggleEndpoint = (key: string) => {
    const newSet = new Set(expandedEndpoints);
    if (newSet.has(key)) {
      newSet.delete(key);
    } else {
      newSet.add(key);
    }
    setExpandedEndpoints(newSet);
  };

  const toggleVuln = (index: number) => {
    const newSet = new Set(expandedVulns);
    if (newSet.has(index)) {
      newSet.delete(index);
    } else {
      newSet.add(index);
    }
    setExpandedVulns(newSet);
  };

  const generatePocForVuln = async (vulnId: string, vulnIndex: number) => {
    try {
      const newSet = new Set(generatingPoc);
      newSet.add(vulnIndex);
      setGeneratingPoc(newSet);

      const response = await api.post(`/api/vulnerability/${vulnId}/generate-poc`);
      
      // Update vulnerability with generated PoC
      if (scanData && scanData.result && scanData.result.vulnerabilities) {
        const updatedVulns = [...scanData.result.vulnerabilities];
        updatedVulns[vulnIndex].poc_code = response.data.poc_code;
        setScanData({
          ...scanData,
          result: {
            ...scanData.result,
            vulnerabilities: updatedVulns
          }
        });
      }

      alert('PoC 코드가 생성되었습니다!');
    } catch (err: any) {
      alert(err.response?.data?.error || 'PoC 생성에 실패했습니다');
    } finally {
      const newSet = new Set(generatingPoc);
      newSet.delete(vulnIndex);
      setGeneratingPoc(newSet);
    }
  };

  const toggleCurl = async (endpointId: string, key: string, useAi: boolean = false) => {
    const newShowSet = new Set(showCurl);
    const loadingKey = useAi ? `${key}-ai` : key;
    
    if (newShowSet.has(key)) {
      newShowSet.delete(key);
      setShowCurl(newShowSet);
      return;
    }
    
    newShowSet.add(key);
    setShowCurl(newShowSet);
    
    // Load curl if not already loaded or if switching between AI/basic
    const cacheKey = useAi ? `${key}-ai` : key;
    if (!curlData[cacheKey]) {
      const newLoadingSet = new Set(loadingCurl);
      newLoadingSet.add(loadingKey);
      setLoadingCurl(newLoadingSet);
      
      try {
        const response = await api.get(`/api/endpoint/${endpointId}/curl?use_ai=${useAi}`);
        setCurlData({
          ...curlData,
          [key]: response.data.curl_commands,
          [cacheKey]: response.data.curl_commands
        });
      } catch (err: any) {
        alert(err.response?.data?.error || 'curl 명령어 생성에 실패했습니다');
        newShowSet.delete(key);
        setShowCurl(newShowSet);
      } finally {
        newLoadingSet.delete(loadingKey);
        setLoadingCurl(newLoadingSet);
      }
    }
  };

  const copyCurlToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCurl(key);
    setTimeout(() => setCopiedCurl(''), 2000);
  };

  const downloadPostmanCollection = async () => {
    try {
      const response = await api.get(`/api/scan/${scanId}/postman-collection`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan_${scanId}_postman_collection.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      alert('Postman Collection이 다운로드되었습니다!');
    } catch (err: any) {
      alert(err.response?.data?.error || 'Postman Collection 다운로드에 실패했습니다');
    }
  };

  const generateAllPocs = async () => {
    if (!confirm('모든 취약점에 대한 PoC를 생성하시겠습니까? (시간이 걸릴 수 있습니다)')) {
      return;
    }

    try {
      setGeneratingAllPocs(true);
      const response = await api.post(`/api/scan/${scanId}/generate-all-pocs`);
      
      alert(`PoC 생성 완료!\n생성: ${response.data.generated}개\n건너뜀: ${response.data.skipped}개\n오류: ${response.data.errors}개`);
      
      // Reload scan data to get updated PoCs
      await loadScanDetail();
    } catch (err: any) {
      alert(err.response?.data?.error || '일괄 PoC 생성에 실패했습니다');
    } finally {
      setGeneratingAllPocs(false);
    }
  };

  const getSeverityColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'text-red-400 bg-red-500/20 border-red-500/50';
      case 'high': return 'text-orange-400 bg-orange-500/20 border-orange-500/50';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
      case 'low': return 'text-blue-400 bg-blue-500/20 border-blue-500/50';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-500/50';
    }
  };

  const getMethodColor = (method: string) => {
    switch (method?.toUpperCase()) {
      case 'GET': return 'bg-green-500/20 text-green-400';
      case 'POST': return 'bg-blue-500/20 text-blue-400';
      case 'PUT': return 'bg-yellow-500/20 text-yellow-400';
      case 'DELETE': return 'bg-red-500/20 text-red-400';
      case 'PATCH': return 'bg-purple-500/20 text-purple-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('ko-KR');
  };

  const calculateDuration = () => {
    if (!scanData?.created_at || !scanData?.completed_at) return 'N/A';
    const start = new Date(scanData.created_at).getTime();
    const end = new Date(scanData.completed_at).getTime();
    const seconds = Math.floor((end - start) / 1000);
    return `${seconds}초`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">스캔 정보 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error || !scanData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">오류 발생</h2>
          <p className="text-gray-300 mb-6">{error || '스캔 정보를 찾을 수 없습니다'}</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center gap-2 mx-auto"
          >
            <ArrowLeft className="w-5 h-5" />
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  const stats: Statistics = scanData.result?.statistics || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition mb-4"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>돌아가기</span>
          </button>

          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-white mb-2">스캔 상세 정보</h1>
                <div className="flex items-center gap-2 text-gray-300 mb-2">
                  <Globe className="w-5 h-5" />
                  <span className="font-mono text-lg">{scanData.target_url}</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span>{formatDate(scanData.created_at)}</span>
                  </div>
                  {scanData.completed_at && (
                    <div className="flex items-center gap-1">
                      <Activity className="w-4 h-4" />
                      <span>소요 시간: {calculateDuration()}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className={`px-4 py-2 rounded-lg font-semibold ${
                scanData.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                scanData.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
                scanData.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>
                {scanData.status === 'completed' ? '완료' :
                 scanData.status === 'running' ? '진행중' :
                 scanData.status === 'failed' ? '실패' : '대기중'}
              </div>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
              <div className="bg-blue-500/20 rounded-lg p-4 border border-blue-500/30">
                <div className="text-blue-300 text-sm mb-1">엔드포인트</div>
                <div className="text-3xl font-bold text-blue-400">{stats.total_endpoints || 0}</div>
              </div>
              <div className="bg-red-500/20 rounded-lg p-4 border border-red-500/30">
                <div className="text-red-300 text-sm mb-1">Shadow APIs</div>
                <div className="text-3xl font-bold text-red-400">{stats.shadow_apis || 0}</div>
              </div>
              <div className="bg-green-500/20 rounded-lg p-4 border border-green-500/30">
                <div className="text-green-300 text-sm mb-1">Public APIs</div>
                <div className="text-3xl font-bold text-green-400">{stats.public_apis || 0}</div>
              </div>
              <div className="bg-orange-500/20 rounded-lg p-4 border border-orange-500/30">
                <div className="text-orange-300 text-sm mb-1">취약점</div>
                <div className="text-3xl font-bold text-orange-400">{stats.total_vulnerabilities || 0}</div>
              </div>
              <div className="bg-purple-500/20 rounded-lg p-4 border border-purple-500/30">
                <div className="text-purple-300 text-sm mb-1">발견된 경로</div>
                <div className="text-3xl font-bold text-purple-400">{stats.discovered_paths || 0}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-6 py-3 rounded-lg font-semibold transition whitespace-nowrap ${
              activeTab === 'overview'
                ? 'bg-blue-600 text-white'
                : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            개요
          </button>
          <button
            onClick={() => setActiveTab('endpoints')}
            className={`px-6 py-3 rounded-lg font-semibold transition whitespace-nowrap ${
              activeTab === 'endpoints'
                ? 'bg-blue-600 text-white'
                : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            엔드포인트 ({stats.total_endpoints || 0})
          </button>
          <button
            onClick={() => setActiveTab('vulnerabilities')}
            className={`px-6 py-3 rounded-lg font-semibold transition whitespace-nowrap ${
              activeTab === 'vulnerabilities'
                ? 'bg-blue-600 text-white'
                : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            취약점 ({stats.total_vulnerabilities || 0})
          </button>
          <button
            onClick={() => setActiveTab('paths')}
            className={`px-6 py-3 rounded-lg font-semibold transition whitespace-nowrap ${
              activeTab === 'paths'
                ? 'bg-blue-600 text-white'
                : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            발견된 경로 ({stats.discovered_paths || 0})
          </button>
        </div>

        {/* Tab Content */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-4">취약점 분포</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-red-500/20 rounded-lg p-4 border border-red-500/30">
                    <div className="text-red-300 text-sm mb-1">Critical</div>
                    <div className="text-2xl font-bold text-red-400">{stats.critical || 0}</div>
                  </div>
                  <div className="bg-orange-500/20 rounded-lg p-4 border border-orange-500/30">
                    <div className="text-orange-300 text-sm mb-1">High</div>
                    <div className="text-2xl font-bold text-orange-400">{stats.high || 0}</div>
                  </div>
                  <div className="bg-yellow-500/20 rounded-lg p-4 border border-yellow-500/30">
                    <div className="text-yellow-300 text-sm mb-1">Medium</div>
                    <div className="text-2xl font-bold text-yellow-400">{stats.medium || 0}</div>
                  </div>
                  <div className="bg-blue-500/20 rounded-lg p-4 border border-blue-500/30">
                    <div className="text-blue-300 text-sm mb-1">Low</div>
                    <div className="text-2xl font-bold text-blue-400">{stats.low || 0}</div>
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-4">스캔 정보</h2>
                <div className="bg-gray-800/50 rounded-lg p-4 space-y-2 font-mono text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Scan ID:</span>
                    <span className="text-gray-200">{scanData.scan_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-gray-200">{scanData.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Progress:</span>
                    <span className="text-gray-200">{scanData.progress}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Message:</span>
                    <span className="text-gray-200">{scanData.message}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Endpoints Tab */}
          {activeTab === 'endpoints' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white mb-4">
                엔드포인트 목록
              </h2>
              
              {scanData.result?.shadow_apis && scanData.result.shadow_apis.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-red-400 mb-3">🔴 Shadow APIs ({scanData.result.shadow_apis.length})</h3>
                  <div className="space-y-2">
                    {scanData.result.shadow_apis.map((endpoint: any, index: number) => {
                      const key = `shadow-${index}`;
                      const isExpanded = expandedEndpoints.has(key);
                      return (
                        <div key={key} className="bg-red-500/20 border border-red-500/50 rounded-lg overflow-hidden">
                          <div
                            className="p-4 flex items-center justify-between cursor-pointer hover:bg-red-500/30 transition"
                            onClick={() => toggleEndpoint(key)}
                          >
                            <div className="flex items-center gap-4 flex-1">
                              <span className={`px-3 py-1 rounded text-sm font-semibold ${getMethodColor(endpoint.method)}`}>
                                {endpoint.method}
                              </span>
                              <code className="text-red-200 font-semibold">{endpoint.url}</code>
                            </div>
                            {isExpanded ? <ChevronUp className="w-5 h-5 text-red-400" /> : <ChevronDown className="w-5 h-5 text-red-400" />}
                          </div>
                          {isExpanded && (
                            <div className="p-4 bg-red-900/30 border-t border-red-500/50 space-y-3">
                              {endpoint.parameters && Object.keys(endpoint.parameters).length > 0 && (
                                <div>
                                  <div className="text-red-300 font-semibold mb-2">Parameters:</div>
                                  <pre className="bg-black/30 p-3 rounded text-red-200 text-sm overflow-x-auto">
                                    {JSON.stringify(endpoint.parameters, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.source && (
                                <div>
                                  <span className="text-red-300 font-semibold">Source: </span>
                                  <span className="text-red-200">{endpoint.source}</span>
                                </div>
                              )}
                              
                              {/* Curl Command Buttons */}
                              <div className="mt-3 flex gap-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleCurl(endpoint.id, key, false);
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition"
                                  disabled={loadingCurl.has(key)}
                                >
                                  <Terminal className="w-4 h-4" />
                                  {loadingCurl.has(key) && !loadingCurl.has(`${key}-ai`) ? '로딩 중...' : showCurl.has(key) ? 'curl 숨기기' : 'curl 명령어 보기'}
                                </button>
                                
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleCurl(endpoint.id, key, true);
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded transition"
                                  disabled={loadingCurl.has(key)}
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                  </svg>
                                  {loadingCurl.has(`${key}-ai`) ? 'AI 생성 중...' : 'AI로 curl 생성'}
                                </button>
                              </div>
                                
                              {showCurl.has(key) && curlData[key] && (
                                <div className="mt-3 space-y-3">
                                  {/* Format Selector */}
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => setCurlFormat('powershell')}
                                      className={`px-3 py-1 rounded text-sm ${curlFormat === 'powershell' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                                    >
                                      PowerShell
                                    </button>
                                    <button
                                      onClick={() => setCurlFormat('cmd')}
                                      className={`px-3 py-1 rounded text-sm ${curlFormat === 'cmd' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                                    >
                                      CMD
                                    </button>
                                    <button
                                      onClick={() => setCurlFormat('bash')}
                                      className={`px-3 py-1 rounded text-sm ${curlFormat === 'bash' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                                    >
                                      Bash/WSL
                                    </button>
                                  </div>
                                  
                                  {/* Curl Command Display */}
                                  <div className="relative">
                                    <pre className="bg-black/50 p-4 rounded text-green-300 text-xs overflow-x-auto border border-red-500/30">
                                      {curlData[key][curlFormat]}
                                    </pre>
                                    <button
                                      onClick={() => copyCurlToClipboard(curlData[key][curlFormat], `${key}-${curlFormat}`)}
                                      className="absolute top-2 right-2 p-2 bg-red-700 hover:bg-red-600 rounded transition"
                                      title="복사"
                                    >
                                      {copiedCurl === `${key}-${curlFormat}` ? (
                                        <Check className="w-4 h-4 text-green-400" />
                                      ) : (
                                        <Copy className="w-4 h-4" />
                                      )}
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {scanData.result?.public_apis && scanData.result.public_apis.length > 0 && (
                <div>
                  <h3 className="text-xl font-bold text-green-400 mb-3">🟢 Public APIs ({scanData.result.public_apis.length})</h3>
                  <div className="space-y-2">
                    {scanData.result.public_apis.map((endpoint: any, index: number) => {
                      const key = `public-${index}`;
                      const isExpanded = expandedEndpoints.has(key);
                      return (
                        <div key={key} className="bg-green-500/20 border border-green-500/50 rounded-lg overflow-hidden">
                          <div
                            className="p-4 flex items-center justify-between cursor-pointer hover:bg-green-500/30 transition"
                            onClick={() => toggleEndpoint(key)}
                          >
                            <div className="flex items-center gap-4 flex-1">
                              <span className={`px-3 py-1 rounded text-sm font-semibold ${getMethodColor(endpoint.method)}`}>
                                {endpoint.method}
                              </span>
                              <code className="text-green-200 font-semibold">{endpoint.url}</code>
                            </div>
                            {isExpanded ? <ChevronUp className="w-5 h-5 text-green-400" /> : <ChevronDown className="w-5 h-5 text-green-400" />}
                          </div>
                          {isExpanded && (
                            <div className="p-4 bg-green-900/30 border-t border-green-500/50 space-y-3">
                              {endpoint.parameters && Object.keys(endpoint.parameters).length > 0 && (
                                <div>
                                  <div className="text-green-300 font-semibold mb-2">Parameters:</div>
                                  <pre className="bg-black/30 p-3 rounded text-green-200 text-sm overflow-x-auto">
                                    {JSON.stringify(endpoint.parameters, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.source && (
                                <div>
                                  <span className="text-green-300 font-semibold">Source: </span>
                                  <span className="text-green-200">{endpoint.source}</span>
                                </div>
                              )}
                              
                              {/* Curl Command Buttons */}
                              <div className="mt-3 flex gap-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleCurl(endpoint.id, key, false);
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition"
                                  disabled={loadingCurl.has(key)}
                                >
                                  <Terminal className="w-4 h-4" />
                                  {loadingCurl.has(key) && !loadingCurl.has(`${key}-ai`) ? '로딩 중...' : showCurl.has(key) ? 'curl 숨기기' : 'curl 명령어 보기'}
                                </button>
                                
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleCurl(endpoint.id, key, true);
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded transition"
                                  disabled={loadingCurl.has(key)}
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                  </svg>
                                  {loadingCurl.has(`${key}-ai`) ? 'AI 생성 중...' : 'AI로 curl 생성'}
                                </button>
                              </div>
                                
                              {showCurl.has(key) && curlData[key] && (
                                <div className="mt-3 space-y-3">
                                  {/* Format Selector */}
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => setCurlFormat('powershell')}
                                      className={`px-3 py-1 rounded text-sm ${curlFormat === 'powershell' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                                    >
                                      PowerShell
                                    </button>
                                    <button
                                      onClick={() => setCurlFormat('cmd')}
                                      className={`px-3 py-1 rounded text-sm ${curlFormat === 'cmd' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                                    >
                                      CMD
                                    </button>
                                    <button
                                      onClick={() => setCurlFormat('bash')}
                                      className={`px-3 py-1 rounded text-sm ${curlFormat === 'bash' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                                    >
                                      Bash/WSL
                                    </button>
                                  </div>
                                  
                                  {/* Curl Command Display */}
                                  <div className="relative">
                                    <pre className="bg-black/50 p-4 rounded text-green-300 text-xs overflow-x-auto border border-green-500/30">
                                      {curlData[key][curlFormat]}
                                    </pre>
                                    <button
                                      onClick={() => copyCurlToClipboard(curlData[key][curlFormat], `${key}-${curlFormat}`)}
                                      className="absolute top-2 right-2 p-2 bg-green-700 hover:bg-green-600 rounded transition"
                                      title="복사"
                                    >
                                      {copiedCurl === `${key}-${curlFormat}` ? (
                                        <Check className="w-4 h-4 text-green-400" />
                                      ) : (
                                        <Copy className="w-4 h-4" />
                                      )}
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {(!scanData.result?.endpoints || scanData.result.endpoints.length === 0) && (
                <div className="text-center py-12 text-gray-400">
                  <Info className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>발견된 엔드포인트가 없습니다</p>
                </div>
              )}
            </div>
          )}

          {/* Vulnerabilities Tab */}
          {activeTab === 'vulnerabilities' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-white">
                  취약점 목록
                </h2>
                {scanData.result?.vulnerabilities && scanData.result.vulnerabilities.length > 0 && (
                  <button
                    onClick={generateAllPocs}
                    disabled={generatingAllPocs}
                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg font-semibold flex items-center gap-2 transition"
                  >
                    {generatingAllPocs ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                        <span>PoC 생성 중...</span>
                      </>
                    ) : (
                      <>
                        <FileCode className="w-4 h-4" />
                        <span>전체 PoC 생성</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {scanData.result?.vulnerabilities && scanData.result.vulnerabilities.length > 0 ? (
                <div className="space-y-3">
                  {scanData.result.vulnerabilities.map((vuln: any, index: number) => {
                    const isExpanded = expandedVulns.has(index);
                    return (
                      <div key={index} className={`border rounded-lg overflow-hidden ${getSeverityColor(vuln.level)}`}>
                        <div
                          className="p-4 flex items-center justify-between cursor-pointer hover:opacity-80 transition"
                          onClick={() => toggleVuln(index)}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className={`px-3 py-1 rounded text-sm font-bold ${getSeverityColor(vuln.level)}`}>
                                {vuln.level?.toUpperCase()}
                              </span>
                              <span className="font-bold text-lg">{vuln.type}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <span className={`px-2 py-1 rounded ${getMethodColor(vuln.method)}`}>
                                {vuln.method}
                              </span>
                              <code className="font-mono">{vuln.endpoint}</code>
                            </div>
                          </div>
                          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                        </div>
                        {isExpanded && (
                          <div className="p-4 bg-black/30 border-t space-y-4">
                            <div>
                              <div className="font-semibold mb-2">📝 설명:</div>
                              <p className="text-sm leading-relaxed">{vuln.description}</p>
                            </div>
                            {vuln.evidence && (
                              <div>
                                <div className="font-semibold mb-2">🔍 증거:</div>
                                <pre className="bg-black/50 p-3 rounded text-sm overflow-x-auto">{vuln.evidence}</pre>
                              </div>
                            )}
                            <div>
                              <div className="font-semibold mb-2">💡 권장사항:</div>
                              <p className="text-sm leading-relaxed">{vuln.recommendation}</p>
                            </div>
                            {vuln.cwe_id && (
                              <div>
                                <span className="font-semibold">CWE ID: </span>
                                <a
                                  href={`https://cwe.mitre.org/data/definitions/${vuln.cwe_id.replace('CWE-', '')}.html`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1"
                                >
                                  {vuln.cwe_id}
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </div>
                            )}
                            
                            {/* PoC Section */}
                            <div className="mt-4 pt-4 border-t border-white/20">
                              <div className="flex items-center justify-between mb-3">
                                <div className="font-semibold text-lg">🔬 PoC (Proof of Concept)</div>
                                {!vuln.poc_code && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      generatePocForVuln(vuln.id, index);
                                    }}
                                    disabled={generatingPoc.has(index)}
                                    className="px-3 py-1.5 bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg text-sm font-semibold flex items-center gap-2 transition"
                                  >
                                    {generatingPoc.has(index) ? (
                                      <>
                                        <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" />
                                        <span>생성 중...</span>
                                      </>
                                    ) : (
                                      <>
                                        <FileCode className="w-3 h-3" />
                                        <span>PoC 생성</span>
                                      </>
                                    )}
                                  </button>
                                )}
                              </div>
                              
                              {vuln.poc_code ? (
                                <div className="relative">
                                  <pre className="bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto border border-green-500/30">
                                    <code className="text-green-300">{vuln.poc_code}</code>
                                  </pre>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      navigator.clipboard.writeText(vuln.poc_code);
                                      alert('PoC 코드가 클립보드에 복사되었습니다!');
                                    }}
                                    className="absolute top-2 right-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold transition"
                                  >
                                    복사
                                  </button>
                                </div>
                              ) : (
                                <div className="bg-gray-900/50 p-6 rounded-lg text-center border border-dashed border-gray-600">
                                  <FileCode className="w-8 h-8 mx-auto mb-2 text-gray-500" />
                                  <p className="text-gray-400 text-sm">
                                    PoC 코드가 생성되지 않았습니다.<br />
                                    <span className="text-gray-500">위의 &quot;PoC 생성&quot; 버튼을 클릭하여 생성하세요.</span>
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <Shield className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>발견된 취약점이 없습니다</p>
                </div>
              )}
            </div>
          )}

          {/* Discovered Paths Tab */}
          {activeTab === 'paths' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white mb-4">
                발견된 경로
              </h2>

              {scanData.result?.discovered_paths && scanData.result.discovered_paths.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {scanData.result.discovered_paths.map((pathData: any, index: number) => (
                    <div key={index} className="bg-purple-900/40 rounded-lg p-4 hover:bg-purple-900/60 transition">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-purple-400">🔗</span>
                        <code className="text-purple-200 text-sm font-semibold flex-1 break-all">
                          {pathData.path || pathData}
                        </code>
                      </div>
                      {pathData.status_code && (
                        <div className="flex flex-wrap gap-2 text-xs mt-2">
                          <span className={`px-2 py-1 rounded ${
                            pathData.status_code === 200 ? 'bg-green-500/20 text-green-300' :
                            pathData.status_code >= 300 && pathData.status_code < 400 ? 'bg-yellow-500/20 text-yellow-300' :
                            'bg-blue-500/20 text-blue-300'
                          }`}>
                            Status: {pathData.status_code}
                          </span>
                          {pathData.content_length && (
                            <span className="px-2 py-1 rounded bg-purple-500/20 text-purple-300">
                              Size: {(pathData.content_length / 1024).toFixed(2)} KB
                            </span>
                          )}
                          {pathData.content_type && (
                            <span className="px-2 py-1 rounded bg-gray-500/20 text-gray-300">
                              {pathData.content_type.split(';')[0]}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <Info className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>발견된 경로가 없습니다</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
