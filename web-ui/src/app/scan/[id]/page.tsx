'use client';

import { useEffect, useState, useRef } from 'react';
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
  Download,
  StopCircle,
  MessageSquare,
  Send,
  Bot,
  User as UserIcon
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

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function ScanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scanId = params.id as string;

  const [scanData, setScanData] = useState<ScanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedEndpoints, setExpandedEndpoints] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'overview' | 'endpoints' | 'paths' | 'chat'>('overview');
  const [copiedCurl, setCopiedCurl] = useState<string | null>(null);
  const [stopping, setStopping] = useState(false);
  
  // AI Chat states
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
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

  // Auto-scroll chat to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages, isSendingMessage]);

  // Auto-scroll chat to bottom when switching to chat tab
  useEffect(() => {
    if (activeTab === 'chat' && chatContainerRef.current) {
      // Use setTimeout to ensure DOM is rendered
      setTimeout(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
      }, 100);
    }
  }, [activeTab]);

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

  // Download single endpoint as .http/.req file
  const downloadSingleEndpoint = async (endpointId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    try {
      const response = await fetch(`http://localhost:5001/api/endpoint/${endpointId}/http-request`);
      const data = await response.json();
      
      if (data.success) {
        // Create download link
        const blob = new Blob([data.content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename.replace('.http', '.req'); // Use .req extension
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        // Also download as .http
        const url2 = window.URL.createObjectURL(blob);
        const a2 = document.createElement('a');
        a2.href = url2;
        a2.download = data.filename;
        document.body.appendChild(a2);
        a2.click();
        document.body.removeChild(a2);
        window.URL.revokeObjectURL(url2);
      } else {
        alert('❌ 파일 생성 실패: ' + (data.error || '알 수 없는 오류'));
      }
    } catch (err) {
      console.error('Failed to download:', err);
      alert('❌ 다운로드 실패: ' + err);
    }
  };

  // Download single endpoint as Burp Suite format
  const downloadBurpRequest = async (endpointId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    try {
      const response = await fetch(`http://localhost:5001/api/endpoint/${endpointId}/http-request?format=burp`);
      const data = await response.json();
      
      if (data.success) {
        // Create download link
        const blob = new Blob([data.content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        alert('❌ 파일 생성 실패: ' + (data.error || '알 수 없는 오류'));
      }
    } catch (err) {
      console.error('Failed to download:', err);
      alert('❌ 다운로드 실패: ' + err);
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

  const handleStopScan = async () => {
    if (!scanData || scanData.status !== 'running') return;
    
    if (!confirm('스캔을 정지하시겠습니까? 진행 중인 작업이 취소됩니다.')) {
      return;
    }

    try {
      setStopping(true);
      await api.post(`/api/scan/${scanId}/stop`);
      // Reload scan detail after stopping
      await loadScanDetail();
      alert('스캔이 정지되었습니다.');
    } catch (err: any) {
      console.error('Failed to stop scan:', err);
      alert(err.response?.data?.error || '스캔 정지에 실패했습니다.');
    } finally {
      setStopping(false);
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || isSendingMessage || !scanData) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsSendingMessage(true);

    try {
      // Prepare comprehensive scan context for AI (with actual endpoint data)
      const allEndpoints = [
        ...(scanData.result?.shadow_apis || []),
        ...(scanData.result?.public_apis || [])
      ];

      // Sample endpoints by status code for better analysis
      const endpointsByStatus = {
        success_2xx: allEndpoints.filter(ep => ep.status_code >= 200 && ep.status_code < 300).slice(0, 5),
        redirect_3xx: allEndpoints.filter(ep => ep.status_code >= 300 && ep.status_code < 400).slice(0, 3),
        client_error_4xx: allEndpoints.filter(ep => ep.status_code >= 400 && ep.status_code < 500).slice(0, 5),
        server_error_5xx: allEndpoints.filter(ep => ep.status_code >= 500 && ep.status_code < 600).slice(0, 3)
      };

      // Identify sensitive endpoints
      const sensitivePatterns = /admin|api|auth|login|password|token|key|secret|user|account|config|settings/i;
      const sensitiveEndpoints = allEndpoints
        .filter(ep => sensitivePatterns.test(ep.url))
        .slice(0, 10);

      const scanContext = {
        target_url: scanData.target_url,
        status: scanData.status,
        statistics: scanData.result?.statistics,
        total_endpoints: allEndpoints.length,
        discovered_paths_count: scanData.result?.discovered_paths?.length || 0,
        // Add sample endpoint data with request/response details for intelligent analysis
        endpoint_samples: {
          by_status: {
            success_2xx: endpointsByStatus.success_2xx.map(ep => ({
              url: ep.url,
              method: ep.method,
              status_code: ep.status_code,
              request_headers: ep.request_headers,
              request_body: ep.request_body,
              response_headers: ep.response_headers,
              response_body: ep.response_body,
              response_time: ep.response_time,
              source: ep.source
            })),
            redirect_3xx: endpointsByStatus.redirect_3xx.map(ep => ({
              url: ep.url,
              method: ep.method,
              status_code: ep.status_code,
              request_headers: ep.request_headers,
              request_body: ep.request_body,
              response_headers: ep.response_headers,
              response_body: ep.response_body,
              response_time: ep.response_time,
              source: ep.source
            })),
            client_error_4xx: endpointsByStatus.client_error_4xx.map(ep => ({
              url: ep.url,
              method: ep.method,
              status_code: ep.status_code,
              request_headers: ep.request_headers,
              request_body: ep.request_body,
              response_headers: ep.response_headers,
              response_body: ep.response_body,
              response_time: ep.response_time,
              source: ep.source
            })),
            server_error_5xx: endpointsByStatus.server_error_5xx.map(ep => ({
              url: ep.url,
              method: ep.method,
              status_code: ep.status_code,
              request_headers: ep.request_headers,
              request_body: ep.request_body,
              response_headers: ep.response_headers,
              response_body: ep.response_body,
              response_time: ep.response_time,
              source: ep.source
            }))
          },
          sensitive_endpoints: sensitiveEndpoints.map(ep => ({
            url: ep.url,
            method: ep.method,
            status_code: ep.status_code,
            request_headers: ep.request_headers,
            request_body: ep.request_body,
            response_headers: ep.response_headers,
            response_body: ep.response_body,
            response_time: ep.response_time,
            source: ep.source
          }))
        },
        // Add endpoint methods distribution
        methods_distribution: {
          GET: allEndpoints.filter(ep => ep.method === 'GET').length,
          POST: allEndpoints.filter(ep => ep.method === 'POST').length,
          PUT: allEndpoints.filter(ep => ep.method === 'PUT').length,
          DELETE: allEndpoints.filter(ep => ep.method === 'DELETE').length,
          PATCH: allEndpoints.filter(ep => ep.method === 'PATCH').length
        }
      };

      // Send message to AI endpoint (optimized - only last 4 messages)
      const response = await api.post('/api/chat', {
        message: userMessage.content,
        scan_context: scanContext,
        conversation_history: chatMessages.slice(-4) // Last 4 messages for better performance
      }, {
        timeout: 35000 // 35 second timeout
      });

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.response || '죄송합니다. 응답을 생성할 수 없습니다.',
        timestamp: new Date()
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Failed to send message:', err);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '죄송합니다. 메시지 전송 중 오류가 발생했습니다. 나중에 다시 시도해주세요.',
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
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
                <div className="flex items-center gap-2">
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
                    <button
                      onClick={handleStopScan}
                      disabled={stopping}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition"
                    >
                      <StopCircle className="w-5 h-5" />
                      {stopping ? '정지 중...' : '스캔 정지'}
                    </button>
                  )}
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
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-6 py-3 rounded-lg font-semibold transition whitespace-nowrap flex items-center gap-2 ${
              activeTab === 'chat'
                ? 'bg-blue-600 text-white'
                : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            <MessageSquare className="w-5 h-5" />
            AI 챗
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
              
              {/* Unified Endpoint List */}
              {(() => {
                // Combine shadow_apis and public_apis
                const allEndpoints = [
                  ...(scanData.result?.shadow_apis || []),
                  ...(scanData.result?.public_apis || [])
                ];
                
                const filteredEndpoints = filterAndSortEndpoints(allEndpoints, 'all');
                
                return (
                  <>
                    {filteredEndpoints.length === 0 ? (
                      <div className="text-center py-8 text-gray-400">
                        <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>필터 조건에 맞는 엔드포인트가 없습니다</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="text-xl font-bold text-white">
                            전체 엔드포인트 ({filteredEndpoints.length}/{allEndpoints.length})
                          </h3>
                        </div>
                        {filteredEndpoints.map((endpoint: any, index: number) => {
                          const key = `endpoint-${index}`;
                          const isExpanded = expandedEndpoints.has(key);
                          const isShadow = endpoint.is_shadow_api;
                          
                          return (
                            <div 
                              key={key} 
                              className={`border rounded-lg overflow-hidden ${
                                isShadow 
                                  ? 'bg-red-500/10 border-red-500/50' 
                                  : 'bg-green-500/10 border-green-500/50'
                              }`}
                            >
                              <div
                                className={`p-4 flex items-center justify-between cursor-pointer transition ${
                                  isShadow
                                    ? 'hover:bg-red-500/20'
                                    : 'hover:bg-green-500/20'
                                }`}
                                onClick={() => toggleEndpoint(key)}
                              >
                                <div className="flex items-center gap-4 flex-1">
                                  {isShadow && (
                                    <span className="px-2 py-0.5 bg-red-500/30 text-red-300 rounded text-xs font-semibold">
                                      🔴 Shadow
                                    </span>
                                  )}
                                  {!isShadow && (
                                    <span className="px-2 py-0.5 bg-green-500/30 text-green-300 rounded text-xs font-semibold">
                                      🟢 Public
                                    </span>
                                  )}
                                  <span className={`px-3 py-1 rounded text-sm font-semibold ${getMethodColor(endpoint.method)}`}>
                                    {endpoint.method}
                                  </span>
                                  <code className={`font-semibold ${isShadow ? 'text-red-200' : 'text-green-200'}`}>
                                    {endpoint.url}
                                  </code>
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
                                {isExpanded ? (
                                  <ChevronUp className={`w-5 h-5 ${isShadow ? 'text-red-400' : 'text-green-400'}`} />
                                ) : (
                                  <ChevronDown className={`w-5 h-5 ${isShadow ? 'text-red-400' : 'text-green-400'}`} />
                                )}
                              </div>
                              {isExpanded && (
                                <div className={`p-4 border-t space-y-3 ${
                                  isShadow 
                                    ? 'bg-red-900/20 border-red-500/50' 
                                    : 'bg-green-900/20 border-green-500/50'
                                }`}>
                                  {endpoint.curl_command && (
                                    <div>
                                      <div className="flex items-center justify-between mb-2">
                                        <div className={`flex items-center gap-2 font-semibold ${
                                          isShadow ? 'text-red-300' : 'text-green-300'
                                        }`}>
                                          <Terminal className="w-4 h-4" />
                                          <span>cURL Command:</span>
                                        </div>
                                        <div className="flex gap-2">
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              copyCurl(endpoint.curl_command, key);
                                            }}
                                            className={`flex items-center gap-1 px-3 py-1 text-white rounded text-sm transition ${
                                              isShadow
                                                ? 'bg-red-600 hover:bg-red-700'
                                                : 'bg-green-600 hover:bg-green-700'
                                            }`}
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
                                          <button
                                            onClick={(e) => downloadSingleEndpoint(endpoint.id, e)}
                                            className="flex items-center gap-1 px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition"
                                          >
                                            <Download className="w-4 h-4" />
                                            <span>.req</span>
                                          </button>
                                          <button
                                            onClick={(e) => downloadBurpRequest(endpoint.id, e)}
                                            className="flex items-center gap-1 px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white rounded text-sm transition"
                                          >
                                            <Download className="w-4 h-4" />
                                            <span>Burp</span>
                                          </button>
                                        </div>
                                      </div>
                                      <pre className={`bg-black/30 p-3 rounded text-sm overflow-x-auto whitespace-pre-wrap break-all ${
                                        isShadow ? 'text-red-200' : 'text-green-200'
                                      }`}>
                                        {endpoint.curl_command}
                                      </pre>
                                    </div>
                                  )}
                                  {endpoint.headers && Object.keys(endpoint.headers).length > 0 && (
                                    <div>
                                      <div className={`font-semibold mb-2 ${isShadow ? 'text-red-300' : 'text-green-300'}`}>
                                        Headers:
                                      </div>
                                      <pre className={`bg-black/30 p-3 rounded text-sm overflow-x-auto ${
                                        isShadow ? 'text-red-200' : 'text-green-200'
                                      }`}>
                                        {JSON.stringify(endpoint.headers, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                  {endpoint.body_example && (
                                    <div>
                                      <div className={`font-semibold mb-2 ${isShadow ? 'text-red-300' : 'text-green-300'}`}>
                                        Request Body:
                                      </div>
                                      <pre className={`bg-black/30 p-3 rounded text-sm overflow-x-auto ${
                                        isShadow ? 'text-red-200' : 'text-green-200'
                                      }`}>
                                        {typeof endpoint.body_example === 'string'
                                          ? endpoint.body_example
                                          : JSON.stringify(endpoint.body_example, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                  {endpoint.parameters && Object.keys(endpoint.parameters).length > 0 && (
                                    <div>
                                      <div className={`font-semibold mb-2 ${isShadow ? 'text-red-300' : 'text-green-300'}`}>
                                        Parameters:
                                      </div>
                                      <pre className={`bg-black/30 p-3 rounded text-sm overflow-x-auto ${
                                        isShadow ? 'text-red-200' : 'text-green-200'
                                      }`}>
                                        {JSON.stringify(endpoint.parameters, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                  {endpoint.response_example && (
                                    <div>
                                      <div className={`font-semibold mb-2 ${isShadow ? 'text-red-300' : 'text-green-300'}`}>
                                        Response Example:
                                      </div>
                                      <pre className={`bg-black/30 p-3 rounded text-sm overflow-x-auto ${
                                        isShadow ? 'text-red-200' : 'text-green-200'
                                      }`}>
                                        {typeof endpoint.response_example === 'string'
                                          ? endpoint.response_example
                                          : JSON.stringify(endpoint.response_example, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                  {endpoint.source && (
                                    <div>
                                      <div className={`font-semibold mb-2 ${isShadow ? 'text-red-300' : 'text-green-300'}`}>
                                        Source:
                                      </div>
                                      <div className={`text-sm ${isShadow ? 'text-red-200' : 'text-green-200'}`}>
                                        {endpoint.source}
                                      </div>
                                    </div>
                                  )}
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

          {/* AI Chat Tab */}
          {activeTab === 'chat' && (
            <div className="flex flex-col h-[600px]">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                  <Bot className="w-7 h-7 text-blue-400" />
                  AI 어시스턴트
                  <span className="text-xs px-2 py-1 bg-green-600/20 text-green-400 rounded-full font-normal">
                    🧠 고급 분석 모드
                  </span>
                </h2>
                <p className="text-gray-400 text-sm mb-3">
                  실제 엔드포인트 데이터를 분석하여 구체적인 보안 권장사항을 제공합니다.
                </p>
                
                {/* Quick Question Buttons */}
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setChatInput('스캔 결과를 요약하고 주요 발견사항을 알려줘')}
                    className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 rounded-lg text-xs font-semibold transition"
                  >
                    📊 스캔 요약
                  </button>
                  <button
                    onClick={() => setChatInput('보안 취약점을 분석하고 위험도를 평가해줘')}
                    className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-300 rounded-lg text-xs font-semibold transition"
                  >
                    🔒 보안 분석
                  </button>
                  <button
                    onClick={() => setChatInput('4xx 에러가 발생한 엔드포인트를 분석해줘')}
                    className="px-3 py-1.5 bg-orange-600/20 hover:bg-orange-600/30 text-orange-300 rounded-lg text-xs font-semibold transition"
                  >
                    ⚠️ 에러 분석
                  </button>
                  <button
                    onClick={() => setChatInput('민감한 엔드포인트(admin, api, auth 등)의 보안 상태를 점검해줘')}
                    className="px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-300 rounded-lg text-xs font-semibold transition"
                  >
                    🎯 민감 엔드포인트
                  </button>
                  <button
                    onClick={() => setChatInput('API 설계 품질을 평가하고 개선 방안을 제안해줘')}
                    className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded-lg text-xs font-semibold transition"
                  >
                    💡 개선 권장
                  </button>
                </div>
              </div>

              {/* Chat Messages */}
              <div 
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto bg-gray-800/50 rounded-lg p-4 mb-4 space-y-4"
              >
                {chatMessages.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <Bot className="w-16 h-16 mx-auto mb-4 opacity-30 text-blue-400" />
                    <h3 className="text-lg font-semibold text-white mb-2">고급 AI 분석 준비 완료</h3>
                    <p className="mb-4 text-sm">실제 엔드포인트 데이터를 기반으로 구체적인 분석을 제공합니다</p>
                    <div className="text-sm space-y-2 mt-4 max-w-md mx-auto text-left">
                      <p className="text-gray-500 font-semibold">💡 똑똑한 질문 예시:</p>
                      <div className="bg-gray-700/30 rounded-lg p-3 space-y-1.5">
                        <p className="text-blue-400">• "GET 메서드가 가장 많은데, POST/PUT/DELETE는 왜 적어?"</p>
                        <p className="text-blue-400">• "401/403 에러가 있는 엔드포인트의 보안 상태는?"</p>
                        <p className="text-blue-400">• "/admin이나 /api 경로의 접근 제어는 적절해?"</p>
                        <p className="text-blue-400">• "5xx 에러가 발생한 엔드포인트를 우선순위로 수정해야 해?"</p>
                      </div>
                      <p className="text-xs text-gray-500 mt-3">👆 위 버튼을 클릭하거나 직접 질문을 입력하세요</p>
                    </div>
                  </div>
                ) : (
                  chatMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-3 ${
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {msg.role === 'assistant' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                            <Bot className="w-5 h-5 text-white" />
                          </div>
                        </div>
                      )}
                      <div
                        className={`max-w-[80%] rounded-lg p-4 ${
                          msg.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700/50 text-gray-200'
                        }`}
                      >
                        <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                        <div className="text-xs opacity-70 mt-2">
                          {msg.timestamp.toLocaleTimeString('ko-KR')}
                        </div>
                      </div>
                      {msg.role === 'user' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                            <UserIcon className="w-5 h-5 text-white" />
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
                {isSendingMessage && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                        <Bot className="w-5 h-5 text-white" />
                      </div>
                    </div>
                    <div className="bg-gray-700/50 text-gray-200 rounded-lg p-4">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="flex gap-2">
                <textarea
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="스캔 결과에 대해 질문하세요... (Shift+Enter로 줄바꿈, Enter로 전송)"
                  disabled={isSendingMessage}
                  className="flex-1 px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition resize-none"
                  rows={3}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!chatInput.trim() || isSendingMessage}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition flex items-center gap-2"
                >
                  <Send className="w-5 h-5" />
                  전송
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
