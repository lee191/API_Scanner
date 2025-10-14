'use client';

import { useState, useEffect } from 'react';
import {
  Shield, Search, FileCode, AlertTriangle, CheckCircle, ChevronDown, ChevronRight,
  Copy, Terminal, Play, Download, History, BarChart3, Filter, X, Loader2,
  FileJson, FileSpreadsheet, Clock, TrendingUp, Folder, Edit2, Trash2, Plus, StopCircle
} from 'lucide-react';
import axios from 'axios';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// 색상 팔레트
const COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#6366f1'
};

const SEVERITY_COLORS = ['#ef4444', '#f97316', '#eab308', '#3b82f6'];

export default function ImprovedHome() {
  // 기본 상태
  const [targetUrl, setTargetUrl] = useState('');
  const [jsPath, setJsPath] = useState('');
  const [scanVulns, setScanVulns] = useState(true);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [bruteforceEnabled, setBruteforceEnabled] = useState(false);
  const [analysisType, setAnalysisType] = useState<'js_only' | 'full_scan'>('full_scan');
  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');

  // 프로젝트 상태
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingProject, setEditingProject] = useState<any>(null);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');

  // UI 상태
  const [activeTab, setActiveTab] = useState<'scan' | 'dashboard' | 'history' | 'projects'>('projects');
  const [expandedEndpoints, setExpandedEndpoints] = useState<Set<string>>(new Set());

  // 필터링 상태
  const [searchQuery, setSearchQuery] = useState('');
  const [filterMethod, setFilterMethod] = useState<string>('all');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);

  // PoC 실행 상태
  const [executingPoc, setExecutingPoc] = useState(false);
  const [pocResult, setPocResult] = useState<any>(null);
  const [showPocModal, setShowPocModal] = useState(false);

  // 히스토리
  const [scanHistory, setScanHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // 실시간 로그
  const [logs, setLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);

  // 초기 로드
  useEffect(() => {
    loadProjects();
  }, []);

  // 선택된 프로젝트가 변경될 때 히스토리 로드
  useEffect(() => {
    if (selectedProject) {
      loadProjectHistory(selectedProject);
    } else {
      setScanHistory([]);
    }
  }, [selectedProject]);

  // 프로젝트 목록 로드
  const loadProjects = async () => {
    try {
      const response = await axios.get('/api/projects');
      setProjects(response.data.projects || []);
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  };

  // 프로젝트 히스토리 로드
  const loadProjectHistory = async (projectId: string) => {
    setLoadingHistory(true);
    try {
      const response = await axios.get(`/api/projects/${projectId}`);
      const scans = response.data.scans || [];
      // 스캔을 히스토리 형식으로 변환
      const historyItems = scans.map((scan: any) => ({
        id: scan.scan_id,
        target: scan.target_url,
        timestamp: scan.created_at,
        result: {
          statistics: scan.statistics || {},
          shadow_apis: [],
          public_apis: [],
          vulnerabilities: []
        }
      }));
      setScanHistory(historyItems);
    } catch (err) {
      console.error('Failed to load project history:', err);
      setScanHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  // 프로젝트 생성
  const createProject = async () => {
    if (!newProjectName.trim()) {
      alert('프로젝트 이름을 입력해주세요');
      return;
    }

    try {
      const response = await axios.post('/api/projects', {
        name: newProjectName,
        description: newProjectDescription
      });
      setNewProjectName('');
      setNewProjectDescription('');
      setShowProjectModal(false);
      await loadProjects();
      alert('프로젝트가 생성되었습니다');
      // 자동으로 새 프로젝트 선택
      setSelectedProject(response.data.project.project_id);
    } catch (err: any) {
      alert(`프로젝트 생성 실패: ${err.response?.data?.error || err.message}`);
    }
  };

  // 프로젝트 수정
  const updateProject = async () => {
    if (!editingProject || !newProjectName.trim()) {
      alert('프로젝트 이름을 입력해주세요');
      return;
    }

    try {
      await axios.put(`/api/projects/${editingProject.project_id}`, {
        name: newProjectName,
        description: newProjectDescription
      });
      setNewProjectName('');
      setNewProjectDescription('');
      setShowEditModal(false);
      setEditingProject(null);
      await loadProjects();
      alert('프로젝트가 수정되었습니다');
    } catch (err: any) {
      alert(`프로젝트 수정 실패: ${err.response?.data?.error || err.message}`);
    }
  };

  // 프로젝트 수정 모달 열기
  const openEditModal = (project: any) => {
    setEditingProject(project);
    setNewProjectName(project.name);
    setNewProjectDescription(project.description || '');
    setShowEditModal(true);
  };

  // 프로젝트 삭제
  const deleteProject = async (projectId: string) => {
    if (!confirm('정말로 이 프로젝트를 삭제하시겠습니까? 프로젝트의 모든 스캔도 함께 삭제됩니다.')) {
      return;
    }

    try {
      await axios.delete(`/api/projects/${projectId}`);
      if (selectedProject === projectId) {
        setSelectedProject(null);
      }
      await loadProjects();
      alert('프로젝트가 삭제되었습니다');
    } catch (err: any) {
      alert(`프로젝트 삭제 실패: ${err.response?.data?.error || err.message}`);
    }
  };

  // 토글
  const toggleEndpoint = (id: string) => {
    const newExpanded = new Set(expandedEndpoints);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedEndpoints(newExpanded);
  };

  // 복사
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  // cURL 생성
  const generateCurlCommand = (endpoint: any) => {
    let cleanUrl = endpoint.url;
    cleanUrl = cleanUrl
      .replace(/\/:id\b/g, '/123')
      .replace(/\/:param\b/g, '/value')
      .replace(/\/:[a-zA-Z_]\w*/g, '/value');

    const url = cleanUrl.startsWith('http') ? cleanUrl : `${targetUrl}${cleanUrl}`;
    let curl = `curl -X ${endpoint.method} "${url}"`;

    if (endpoint.method !== 'GET' && endpoint.method !== 'DELETE') {
      curl += ` \\\n  -H "Content-Type: application/json"`;
      curl += ` \\\n  -d '{"key": "value"}'`;
    }

    return curl;
  };

  // PoC 실행
  const executePoc = async (pocCode: string) => {
    setExecutingPoc(true);
    setPocResult(null);
    setShowPocModal(true);

    try {
      const response = await axios.post('/api/execute-poc', {
        poc_code: pocCode,
        timeout: 30000
      });

      setPocResult(response.data);
    } catch (err: any) {
      setPocResult({
        success: false,
        error: err.response?.data?.error || err.message,
        stdout: err.response?.data?.stdout || '',
        stderr: err.response?.data?.stderr || ''
      });
    } finally {
      setExecutingPoc(false);
    }
  };

  // 데이터 내보내기
  const exportData = (format: 'json' | 'csv') => {
    if (!result) return;

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan_result_${Date.now()}.json`;
      a.click();
    } else {
      let csv = 'Type,Method,URL,Severity,Description\n';

      [...(result.shadow_apis || []), ...(result.public_apis || [])].forEach((ep: any) => {
        csv += `Endpoint,${ep.method},"${ep.url}",N/A,N/A\n`;
      });

      (result.vulnerabilities || []).forEach((vuln: any) => {
        csv += `Vulnerability,${vuln.method},"${vuln.endpoint}",${vuln.level},"${vuln.type}"\n`;
      });

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan_result_${Date.now()}.csv`;
      a.click();
    }
  };

  // 스캔 시작
  const startScan = async () => {
    if (!selectedProject) {
      setError('프로젝트를 선택해주세요');
      return;
    }

    if (!targetUrl) {
      setError('대상 URL을 입력해주세요');
      return;
    }

    setScanning(true);
    setError(null);
    setResult(null);
    setExpandedEndpoints(new Set());
    setLogs([]);
    setShowLogs(true);
    addLog('스캔 시작...');

    try {
      addLog(`대상: ${targetUrl}`);
      const response = await axios.post('/api/scan', {
        target_url: targetUrl,
        js_path: jsPath || undefined,
        project_id: selectedProject,
        scan_vulns: scanVulns,
        ai_enabled: aiEnabled,
        bruteforce_enabled: bruteforceEnabled,
        analysis_type: analysisType
      });

      const { scan_id } = response.data;
      setScanId(scan_id);
      addLog(`스캔 ID: ${scan_id}`);

      pollScanStatus(scan_id);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || 'Failed to start scan';
      setError(`스캔 시작 실패: ${errorMsg}`);
      addLog(`에러: ${errorMsg}`);
      setScanning(false);
    }
  };

  // 스캔 정지
  const stopScan = async () => {
    if (!scanId) return;

    try {
      addLog('스캔 중단 요청...');
      const response = await axios.post(`/api/scan/${scanId}/stop`);
      addLog('스캔이 중단되었습니다');
      setScanning(false);
      setError('스캔이 사용자에 의해 중단되었습니다');
      setStatusMessage('스캔 중단됨');
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message;
      addLog(`스캔 중단 실패: ${errorMsg}`);
      setError(`스캔 중단 실패: ${errorMsg}`);
    }
  };

  // 로그 추가
  const addLog = (message: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  // 폴링
  const pollScanStatus = async (id: string) => {
    let attempts = 0;
    const maxAttempts = 150;

    const interval = setInterval(async () => {
      attempts++;

      if (attempts >= maxAttempts) {
        clearInterval(interval);
        setError('Scan timeout');
        addLog('스캔 타임아웃');
        setScanning(false);
        return;
      }

      try {
        const response = await axios.get(`/api/status/${id}`);
        const status = response.data;

        setProgress(status.progress || 0);
        setStatusMessage(status.message || '');
        addLog(status.message || '');

        if (status.status === 'completed') {
          clearInterval(interval);
          setResult(status.result);
          setScanning(false);
          setProgress(100);
          setStatusMessage('스캔 완료!');
          addLog('스캔 완료!');
          // 프로젝트 히스토리 새로고침
          if (selectedProject) {
            loadProjectHistory(selectedProject);
          }
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setError(status.message || 'Scan failed');
          addLog(`스캔 실패: ${status.message}`);
          setScanning(false);
        }
      } catch (err: any) {
        clearInterval(interval);
        const errorMsg = err.response?.data?.error || err.message;
        setError(`스캔 상태 확인 실패: ${errorMsg}`);
        addLog(`에러: ${errorMsg}`);
        setScanning(false);
      }
    }, 2000);
  };

  // 필터링
  const getFilteredEndpoints = (endpoints: any[]) => {
    if (!endpoints) return [];

    return endpoints.filter(ep => {
      if (filterMethod !== 'all' && ep.method !== filterMethod) return false;
      if (searchQuery && !ep.url.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  };

  const getFilteredVulnerabilities = (vulnerabilities: any[]) => {
    if (!vulnerabilities) return [];

    return vulnerabilities.filter(vuln => {
      if (filterSeverity !== 'all' && vuln.level !== filterSeverity) return false;
      if (searchQuery && !vuln.type.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !vuln.endpoint.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  };

  // 대시보드 데이터
  const getDashboardData = () => {
    if (!result) return null;

    const stats = result.statistics || {};
    const vulns = result.vulnerabilities || [];

    const severityData = [
      { name: 'Critical', value: vulns.filter((v: any) => v.level === 'critical').length, color: COLORS.critical },
      { name: 'High', value: vulns.filter((v: any) => v.level === 'high').length, color: COLORS.high },
      { name: 'Medium', value: vulns.filter((v: any) => v.level === 'medium').length, color: COLORS.medium },
      { name: 'Low', value: vulns.filter((v: any) => v.level === 'low').length, color: COLORS.low }
    ];

    const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];
    const allEndpoints = [...(result.shadow_apis || []), ...(result.public_apis || [])];
    const methodData = methods.map(method => ({
      name: method,
      count: allEndpoints.filter((ep: any) => ep.method === method).length
    }));

    return { severityData, methodData, stats };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Shield className="w-12 h-12 text-blue-400" />
            <h1 className="text-4xl font-bold text-white">Shadow API Scanner</h1>
          </div>
          <p className="text-gray-300 text-lg">숨겨진 API와 보안 취약점을 발견합니다</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 max-w-5xl mx-auto">
          <button
            onClick={() => setActiveTab('projects')}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition ${
              activeTab === 'projects' ? 'bg-blue-600 text-white' : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            <Folder className="w-5 h-5 inline mr-2" />
            프로젝트 관리
          </button>
          <button
            onClick={() => setActiveTab('scan')}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition ${
              activeTab === 'scan' ? 'bg-blue-600 text-white' : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
            disabled={!selectedProject}
          >
            <Search className="w-5 h-5 inline mr-2" />
            스캔
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition ${
              activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
            disabled={!result}
          >
            <BarChart3 className="w-5 h-5 inline mr-2" />
            대시보드
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition ${
              activeTab === 'history' ? 'bg-blue-600 text-white' : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            <History className="w-5 h-5 inline mr-2" />
            히스토리 ({scanHistory.length})
          </button>
        </div>

        {/* 프로젝트 관리 탭 */}
        {activeTab === 'projects' && (
          <div className="max-w-6xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-lg p-8 mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Folder className="w-7 h-7 text-blue-400" />
                  프로젝트 관리
                </h2>
                <button
                  onClick={() => setShowProjectModal(true)}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold flex items-center gap-2"
                >
                  <Plus className="w-5 h-5" />
                  새 프로젝트 생성
                </button>
              </div>

              {projects.length === 0 ? (
                <div className="text-center py-12">
                  <Folder className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400 text-lg mb-6">프로젝트가 없습니다</p>
                  <button
                    onClick={() => setShowProjectModal(true)}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
                  >
                    첫 프로젝트 만들기
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {projects.map((project) => (
                    <div
                      key={project.project_id}
                      className={`bg-white/10 rounded-lg p-6 hover:bg-white/20 transition cursor-pointer border-2 ${
                        selectedProject === project.project_id ? 'border-blue-500' : 'border-transparent'
                      }`}
                      onClick={() => setSelectedProject(project.project_id)}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-white mb-2">{project.name}</h3>
                          {project.description && (
                            <p className="text-gray-300 text-sm mb-3">{project.description}</p>
                          )}
                        </div>
                        {selectedProject === project.project_id && (
                          <CheckCircle className="w-6 h-6 text-blue-400 flex-shrink-0 ml-2" />
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
                        <Clock className="w-4 h-4" />
                        <span>{new Date(project.created_at).toLocaleDateString()}</span>
                      </div>

                      <div className="bg-blue-500/20 rounded-lg p-3 mb-4">
                        <div className="text-2xl font-bold text-blue-400">{project.scan_count || 0}</div>
                        <div className="text-blue-200 text-sm">스캔 수행</div>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openEditModal(project);
                          }}
                          className="flex-1 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
                        >
                          <Edit2 className="w-4 h-4" />
                          수정
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteProject(project.project_id);
                          }}
                          className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          삭제
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {selectedProject && (
                <div className="mt-8 p-4 bg-blue-500/20 border border-blue-500 rounded-lg">
                  <p className="text-blue-200 font-semibold flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    선택된 프로젝트: {projects.find(p => p.project_id === selectedProject)?.name}
                  </p>
                  <p className="text-blue-300 text-sm mt-2">
                    스캔 탭으로 이동하여 보안 분석을 시작하세요
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 스캔 탭 */}
        {activeTab === 'scan' && (
          <div className="max-w-4xl mx-auto">
            {!selectedProject ? (
              <div className="bg-white/10 backdrop-blur-lg rounded-lg p-12 text-center">
                <Folder className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">프로젝트를 먼저 선택해주세요</h3>
                <p className="text-gray-300 mb-6">
                  스캔을 시작하려면 프로젝트 관리 탭에서 프로젝트를 선택하거나 생성하세요
                </p>
                <button
                  onClick={() => setActiveTab('projects')}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
                >
                  프로젝트 관리로 이동
                </button>
              </div>
            ) : (
              <>
                {/* Selected Project Info */}
                <div className="bg-blue-500/20 border border-blue-500 rounded-lg p-4 mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-200 font-semibold flex items-center gap-2">
                        <Folder className="w-5 h-5" />
                        현재 프로젝트: {projects.find(p => p.project_id === selectedProject)?.name}
                      </p>
                      <p className="text-blue-300 text-sm mt-1">
                        {projects.find(p => p.project_id === selectedProject)?.description || '설명 없음'}
                      </p>
                    </div>
                    <button
                      onClick={() => setActiveTab('projects')}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm"
                    >
                      변경
                    </button>
                  </div>
                </div>

                {/* Scan Form */}
                <div className="bg-white/10 backdrop-blur-lg rounded-lg p-8 mb-8">
                  <div className="space-y-6">
                    {/* Target URL */}
                    <div>
                      <label className="block text-white mb-2 font-semibold">대상 URL *</label>
                      <input
                        type="text"
                        value={targetUrl}
                        onChange={(e) => setTargetUrl(e.target.value)}
                        placeholder="http://localhost:5000"
                        className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400"
                      />
                    </div>

                    {/* JavaScript Path */}
                    <div>
                      <label className="block text-white mb-2 font-semibold">JavaScript 경로 (선택사항)</label>
                      <input
                        type="text"
                        value={jsPath}
                        onChange={(e) => setJsPath(e.target.value)}
                        placeholder="비워두면 자동으로 수집합니다"
                        className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400"
                      />
                    </div>

                    {/* Analysis Type */}
                    <div>
                      <label className="block text-white mb-2 font-semibold">분석 타입</label>
                      <div className="flex gap-4">
                        <button
                          onClick={() => setAnalysisType('js_only')}
                          className={`flex-1 py-3 px-4 rounded-lg font-semibold transition ${
                            analysisType === 'js_only' ? 'bg-blue-500 text-white' : 'bg-white/20 text-gray-300 hover:bg-white/30'
                          }`}
                        >
                          <FileCode className="w-5 h-5 inline mr-2" />
                          JS 분석만
                        </button>
                        <button
                          onClick={() => setAnalysisType('full_scan')}
                          className={`flex-1 py-3 px-4 rounded-lg font-semibold transition ${
                            analysisType === 'full_scan' ? 'bg-blue-500 text-white' : 'bg-white/20 text-gray-300 hover:bg-white/30'
                          }`}
                        >
                          <Search className="w-5 h-5 inline mr-2" />
                          전체 스캔
                        </button>
                      </div>
                    </div>

                    {/* Options */}
                    {analysisType === 'full_scan' && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            id="scanVulns"
                            checked={scanVulns}
                            onChange={(e) => setScanVulns(e.target.checked)}
                            className="w-5 h-5 rounded"
                          />
                          <label htmlFor="scanVulns" className="text-white font-semibold">취약점 스캔</label>
                        </div>
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            id="aiEnabled"
                            checked={aiEnabled}
                            onChange={(e) => setAiEnabled(e.target.checked)}
                            className="w-5 h-5 rounded"
                          />
                          <label htmlFor="aiEnabled" className="text-white font-semibold flex items-center gap-2">
                            🤖 AI 분석 활성화
                            <span className="text-xs text-gray-400">(PoC 코드 자동 생성)</span>
                          </label>
                        </div>
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            id="bruteforceEnabled"
                            checked={bruteforceEnabled}
                            onChange={(e) => setBruteforceEnabled(e.target.checked)}
                            className="w-5 h-5 rounded"
                          />
                          <label htmlFor="bruteforceEnabled" className="text-white font-semibold flex items-center gap-2">
                            🔍 디렉토리 브루트포싱
                            <span className="text-xs text-gray-400">(숨겨진 경로 탐색 및 JS 수집)</span>
                          </label>
                        </div>
                      </div>
                    )}

                    {/* Start Button */}
                    <button
                      onClick={startScan}
                      disabled={scanning || !selectedProject}
                      className="w-full py-4 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold rounded-lg transition text-lg"
                    >
                      {scanning ? (
                        <>
                          <Loader2 className="w-5 h-5 inline mr-2 animate-spin" />
                          스캔 중...
                        </>
                      ) : (
                        <>
                          <Search className="w-5 h-5 inline mr-2" />
                          스캔 시작
                        </>
                      )}
                    </button>
                  </div>

                  {/* Progress */}
                  {scanning && (
                    <div className="mt-6 p-4 bg-blue-500/20 border border-blue-500 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-blue-200 font-semibold">진행률: {progress}%</span>
                        <button
                          onClick={stopScan}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold flex items-center gap-2 transition"
                        >
                          <StopCircle className="w-4 h-4" />
                          스캔 정지
                        </button>
                      </div>
                      <div className="flex items-center gap-3 mb-3">
                        <div className="flex-1">
                          <div className="w-full bg-gray-700 rounded-full h-2.5">
                            <div
                              className="bg-blue-500 h-2.5 rounded-full transition-all duration-300"
                              style={{ width: `${progress}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="text-blue-300 text-sm whitespace-nowrap">{statusMessage}</span>
                      </div>
                      {scanId && (
                        <div className="text-gray-400 text-xs">Scan ID: {scanId}</div>
                      )}
                    </div>
                  )}

                  {/* Error */}
                  {error && (
                    <div className="mt-6 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-200">
                      <AlertTriangle className="w-5 h-5 inline mr-2" />
                      {error}
                    </div>
                  )}
                </div>

                {/* Logs Panel */}
                {showLogs && logs.length > 0 && (
                  <div className="bg-black/40 backdrop-blur-lg rounded-lg p-6 mb-8">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <Terminal className="w-5 h-5" />
                        실시간 로그
                      </h3>
                      <button
                        onClick={() => setShowLogs(false)}
                        className="text-gray-400 hover:text-white"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                    <div className="bg-gray-900 rounded-lg p-4 max-h-60 overflow-y-auto font-mono text-xs text-green-400">
                      {logs.map((log, i) => (
                        <div key={i}>{log}</div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Results */}
                {result && (
                  <div className="bg-white/10 backdrop-blur-lg rounded-lg p-8">
                    {/* Header with Export */}
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <CheckCircle className="w-7 h-7 text-green-400" />
                        스캔 결과
                      </h2>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setShowFilters(!showFilters)}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2"
                        >
                          <Filter className="w-4 h-4" />
                          필터
                        </button>
                        <button
                          onClick={() => exportData('json')}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg flex items-center gap-2"
                        >
                          <FileJson className="w-4 h-4" />
                          JSON
                        </button>
                        <button
                          onClick={() => exportData('csv')}
                          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2"
                        >
                          <FileSpreadsheet className="w-4 h-4" />
                          CSV
                        </button>
                      </div>
                    </div>

                    {/* Filters */}
                    {showFilters && (
                      <div className="mb-6 p-4 bg-white/10 rounded-lg space-y-3">
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="URL 또는 취약점 검색..."
                          className="w-full px-4 py-2 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30"
                        />
                        <div className="flex gap-4">
                          <select
                            value={filterMethod}
                            onChange={(e) => setFilterMethod(e.target.value)}
                            className="flex-1 px-4 py-2 rounded-lg bg-white/20 text-white border border-white/30"
                          >
                            <option value="all">모든 메서드</option>
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                            <option value="PUT">PUT</option>
                            <option value="DELETE">DELETE</option>
                            <option value="PATCH">PATCH</option>
                          </select>
                          <select
                            value={filterSeverity}
                            onChange={(e) => setFilterSeverity(e.target.value)}
                            className="flex-1 px-4 py-2 rounded-lg bg-white/20 text-white border border-white/30"
                          >
                            <option value="all">모든 심각도</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                          </select>
                        </div>
                      </div>
                    )}

                    {/* Statistics */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
                      <div className="bg-white/10 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-white">{result.statistics?.total_endpoints || 0}</div>
                        <div className="text-gray-300 text-sm">전체 엔드포인트</div>
                      </div>
                      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-red-400">{result.statistics?.shadow_apis || 0}</div>
                        <div className="text-red-200 text-sm">숨겨진 API</div>
                      </div>
                      <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-green-400">{result.statistics?.public_apis || 0}</div>
                        <div className="text-green-200 text-sm">일반 API</div>
                      </div>
                      <div className="bg-purple-500/20 border border-purple-500/50 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-purple-400">{result.statistics?.discovered_paths || 0}</div>
                        <div className="text-purple-200 text-sm">발견된 경로</div>
                      </div>
                      <div className="bg-orange-500/20 border border-orange-500/50 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-orange-400">{result.statistics?.total_vulnerabilities || 0}</div>
                        <div className="text-orange-200 text-sm">취약점</div>
                      </div>
                    </div>

                    {/* Discovered Paths Section */}
                    {result.discovered_paths && result.discovered_paths.length > 0 && (
                      <div className="mb-8">
                        <div className="bg-purple-500/20 border border-purple-500/50 rounded-lg p-6">
                          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="text-purple-400">🔍 Discovered Paths</span>
                            <span className="text-purple-300">({result.discovered_paths.length}개)</span>
                          </h3>
                          <p className="text-gray-300 text-sm mb-4">브루트포싱을 통해 발견된 숨겨진 경로들입니다:</p>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
                            {result.discovered_paths.map((path: string, index: number) => (
                              <div key={index} className="bg-purple-900/40 rounded-lg p-3 flex items-center gap-3 hover:bg-purple-900/60 transition">
                                <span className="text-purple-400">🔗</span>
                                <code className="text-purple-200 text-sm font-semibold flex-1 break-all">{path}</code>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Shadow APIs */}
                    {getFilteredEndpoints(result.shadow_apis).length > 0 && (
                      <div className="mb-8">
                        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                          <span className="text-red-400">🔴 Shadow APIs</span>
                          <span className="text-red-300">({getFilteredEndpoints(result.shadow_apis).length}개)</span>
                        </h3>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {getFilteredEndpoints(result.shadow_apis).map((endpoint: any, index: number) => {
                            const isExpanded = expandedEndpoints.has(`shadow-${index}`);
                            return (
                              <div key={index} className="bg-red-500/20 border border-red-500/50 rounded-lg overflow-hidden">
                                <div
                                  className="p-4 flex items-center gap-4 cursor-pointer hover:bg-red-500/30 transition"
                                  onClick={() => toggleEndpoint(`shadow-${index}`)}
                                >
                                  {isExpanded ? <ChevronDown className="w-5 h-5 text-red-300" /> : <ChevronRight className="w-5 h-5 text-red-300" />}
                                  <span className={`px-3 py-1 rounded font-semibold text-sm ${
                                    endpoint.method === 'GET' ? 'bg-blue-500' :
                                    endpoint.method === 'POST' ? 'bg-green-500' :
                                    endpoint.method === 'DELETE' ? 'bg-red-500' :
                                    'bg-gray-500'
                                  } text-white`}>
                                    {endpoint.method}
                                  </span>
                                  <code className="flex-1 text-red-200 font-semibold">{endpoint.url}</code>
                                  <span className="px-2 py-1 bg-red-600 text-white text-xs rounded">SHADOW</span>
                                </div>

                                {isExpanded && (
                                  <div className="px-4 pb-4 space-y-3 bg-red-900/20">
                                    {/* cURL */}
                                    <div>
                                      <div className="flex items-center justify-between mb-2">
                                        <p className="text-red-200 font-semibold text-sm flex items-center gap-2">
                                          <Terminal className="w-4 h-4" />
                                          cURL:
                                        </p>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            copyToClipboard(generateCurlCommand(endpoint));
                                          }}
                                          className="flex items-center gap-1 px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white"
                                        >
                                          <Copy className="w-3 h-3" />
                                          복사
                                        </button>
                                      </div>
                                      <pre className="bg-gray-900 p-3 rounded text-xs text-green-400 overflow-x-auto">
                                        {generateCurlCommand(endpoint)}
                                      </pre>
                                    </div>

                                    {/* PoC */}
                                    {endpoint.poc_code && (
                                      <div>
                                        <div className="flex items-center justify-between mb-2">
                                          <p className="text-red-200 font-semibold text-sm">🔥 PoC 코드:</p>
                                          <div className="flex gap-2">
                                            <button
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                executePoc(endpoint.poc_code);
                                              }}
                                              className="flex items-center gap-1 px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs text-white"
                                            >
                                              <Play className="w-3 h-3" />
                                              실행
                                            </button>
                                            <button
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                copyToClipboard(endpoint.poc_code);
                                              }}
                                              className="flex items-center gap-1 px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white"
                                            >
                                              <Copy className="w-3 h-3" />
                                              복사
                                            </button>
                                          </div>
                                        </div>
                                        <pre className="bg-gray-900 p-3 rounded text-xs text-blue-400 overflow-x-auto">
                                          {endpoint.poc_code}
                                        </pre>
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

                    {/* Public APIs */}
                    {getFilteredEndpoints(result.public_apis).length > 0 && (
                      <div className="mb-8">
                        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                          <span className="text-green-400">🟢 Public APIs</span>
                          <span className="text-green-300">({getFilteredEndpoints(result.public_apis).length}개)</span>
                        </h3>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {getFilteredEndpoints(result.public_apis).map((endpoint: any, index: number) => {
                            const isExpanded = expandedEndpoints.has(`public-${index}`);
                            return (
                              <div key={index} className="bg-green-500/20 border border-green-500/50 rounded-lg overflow-hidden">
                                <div
                                  className="p-4 flex items-center gap-4 cursor-pointer hover:bg-green-500/30 transition"
                                  onClick={() => toggleEndpoint(`public-${index}`)}
                                >
                                  {isExpanded ? <ChevronDown className="w-5 h-5 text-green-300" /> : <ChevronRight className="w-5 h-5 text-green-300" />}
                                  <span className={`px-3 py-1 rounded font-semibold text-sm ${
                                    endpoint.method === 'GET' ? 'bg-blue-500' :
                                    endpoint.method === 'POST' ? 'bg-green-500' :
                                    endpoint.method === 'PUT' ? 'bg-yellow-500' :
                                    endpoint.method === 'DELETE' ? 'bg-red-500' :
                                    'bg-gray-500'
                                  } text-white`}>
                                    {endpoint.method}
                                  </span>
                                  <code className="flex-1 text-green-200 font-semibold">{endpoint.url}</code>
                                  <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">PUBLIC</span>
                                </div>

                                {isExpanded && (
                                  <div className="px-4 pb-4 space-y-3 bg-green-900/20">
                                    {/* cURL */}
                                    <div>
                                      <div className="flex items-center justify-between mb-2">
                                        <p className="text-green-200 font-semibold text-sm flex items-center gap-2">
                                          <Terminal className="w-4 h-4" />
                                          cURL:
                                        </p>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            copyToClipboard(generateCurlCommand(endpoint));
                                          }}
                                          className="flex items-center gap-1 px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs text-white"
                                        >
                                          <Copy className="w-3 h-3" />
                                          복사
                                        </button>
                                      </div>
                                      <pre className="bg-gray-900 p-3 rounded text-xs text-green-400 overflow-x-auto">
                                        {generateCurlCommand(endpoint)}
                                      </pre>
                                    </div>

                                    {/* PoC */}
                                    {endpoint.poc_code && (
                                      <div>
                                        <div className="flex items-center justify-between mb-2">
                                          <p className="text-green-200 font-semibold text-sm">🔥 PoC 코드:</p>
                                          <div className="flex gap-2">
                                            <button
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                executePoc(endpoint.poc_code);
                                              }}
                                              className="flex items-center gap-1 px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white"
                                            >
                                              <Play className="w-3 h-3" />
                                              실행
                                            </button>
                                            <button
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                copyToClipboard(endpoint.poc_code);
                                              }}
                                              className="flex items-center gap-1 px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs text-white"
                                            >
                                              <Copy className="w-3 h-3" />
                                              복사
                                            </button>
                                          </div>
                                        </div>
                                        <pre className="bg-gray-900 p-3 rounded text-xs text-blue-400 overflow-x-auto">
                                          {endpoint.poc_code}
                                        </pre>
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

                    {/* Vulnerabilities */}
                    {getFilteredVulnerabilities(result.vulnerabilities).length > 0 && (
                      <div>
                        <h3 className="text-xl font-bold text-white mb-4">
                          취약점 ({getFilteredVulnerabilities(result.vulnerabilities).length})
                        </h3>
                        <div className="space-y-4 max-h-96 overflow-y-auto">
                          {getFilteredVulnerabilities(result.vulnerabilities).map((vuln: any, index: number) => {
                            const isVulnExpanded = expandedEndpoints.has(`vuln-${index}`);
                            return (
                              <div
                                key={index}
                                className={`rounded-lg border-l-4 overflow-hidden ${
                                  vuln.level === 'critical' ? 'bg-red-500/20 border-red-500' :
                                  vuln.level === 'high' ? 'bg-orange-500/20 border-orange-500' :
                                  vuln.level === 'medium' ? 'bg-yellow-500/20 border-yellow-500' :
                                  'bg-blue-500/20 border-blue-500'
                                }`}
                              >
                                <div
                                  className="p-4 cursor-pointer hover:bg-black/20 transition"
                                  onClick={() => toggleEndpoint(`vuln-${index}`)}
                                >
                                  <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                      {isVulnExpanded ? <ChevronDown className="w-5 h-5 text-white" /> : <ChevronRight className="w-5 h-5 text-white" />}
                                      <h4 className="font-bold text-white">{vuln.type}</h4>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                      vuln.level === 'critical' ? 'bg-red-500' :
                                      vuln.level === 'high' ? 'bg-orange-500' :
                                      vuln.level === 'medium' ? 'bg-yellow-500' :
                                      'bg-blue-500'
                                    } text-white uppercase`}>
                                      {vuln.level}
                                    </span>
                                  </div>
                                  <p className="text-gray-200 text-sm mb-2">{vuln.description}</p>
                                  <code className="text-gray-300 text-xs block">{vuln.method} {vuln.endpoint}</code>
                                </div>

                                {isVulnExpanded && vuln.poc_code && (
                                  <div className="px-4 pb-4 bg-black/30">
                                    <div className="flex items-center justify-between mb-2">
                                      <p className="text-white font-semibold text-sm">🔥 PoC 코드:</p>
                                      <div className="flex gap-2">
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            executePoc(vuln.poc_code);
                                          }}
                                          className="flex items-center gap-1 px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs text-white"
                                        >
                                          <Play className="w-3 h-3" />
                                          실행
                                        </button>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            copyToClipboard(vuln.poc_code);
                                          }}
                                          className={`flex items-center gap-1 px-2 py-1 rounded text-xs text-white ${
                                            vuln.level === 'critical' ? 'bg-red-600 hover:bg-red-700' :
                                            'bg-blue-600 hover:bg-blue-700'
                                          }`}
                                        >
                                          <Copy className="w-3 h-3" />
                                          복사
                                        </button>
                                      </div>
                                    </div>
                                    <pre className="bg-gray-900 p-3 rounded text-xs text-blue-400 overflow-x-auto">
                                      {vuln.poc_code}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* 대시보드 탭 */}
        {activeTab === 'dashboard' && result && (
          <div className="max-w-6xl mx-auto">
            {(() => {
              const dashData = getDashboardData();
              if (!dashData) return null;

              return (
                <div className="space-y-8">
                  <div className="bg-white/10 backdrop-blur-lg rounded-lg p-8">
                    <h2 className="text-2xl font-bold text-white mb-6">통계 대시보드</h2>

                    {/* 주요 통계 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                      <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-blue-400">{dashData.stats.total_endpoints || 0}</div>
                        <div className="text-blue-200 text-sm">총 엔드포인트</div>
                      </div>
                      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-red-400">{dashData.stats.shadow_apis || 0}</div>
                        <div className="text-red-200 text-sm">Shadow APIs</div>
                      </div>
                      {dashData.stats.discovered_paths > 0 && (
                        <div className="bg-purple-500/20 border border-purple-500/50 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-purple-400">{dashData.stats.discovered_paths || 0}</div>
                          <div className="text-purple-200 text-sm">발견된 경로</div>
                        </div>
                      )}
                      <div className="bg-orange-500/20 border border-orange-500/50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-orange-400">{dashData.stats.total_vulnerabilities || 0}</div>
                        <div className="text-orange-200 text-sm">취약점</div>
                      </div>
                    </div>

                    {/* 차트 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      {/* 취약점 심각도 */}
                      <div>
                        <h3 className="text-lg font-bold text-white mb-4">취약점 심각도 분포</h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={dashData.severityData.filter((d: any) => d.value > 0)}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={(entry: any) => `${entry.name}: ${entry.value}`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {dashData.severityData.map((entry: any, index: number) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>

                      {/* 메서드 분포 */}
                      <div>
                        <h3 className="text-lg font-bold text-white mb-4">HTTP 메서드 분포</h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={dashData.methodData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                            <XAxis dataKey="name" stroke="#fff" />
                            <YAxis stroke="#fff" />
                            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                            <Bar dataKey="count" fill="#3b82f6" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* 히스토리 탭 */}
        {activeTab === 'history' && (
          <div className="max-w-6xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">스캔 히스토리</h2>
                {selectedProject && (
                  <div className="text-blue-300 text-sm">
                    프로젝트: {projects.find(p => p.project_id === selectedProject)?.name}
                  </div>
                )}
              </div>

              {!selectedProject ? (
                <div className="text-center py-12">
                  <Folder className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400 text-lg mb-2">프로젝트를 선택해주세요</p>
                  <p className="text-gray-500 text-sm">
                    프로젝트 관리 탭에서 프로젝트를 선택하면 해당 프로젝트의 스캔 히스토리를 볼 수 있습니다
                  </p>
                </div>
              ) : loadingHistory ? (
                <div className="text-center py-12">
                  <Loader2 className="w-12 h-12 animate-spin text-blue-400 mx-auto mb-4" />
                  <p className="text-gray-300">히스토리 로드 중...</p>
                </div>
              ) : scanHistory.length === 0 ? (
                <div className="text-center py-12">
                  <History className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400 text-lg mb-2">이 프로젝트에는 스캔 기록이 없습니다</p>
                  <p className="text-gray-500 text-sm mb-6">
                    스캔 탭으로 이동하여 첫 번째 스캔을 시작하세요
                  </p>
                  <button
                    onClick={() => setActiveTab('scan')}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
                  >
                    스캔 시작하기
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {scanHistory.map((item: any, index: number) => (
                    <div key={index} className="bg-white/10 rounded-lg p-6 hover:bg-white/20 transition cursor-pointer"
                         onClick={() => {
                           setResult(item.result);
                           setTargetUrl(item.target);
                           setActiveTab('scan');
                         }}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <Clock className="w-5 h-5 text-blue-400" />
                          <span className="text-white font-semibold">{item.target}</span>
                        </div>
                        <span className="text-gray-400 text-sm">
                          {new Date(item.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex gap-4 text-sm flex-wrap">
                        <span className="text-gray-300">
                          엔드포인트: {item.result?.statistics?.total_endpoints || 0}
                        </span>
                        <span className="text-gray-300">
                          Shadow APIs: {item.result?.statistics?.shadow_apis || 0}
                        </span>
                        {item.result?.statistics?.discovered_paths > 0 && (
                          <span className="text-purple-300">
                            발견된 경로: {item.result?.statistics?.discovered_paths || 0}
                          </span>
                        )}
                        <span className="text-gray-300">
                          취약점: {item.result?.statistics?.total_vulnerabilities || 0}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* PoC 실행 모달 */}
        {showPocModal && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Terminal className="w-6 h-6" />
                    PoC 실행 결과
                  </h3>
                  <button
                    onClick={() => setShowPocModal(false)}
                    className="text-gray-400 hover:text-white"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                {executingPoc ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-12 h-12 animate-spin text-blue-400 mx-auto mb-4" />
                    <p className="text-gray-300">PoC 실행 중...</p>
                  </div>
                ) : pocResult ? (
                  <div className="space-y-4">
                    {/* 상태 */}
                    <div className={`p-4 rounded-lg ${
                      pocResult.success ? 'bg-green-500/20 border border-green-500' : 'bg-red-500/20 border border-red-500'
                    }`}>
                      <p className={`font-semibold ${pocResult.success ? 'text-green-200' : 'text-red-200'}`}>
                        {pocResult.success ? '✅ 실행 성공' : '❌ 실행 실패'}
                      </p>
                      {pocResult.error && (
                        <p className="text-red-300 text-sm mt-2">{pocResult.error}</p>
                      )}
                    </div>

                    {/* stdout */}
                    {pocResult.stdout && (
                      <div>
                        <h4 className="text-white font-semibold mb-2">표준 출력:</h4>
                        <pre className="bg-gray-800 p-4 rounded text-xs text-green-400 overflow-x-auto">
                          {pocResult.stdout}
                        </pre>
                      </div>
                    )}

                    {/* stderr */}
                    {pocResult.stderr && (
                      <div>
                        <h4 className="text-white font-semibold mb-2">에러 출력:</h4>
                        <pre className="bg-gray-800 p-4 rounded text-xs text-red-400 overflow-x-auto">
                          {pocResult.stderr}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        )}

        {/* 프로젝트 생성 모달 */}
        {showProjectModal && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 rounded-lg max-w-lg w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">새 프로젝트 생성</h3>
                  <button
                    onClick={() => {
                      setShowProjectModal(false);
                      setNewProjectName('');
                      setNewProjectDescription('');
                    }}
                    className="text-gray-400 hover:text-white"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-white mb-2 font-semibold">프로젝트 이름 *</label>
                    <input
                      type="text"
                      value={newProjectName}
                      onChange={(e) => setNewProjectName(e.target.value)}
                      placeholder="예: 메인 서비스 스캔"
                      className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400"
                      onKeyPress={(e) => e.key === 'Enter' && createProject()}
                    />
                  </div>

                  <div>
                    <label className="block text-white mb-2 font-semibold">설명 (선택사항)</label>
                    <textarea
                      value={newProjectDescription}
                      onChange={(e) => setNewProjectDescription(e.target.value)}
                      placeholder="프로젝트에 대한 간단한 설명을 입력하세요"
                      rows={3}
                      className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400 resize-none"
                    />
                  </div>

                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={createProject}
                      className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg"
                    >
                      생성
                    </button>
                    <button
                      onClick={() => {
                        setShowProjectModal(false);
                        setNewProjectName('');
                        setNewProjectDescription('');
                      }}
                      className="flex-1 py-3 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-lg"
                    >
                      취소
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 프로젝트 수정 모달 */}
        {showEditModal && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 rounded-lg max-w-lg w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">프로젝트 수정</h3>
                  <button
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingProject(null);
                      setNewProjectName('');
                      setNewProjectDescription('');
                    }}
                    className="text-gray-400 hover:text-white"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-white mb-2 font-semibold">프로젝트 이름 *</label>
                    <input
                      type="text"
                      value={newProjectName}
                      onChange={(e) => setNewProjectName(e.target.value)}
                      placeholder="예: 메인 서비스 스캔"
                      className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400"
                      onKeyPress={(e) => e.key === 'Enter' && updateProject()}
                    />
                  </div>

                  <div>
                    <label className="block text-white mb-2 font-semibold">설명 (선택사항)</label>
                    <textarea
                      value={newProjectDescription}
                      onChange={(e) => setNewProjectDescription(e.target.value)}
                      placeholder="프로젝트에 대한 간단한 설명을 입력하세요"
                      rows={3}
                      className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400 resize-none"
                    />
                  </div>

                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={updateProject}
                      className="flex-1 py-3 bg-yellow-600 hover:bg-yellow-700 text-white font-semibold rounded-lg"
                    >
                      수정
                    </button>
                    <button
                      onClick={() => {
                        setShowEditModal(false);
                        setEditingProject(null);
                        setNewProjectName('');
                        setNewProjectDescription('');
                      }}
                      className="flex-1 py-3 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-lg"
                    >
                      취소
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
