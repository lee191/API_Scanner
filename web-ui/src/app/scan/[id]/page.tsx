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
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
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
  count_2xx?: number;
  count_3xx?: number;
  count_4xx?: number;
  count_5xx?: number;
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
  const [activeTab, setActiveTab] = useState<'overview' | 'endpoints' | 'paths'>('overview');
  const [copiedCurl, setCopiedCurl] = useState<string | null>(null);
  
  // New filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [filterMethod, setFilterMethod] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterSource, setFilterSource] = useState<string>('all'); // all, static, ai
  const [sortBy, setSortBy] = useState<'url' | 'method' | 'status'>('url');

  useEffect(() => {
    loadScanDetail();
  }, [scanId]);

  // Poll scan status if it's still running
  useEffect(() => {
    if (!scanData || scanData.status !== 'running') {
      return;
    }

    const pollInterval = setInterval(() => {
      loadScanDetail();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [scanData?.status]);

  const loadScanDetail = async () => {
    try {
      setLoading(true);
      // Add timestamp to prevent caching
      const timestamp = new Date().getTime();
      const response = await api.get(`/api/status/${scanId}?_t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
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

  const copyCurl = async (curlCommand: string, key: string) => {
    try {
      await navigator.clipboard.writeText(curlCommand);
      setCopiedCurl(key);
      setTimeout(() => setCopiedCurl(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Expand/Collapse all endpoints
  const expandAll = () => {
    const allKeys = new Set<string>();
    scanData?.result?.shadow_apis?.forEach((_, idx) => allKeys.add(`shadow-${idx}`));
    scanData?.result?.public_apis?.forEach((_, idx) => allKeys.add(`public-${idx}`));
    setExpandedEndpoints(allKeys);
  };

  const collapseAll = () => {
    setExpandedEndpoints(new Set());
  };

  // Filter and sort endpoints
  const filterAndSortEndpoints = (endpoints: any[], prefix: string) => {
    if (!endpoints) return [];
    
    let filtered = endpoints.filter((ep) => {
      // Search filter
      if (searchQuery && !ep.url.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      
      // Method filter
      if (filterMethod !== 'all' && ep.method?.toUpperCase() !== filterMethod.toUpperCase()) {
        return false;
      }
      
      // Status filter
      if (filterStatus !== 'all') {
        if (filterStatus === '2xx' && (ep.status_code < 200 || ep.status_code >= 300)) return false;
        if (filterStatus === '3xx' && (ep.status_code < 300 || ep.status_code >= 400)) return false;
        if (filterStatus === '4xx' && (ep.status_code < 400 || ep.status_code >= 500)) return false;
        if (filterStatus === '5xx' && (ep.status_code < 500 || ep.status_code >= 600)) return false;
      }
      
      // Source filter
      if (filterSource !== 'all') {
        if (filterSource === 'ai' && !ep.source?.startsWith('AI:')) return false;
        if (filterSource === 'static' && !ep.source?.startsWith('Static:')) return false;
      }
      
      return true;
    });

    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'url') return a.url.localeCompare(b.url);
      if (sortBy === 'method') return (a.method || '').localeCompare(b.method || '');
      if (sortBy === 'status') return (a.status_code || 0) - (b.status_code || 0);
      return 0;
    });

    return filtered;
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

              <div className="flex flex-col items-end gap-2">
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
                {scanData.status === 'running' && (
                  <div className="w-48">
                    <div className="flex justify-between text-sm text-gray-400 mb-1">
                      <span>진행률</span>
                      <span>{scanData.progress || 0}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${scanData.progress || 0}%` }}
                      />
                    </div>
                    {scanData.message && (
                      <div className="text-xs text-gray-400 mt-1">{scanData.message}</div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
              <div className="bg-blue-500/20 rounded-lg p-4 border border-blue-500/30">
                <div className="text-blue-300 text-sm mb-1">총 엔드포인트</div>
                <div className="text-3xl font-bold text-blue-400">{stats.total_endpoints || 0}</div>
              </div>
              <div className="bg-green-500/20 rounded-lg p-4 border border-green-500/30">
                <div className="text-green-300 text-sm mb-1">2xx 성공</div>
                <div className="text-3xl font-bold text-green-400">{stats.count_2xx || 0}</div>
              </div>
              <div className="bg-cyan-500/20 rounded-lg p-4 border border-cyan-500/30">
                <div className="text-cyan-300 text-sm mb-1">3xx 리다이렉트</div>
                <div className="text-3xl font-bold text-cyan-400">{stats.count_3xx || 0}</div>
              </div>
              <div className="bg-orange-500/20 rounded-lg p-4 border border-orange-500/30">
                <div className="text-orange-300 text-sm mb-1">4xx 클라이언트 에러</div>
                <div className="text-3xl font-bold text-orange-400">{stats.count_4xx || 0}</div>
              </div>
              <div className="bg-red-500/20 rounded-lg p-4 border border-red-500/30">
                <div className="text-red-300 text-sm mb-1">5xx 서버 에러</div>
                <div className="text-3xl font-bold text-red-400">{stats.count_5xx || 0}</div>
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
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-white">
                  엔드포인트 목록
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={expandAll}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition flex items-center gap-2"
                  >
                    <ChevronDown className="w-4 h-4" />
                    모두 펼치기
                  </button>
                  <button
                    onClick={collapseAll}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-semibold transition flex items-center gap-2"
                  >
                    <ChevronUp className="w-4 h-4" />
                    모두 접기
                  </button>
                </div>
              </div>

              {/* Filters */}
              <div className="bg-gray-800/50 rounded-lg p-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {/* Search */}
                  <div className="lg:col-span-2">
                    <label className="block text-sm font-semibold text-gray-300 mb-2">🔍 검색</label>
                    <input
                      type="text"
                      placeholder="URL로 검색..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition"
                    />
                  </div>

                  {/* Method Filter */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">HTTP 메서드</label>
                    <select
                      value={filterMethod}
                      onChange={(e) => setFilterMethod(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 transition"
                    >
                      <option value="all">전체</option>
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="DELETE">DELETE</option>
                      <option value="PATCH">PATCH</option>
                    </select>
                  </div>

                  {/* Status Filter */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">상태 코드</label>
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 transition"
                    >
                      <option value="all">전체</option>
                      <option value="2xx">2xx (성공)</option>
                      <option value="3xx">3xx (리다이렉트)</option>
                      <option value="4xx">4xx (클라이언트 오류)</option>
                      <option value="5xx">5xx (서버 오류)</option>
                    </select>
                  </div>

                  {/* Source Filter */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">탐지 방법</label>
                    <select
                      value={filterSource}
                      onChange={(e) => setFilterSource(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 transition"
                    >
                      <option value="all">전체</option>
                      <option value="static">정적 분석</option>
                      <option value="ai">🤖 AI 분석</option>
                    </select>
                  </div>
                </div>

                {/* Sort */}
                <div className="flex items-center gap-4">
                  <span className="text-sm font-semibold text-gray-300">정렬:</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSortBy('url')}
                      className={`px-3 py-1 rounded-lg text-sm font-semibold transition ${
                        sortBy === 'url'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      URL
                    </button>
                    <button
                      onClick={() => setSortBy('method')}
                      className={`px-3 py-1 rounded-lg text-sm font-semibold transition ${
                        sortBy === 'method'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      메서드
                    </button>
                    <button
                      onClick={() => setSortBy('status')}
                      className={`px-3 py-1 rounded-lg text-sm font-semibold transition ${
                        sortBy === 'status'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      상태 코드
                    </button>
                  </div>
                </div>
              </div>
              
              {scanData.result?.shadow_apis && scanData.result.shadow_apis.length > 0 && (
                <div className="mb-6">
                  {(() => {
                    const filteredShadow = filterAndSortEndpoints(scanData.result!.shadow_apis, 'shadow');
                    return (
                      <>
                        <h3 className="text-xl font-bold text-blue-400 mb-3">
                          � 엔드포인트 목록 ({filteredShadow.length}/{scanData.result!.shadow_apis.length})
                        </h3>
                        {filteredShadow.length === 0 ? (
                          <div className="text-center py-8 text-gray-400">
                            <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                            <p>필터 조건에 맞는 엔드포인트가 없습니다</p>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {filteredShadow.map((endpoint: any, index: number) => {
                              const key = `shadow-${index}`;
                              const isExpanded = expandedEndpoints.has(key);
                      return (
                        <div key={key} className="bg-gray-500/20 border border-gray-500/50 rounded-lg overflow-hidden">
                          <div
                            className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-500/30 transition"
                            onClick={() => toggleEndpoint(key)}
                          >
                            <div className="flex items-center gap-4 flex-1">
                              <span className={`px-3 py-1 rounded text-sm font-semibold ${getMethodColor(endpoint.method)}`}>
                                {endpoint.method}
                              </span>
                              <code className="text-gray-200 font-semibold">{endpoint.url}</code>
                              {endpoint.status_code && (
                                <span className={`px-2 py-1 rounded text-xs font-semibold ml-2 ${
                                  endpoint.status_code >= 200 && endpoint.status_code < 300 ? 'bg-green-500/30 text-green-300' :
                                  endpoint.status_code === 404 ? 'bg-gray-500/30 text-gray-300' :
                                  endpoint.status_code === 401 || endpoint.status_code === 403 ? 'bg-yellow-500/30 text-yellow-300' :
                                  endpoint.status_code >= 400 && endpoint.status_code < 500 ? 'bg-orange-500/30 text-orange-300' :
                                  endpoint.status_code >= 500 ? 'bg-red-500/30 text-red-300' :
                                  'bg-blue-500/30 text-blue-300'
                                }`}>
                                  {endpoint.status_code}
                                </span>
                              )}
                              {endpoint.source && endpoint.source.startsWith('AI:') && (
                                <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded text-xs font-semibold ml-2">
                                  🤖 AI
                                </span>
                              )}
                            </div>
                            {isExpanded ? <ChevronUp className="w-5 h-5 text-red-400" /> : <ChevronDown className="w-5 h-5 text-red-400" />}
                          </div>
                          {isExpanded && (
                            <div className="p-4 bg-red-900/30 border-t border-red-500/50 space-y-3">
                              {endpoint.curl_command && (
                                <div>
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2 text-red-300 font-semibold">
                                      <Terminal className="w-4 h-4" />
                                      <span>cURL Command:</span>
                                    </div>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        copyCurl(endpoint.curl_command, key);
                                      }}
                                      className="flex items-center gap-1 px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition"
                                    >
                                      {copiedCurl === key ? (
                                        <>
                                          <Check className="w-4 h-4" />
                                          <span>복사됨</span>
                                        </>
                                      ) : (
                                        <>
                                          <Copy className="w-4 h-4" />
                                          <span>복사</span>
                                        </>
                                      )}
                                    </button>
                                  </div>
                                  <pre className="bg-black/30 p-3 rounded text-red-200 text-sm overflow-x-auto whitespace-pre-wrap break-all">
                                    {endpoint.curl_command}
                                  </pre>
                                </div>
                              )}
                              {endpoint.headers && Object.keys(endpoint.headers).length > 0 && (
                                <div>
                                  <div className="text-red-300 font-semibold mb-2">Headers:</div>
                                  <pre className="bg-black/30 p-3 rounded text-red-200 text-sm overflow-x-auto">
                                    {JSON.stringify(endpoint.headers, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.body_example && (
                                <div>
                                  <div className="text-red-300 font-semibold mb-2">Request Body:</div>
                                  <pre className="bg-black/30 p-3 rounded text-red-200 text-sm overflow-x-auto">
                                    {typeof endpoint.body_example === 'string'
                                      ? endpoint.body_example
                                      : JSON.stringify(endpoint.body_example, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.parameters && Object.keys(endpoint.parameters).length > 0 && (
                                <div>
                                  <div className="text-red-300 font-semibold mb-2">Parameters:</div>
                                  <pre className="bg-black/30 p-3 rounded text-red-200 text-sm overflow-x-auto">
                                    {JSON.stringify(endpoint.parameters, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.response_example && (
                                <div>
                                  <div className="text-red-300 font-semibold mb-2">Response Example:</div>
                                  <pre className="bg-black/30 p-3 rounded text-red-200 text-sm overflow-x-auto">
                                    {typeof endpoint.response_example === 'string'
                                      ? endpoint.response_example
                                      : JSON.stringify(endpoint.response_example, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.poc_code && (
                                <div>
                                  <div className="text-red-300 font-semibold mb-2">PoC Code:</div>
                                  <pre className="bg-black/30 p-3 rounded text-red-200 text-sm overflow-x-auto">
                                    {endpoint.poc_code}
                                  </pre>
                                </div>
                              )}
                              <div className="flex items-center justify-between pt-2 border-t border-red-500/30">
                                <div className="flex items-center gap-2">
                                  <span className="text-red-300 font-semibold">Source: </span>
                                  <span className="text-red-200">{endpoint.source}</span>
                                </div>
                                {endpoint.status_code && (
                                  <div>
                                    <span className="text-red-300 font-semibold">Status: </span>
                                    <span className={`px-2 py-1 rounded text-xs ${
                                      endpoint.status_code >= 200 && endpoint.status_code < 300 ? 'bg-green-500/20 text-green-300' :
                                      endpoint.status_code >= 400 ? 'bg-red-500/20 text-red-300' :
                                      'bg-yellow-500/20 text-yellow-300'
                                    }`}>
                                      {endpoint.status_code}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                              );
                            })}
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}

              {scanData.result?.public_apis && scanData.result.public_apis.length > 0 && (
                <div>
                  {(() => {
                    const filteredPublic = filterAndSortEndpoints(scanData.result!.public_apis, 'public');
                    return (
                      <>
                        <h3 className="text-xl font-bold text-green-400 mb-3">
                          🟢 Public APIs ({filteredPublic.length}/{scanData.result!.public_apis.length})
                        </h3>
                        {filteredPublic.length === 0 ? (
                          <div className="text-center py-8 text-gray-400">
                            <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                            <p>필터 조건에 맞는 Public API가 없습니다</p>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {filteredPublic.map((endpoint: any, index: number) => {
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
                              {endpoint.status_code && (
                                <span className={`px-2 py-1 rounded text-xs font-semibold ml-2 ${
                                  endpoint.status_code >= 200 && endpoint.status_code < 300 ? 'bg-green-500/30 text-green-300' :
                                  endpoint.status_code === 404 ? 'bg-gray-500/30 text-gray-300' :
                                  endpoint.status_code === 401 || endpoint.status_code === 403 ? 'bg-yellow-500/30 text-yellow-300' :
                                  endpoint.status_code >= 400 && endpoint.status_code < 500 ? 'bg-orange-500/30 text-orange-300' :
                                  endpoint.status_code >= 500 ? 'bg-red-500/30 text-red-300' :
                                  'bg-blue-500/30 text-blue-300'
                                }`}>
                                  {endpoint.status_code}
                                </span>
                              )}
                              {endpoint.source && endpoint.source.startsWith('AI:') && (
                                <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded text-xs font-semibold ml-2">
                                  🤖 AI
                                </span>
                              )}
                            </div>
                            {isExpanded ? <ChevronUp className="w-5 h-5 text-green-400" /> : <ChevronDown className="w-5 h-5 text-green-400" />}
                          </div>
                          {isExpanded && (
                            <div className="p-4 bg-green-900/30 border-t border-green-500/50 space-y-3">
                              {endpoint.curl_command && (
                                <div>
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2 text-green-300 font-semibold">
                                      <Terminal className="w-4 h-4" />
                                      <span>cURL Command:</span>
                                    </div>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        copyCurl(endpoint.curl_command, key);
                                      }}
                                      className="flex items-center gap-1 px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition"
                                    >
                                      {copiedCurl === key ? (
                                        <>
                                          <Check className="w-4 h-4" />
                                          <span>복사됨</span>
                                        </>
                                      ) : (
                                        <>
                                          <Copy className="w-4 h-4" />
                                          <span>복사</span>
                                        </>
                                      )}
                                    </button>
                                  </div>
                                  <pre className="bg-black/30 p-3 rounded text-green-200 text-sm overflow-x-auto whitespace-pre-wrap break-all">
                                    {endpoint.curl_command}
                                  </pre>
                                </div>
                              )}
                              {endpoint.headers && Object.keys(endpoint.headers).length > 0 && (
                                <div>
                                  <div className="text-green-300 font-semibold mb-2">Headers:</div>
                                  <pre className="bg-black/30 p-3 rounded text-green-200 text-sm overflow-x-auto">
                                    {JSON.stringify(endpoint.headers, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.body_example && (
                                <div>
                                  <div className="text-green-300 font-semibold mb-2">Request Body:</div>
                                  <pre className="bg-black/30 p-3 rounded text-green-200 text-sm overflow-x-auto">
                                    {typeof endpoint.body_example === 'string'
                                      ? endpoint.body_example
                                      : JSON.stringify(endpoint.body_example, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.parameters && Object.keys(endpoint.parameters).length > 0 && (
                                <div>
                                  <div className="text-green-300 font-semibold mb-2">Parameters:</div>
                                  <pre className="bg-black/30 p-3 rounded text-green-200 text-sm overflow-x-auto">
                                    {JSON.stringify(endpoint.parameters, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.response_example && (
                                <div>
                                  <div className="text-green-300 font-semibold mb-2">Response Example:</div>
                                  <pre className="bg-black/30 p-3 rounded text-green-200 text-sm overflow-x-auto">
                                    {typeof endpoint.response_example === 'string'
                                      ? endpoint.response_example
                                      : JSON.stringify(endpoint.response_example, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {endpoint.poc_code && (
                                <div>
                                  <div className="text-green-300 font-semibold mb-2">PoC Code:</div>
                                  <pre className="bg-black/30 p-3 rounded text-green-200 text-sm overflow-x-auto">
                                    {endpoint.poc_code}
                                  </pre>
                                </div>
                              )}
                              <div className="flex items-center justify-between pt-2 border-t border-green-500/30">
                                <div className="flex items-center gap-2">
                                  <span className="text-green-300 font-semibold">Source: </span>
                                  <span className="text-green-200">{endpoint.source}</span>
                                  {endpoint.source && endpoint.source.startsWith('AI:') && (
                                    <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded text-xs font-semibold">
                                      🤖 AI
                                    </span>
                                  )}
                                </div>
                                {endpoint.status_code && (
                                  <div>
                                    <span className="text-green-300 font-semibold">Status: </span>
                                    <span className={`px-2 py-1 rounded text-xs ${
                                      endpoint.status_code >= 200 && endpoint.status_code < 300 ? 'bg-green-500/20 text-green-300' :
                                      endpoint.status_code >= 400 ? 'bg-red-500/20 text-red-300' :
                                      'bg-yellow-500/20 text-yellow-300'
                                    }`}>
                                      {endpoint.status_code}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                            })}
                          </div>
                        )}
                      </>
                    );
                  })()}
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
