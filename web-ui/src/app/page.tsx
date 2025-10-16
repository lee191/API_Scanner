'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Shield, Search, FileCode, AlertTriangle, CheckCircle, ChevronDown, ChevronRight,
  Copy, Terminal, Play, Download, History, BarChart3, Filter, X, Loader2,
  FileJson, FileSpreadsheet, Clock, TrendingUp, Folder, Edit2, Trash2, Plus, StopCircle,
  Settings, Menu, Home, Scan, FolderOpen, Activity, Globe, Info, Target, Eye, FileText,
  Calendar, PieChart as PieChartIcon
} from 'lucide-react';
import axios from 'axios';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// API Base URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

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
  const router = useRouter();
  
  // 기본 상태
  const [targetUrl, setTargetUrl] = useState('');
  const [jsPath, setJsPath] = useState('');
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 대시보드 상태
  const [dashStats, setDashStats] = useState<any>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);
  const [endpointVulnerabilities, setEndpointVulnerabilities] = useState<any[]>([]);
  const [showEndpointVulnModal, setShowEndpointVulnModal] = useState(false);

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

  // 대시보드 탭이 활성화되고 프로젝트가 선택되면 통계 로드
  useEffect(() => {
    if (activeTab === 'dashboard' && selectedProject) {
      loadProjectStatistics(selectedProject);
    }
  }, [activeTab, selectedProject]);

  // 프로젝트 목록 로드
  const loadProjects = async () => {
    try {
      const response = await api.get('/api/projects');
      setProjects(response.data.projects || []);
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  };

  // 프로젝트 히스토리 로드
  const loadProjectHistory = async (projectId: string) => {
    setLoadingHistory(true);
    try {
      const response = await api.get(`/api/projects/${projectId}`);
      const scans = response.data.scans || [];
      // 스캔을 히스토리 형식으로 변환
      const historyItems = scans.map((scan: any) => ({
        id: scan.scan_id,
        target: scan.target_url,
        timestamp: scan.created_at,
        status: scan.status,
        result: {
          statistics: scan.statistics || {}
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

  // 프로젝트 통계 로드
  const loadProjectStatistics = async (projectId: string) => {
    setLoadingStats(true);
    try {
      const response = await api.get(`/api/projects/${projectId}/statistics`);
      setDashStats(response.data);
    } catch (err) {
      console.error('Failed to load project statistics:', err);
      setDashStats(null);
    } finally {
      setLoadingStats(false);
    }
  };

  // 엔드포인트의 취약점 로드
  const loadEndpointVulnerabilities = async (endpoint: string) => {
    if (!selectedProject) return;

    try {
      // 프로젝트의 모든 스캔에서 해당 엔드포인트의 취약점 조회
      const response = await api.get(`/api/projects/${selectedProject}`);
      const scans = response.data.scans || [];
      
      // 모든 완료된 스캔의 취약점을 수집
      const allVulns: any[] = [];
      for (const scan of scans) {
        if (scan.status === 'completed') {
          try {
            const scanResponse = await api.get(`/api/status/${scan.scan_id}`);
            const scanResult = scanResponse.data.result;
            if (scanResult && scanResult.vulnerabilities) {
              const endpointVulns = scanResult.vulnerabilities.filter(
                (v: any) => v.endpoint === endpoint
              );
              allVulns.push(...endpointVulns.map((v: any) => ({
                ...v,
                scan_id: scan.scan_id,
                scan_date: scan.created_at
              })));
            }
          } catch (err) {
            console.error(`Failed to load vulnerabilities for scan ${scan.scan_id}:`, err);
          }
        }
      }

      setSelectedEndpoint(endpoint);
      setEndpointVulnerabilities(allVulns);
      setShowEndpointVulnModal(true);
    } catch (err) {
      console.error('Failed to load endpoint vulnerabilities:', err);
      alert('취약점 정보를 불러올 수 없습니다');
    }
  };

  // 히스토리 항목 클릭 시 상세 페이지로 이동
  const loadScanDetails = (scanId: string, targetUrl: string) => {
    router.push(`/scan/${scanId}`);
  };

  // 스캔 삭제
  const deleteScan = async (scanId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // 상세보기 클릭 방지
    
    console.log('[deleteScan] Attempting to delete scan:', scanId);
    
    if (!confirm('이 스캔 기록을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      return;
    }

    try {
      setLoadingHistory(true);
      console.log('[deleteScan] Sending DELETE request to:', `/api/scan/${scanId}`);
      const response = await api.delete(`/api/scan/${scanId}`);
      console.log('[deleteScan] Delete response:', response.data);
      
      // 히스토리 목록에서 제거
      setScanHistory(prev => prev.filter(item => item.id !== scanId));
      
      // 만약 삭제된 스캔의 결과가 현재 표시중이라면 초기화
      if (result && scanHistory.find(item => item.id === scanId)) {
        setResult(null);
      }
      
      alert('스캔 기록이 삭제되었습니다');
      
      // 프로젝트 히스토리 새로고침
      if (selectedProject) {
        await loadProjectHistory(selectedProject);
      }
    } catch (err: any) {
      console.error('[deleteScan] Failed to delete scan:', err);
      console.error('[deleteScan] Error response:', err.response?.data);
      alert(`스캔 삭제 실패: ${err.response?.data?.error || err.message}`);
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
        scan_vulns: false,
        ai_enabled: false,
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex">
      {/* Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-20' : 'w-64'} bg-gray-900/90 backdrop-blur-lg border-r border-white/10 transition-all duration-300 flex flex-col flex-shrink-0`}>
        {/* Logo & Toggle */}
        <div className="p-6 border-b border-white/10">
          <div className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'}`}>
            {!sidebarCollapsed && (
              <div className="flex items-center gap-3">
                <Shield className="w-8 h-8 text-blue-400" />
                <div>
                  <h1 className="text-lg font-bold text-white">API Scanner</h1>
                  <p className="text-xs text-gray-400">v2.0</p>
                </div>
              </div>
            )}
            {sidebarCollapsed && (
              <Shield className="w-8 h-8 text-blue-400" />
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className={`p-2 hover:bg-white/10 rounded-lg transition ${sidebarCollapsed ? 'hidden' : ''}`}
            >
              <Menu className="w-5 h-5 text-gray-400" />
            </button>
          </div>
          {sidebarCollapsed && (
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="w-full mt-4 p-2 hover:bg-white/10 rounded-lg transition"
            >
              <Menu className="w-5 h-5 text-gray-400 mx-auto" />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <button
            onClick={() => setActiveTab('projects')}
            className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-lg transition group relative ${
              activeTab === 'projects' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:bg-white/10'
            }`}
            title={sidebarCollapsed ? '프로젝트' : ''}
          >
            <FolderOpen className="w-5 h-5 flex-shrink-0" />
            {!sidebarCollapsed && <span className="font-medium">프로젝트</span>}
          </button>

          <button
            onClick={() => setActiveTab('scan')}
            disabled={!selectedProject}
            className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-lg transition group relative ${
              activeTab === 'scan' 
                ? 'bg-blue-600 text-white' 
                : selectedProject
                ? 'text-gray-300 hover:bg-white/10'
                : 'text-gray-600 cursor-not-allowed'
            }`}
            title={sidebarCollapsed ? '스캔' : ''}
          >
            <Search className="w-5 h-5 flex-shrink-0" />
            {!sidebarCollapsed && <span className="font-medium">스캔</span>}
          </button>

          <button
            onClick={() => setActiveTab('dashboard')}
            disabled={!selectedProject}
            className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-lg transition group relative ${
              activeTab === 'dashboard' 
                ? 'bg-blue-600 text-white' 
                : selectedProject
                ? 'text-gray-300 hover:bg-white/10'
                : 'text-gray-600 cursor-not-allowed'
            }`}
            title={sidebarCollapsed ? '대시보드' : ''}
          >
            <BarChart3 className="w-5 h-5 flex-shrink-0" />
            {!sidebarCollapsed && <span className="font-medium">대시보드</span>}
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-lg transition group relative ${
              activeTab === 'history' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:bg-white/10'
            }`}
            title={sidebarCollapsed ? '히스토리' : ''}
          >
            <div className="relative">
              <History className="w-5 h-5 flex-shrink-0" />
              {sidebarCollapsed && scanHistory.length > 0 && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full"></span>
              )}
            </div>
            {!sidebarCollapsed && (
              <span className="flex items-center justify-between flex-1">
                <span className="font-medium">히스토리</span>
                <span className="px-2 py-0.5 bg-blue-500/30 rounded-full text-xs">{scanHistory.length}</span>
              </span>
            )}
          </button>
        </nav>

        {/* Selected Project Info */}
        {!sidebarCollapsed && selectedProject && (
          <div className="p-4 border-t border-white/10">
            <div className="text-xs text-gray-400 mb-1">현재 프로젝트</div>
            <div className="text-sm text-white font-medium truncate">
              {projects.find(p => p.project_id === selectedProject)?.name || 'Unknown'}
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto px-8 py-8">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              {activeTab === 'projects' && '프로젝트 관리'}
              {activeTab === 'scan' && '보안 스캔'}
              {activeTab === 'dashboard' && '분석 대시보드'}
              {activeTab === 'history' && '스캔 히스토리'}
            </h1>
            <p className="text-gray-400">
              {activeTab === 'projects' && '프로젝트를 생성하고 관리합니다'}
              {activeTab === 'scan' && '웹 애플리케이션의 Shadow API와 취약점을 탐지합니다'}
              {activeTab === 'dashboard' && '스캔 결과를 시각화하여 분석합니다'}
              {activeTab === 'history' && '과거 스캔 기록을 조회하고 관리합니다'}
            </p>
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
          <div className="max-w-6xl mx-auto">
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
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column - Scan Configuration */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Selected Project Info */}
                  <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/50 rounded-xl p-5 backdrop-blur-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-3 bg-blue-500/30 rounded-lg">
                          <Folder className="w-6 h-6 text-blue-300" />
                        </div>
                        <div>
                          <p className="text-sm text-blue-200">현재 프로젝트</p>
                          <p className="text-lg font-bold text-white">
                            {projects.find(p => p.project_id === selectedProject)?.name}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => setActiveTab('projects')}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm transition"
                      >
                        변경
                      </button>
                    </div>
                  </div>

                  {/* Scan Configuration Card */}
                  <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                      <Settings className="w-6 h-6 text-blue-400" />
                      스캔 설정
                    </h3>
                    
                    <div className="space-y-5">
                      {/* Target URL */}
                      <div>
                        <label className="block text-white mb-2 font-semibold text-sm flex items-center gap-2">
                          <Globe className="w-4 h-4 text-blue-400" />
                          대상 URL *
                        </label>
                        <input
                          type="text"
                          value={targetUrl}
                          onChange={(e) => setTargetUrl(e.target.value)}
                          placeholder="http://localhost:5000"
                          className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400 transition"
                        />
                      </div>

                      {/* JavaScript Path */}
                      <div>
                        <label className="block text-white mb-2 font-semibold text-sm flex items-center gap-2">
                          <FileCode className="w-4 h-4 text-purple-400" />
                          JavaScript 경로 (선택사항)
                        </label>
                        <input
                          type="text"
                          value={jsPath}
                          onChange={(e) => setJsPath(e.target.value)}
                          placeholder="비워두면 자동으로 수집합니다"
                          className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-purple-400 transition"
                        />
                      </div>

                      {/* Analysis Type */}
                      <div>
                        <label className="block text-white mb-3 font-semibold text-sm">분석 타입</label>
                        <div className="grid grid-cols-2 gap-3">
                          <button
                            onClick={() => setAnalysisType('js_only')}
                            className={`p-4 rounded-lg font-semibold transition border-2 ${
                              analysisType === 'js_only' 
                                ? 'bg-purple-500/30 border-purple-500 text-white' 
                                : 'bg-white/10 border-white/20 text-gray-300 hover:bg-white/20'
                            }`}
                          >
                            <FileCode className="w-6 h-6 mx-auto mb-2" />
                            <div className="text-sm">JS 분석만</div>
                          </button>
                          <button
                            onClick={() => setAnalysisType('full_scan')}
                            className={`p-4 rounded-lg font-semibold transition border-2 ${
                              analysisType === 'full_scan' 
                                ? 'bg-blue-500/30 border-blue-500 text-white' 
                                : 'bg-white/10 border-white/20 text-gray-300 hover:bg-white/20'
                            }`}
                          >
                            <Search className="w-6 h-6 mx-auto mb-2" />
                            <div className="text-sm">전체 스캔</div>
                          </button>
                        </div>
                      </div>

                      {/* Options */}
                      {analysisType === 'full_scan' && (
                        <div className="space-y-3 bg-blue-500/10 rounded-lg p-4 border border-blue-500/30">
                          <div className="text-sm font-semibold text-blue-300 mb-3">스캔 옵션</div>

                          <label className="flex items-center gap-3 p-3 bg-white/10 rounded-lg hover:bg-white/20 transition cursor-pointer">
                            <input
                              type="checkbox"
                              id="bruteforceEnabled"
                              checked={bruteforceEnabled}
                              onChange={(e) => setBruteforceEnabled(e.target.checked)}
                              className="w-5 h-5 rounded accent-green-500"
                            />
                            <div className="flex-1">
                              <div className="text-white font-semibold">🔍 디렉토리 브루트포싱</div>
                              <div className="text-xs text-gray-400">숨겨진 경로와 JS 파일을 탐색합니다</div>
                            </div>
                          </label>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Start Button */}
                  <button
                    onClick={startScan}
                    disabled={scanning || !selectedProject || !targetUrl}
                    className="w-full py-5 px-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold rounded-xl transition text-lg shadow-lg flex items-center justify-center gap-3"
                  >
                    {scanning ? (
                      <>
                        <Loader2 className="w-6 h-6 animate-spin" />
                        <span>스캔 진행 중...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-6 h-6" />
                        <span>스캔 시작</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Right Column - Info & Progress */}
                <div className="space-y-6">
                  {/* Quick Info Card */}
                  <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-lg rounded-xl p-6 border border-purple-500/30">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      <Info className="w-5 h-5 text-purple-400" />
                      스캔 안내
                    </h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex items-start gap-2">
                        <div className="w-6 h-6 rounded-full bg-blue-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-blue-300 font-bold text-xs">1</span>
                        </div>
                        <div>
                          <div className="text-white font-semibold">대상 URL 입력</div>
                          <div className="text-gray-400 text-xs mt-0.5">스캔할 웹 애플리케이션의 URL</div>
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-6 h-6 rounded-full bg-purple-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-purple-300 font-bold text-xs">2</span>
                        </div>
                        <div>
                          <div className="text-white font-semibold">분석 타입 선택</div>
                          <div className="text-gray-400 text-xs mt-0.5">JS만 또는 전체 스캔 선택</div>
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-6 h-6 rounded-full bg-pink-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-pink-300 font-bold text-xs">3</span>
                        </div>
                        <div>
                          <div className="text-white font-semibold">옵션 설정</div>
                          <div className="text-gray-400 text-xs mt-0.5">필요한 기능을 활성화</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Progress Card */}
                  {scanning && (
                    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 animate-pulse-subtle">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                          <Activity className="w-5 h-5 text-blue-400" />
                          진행 상황
                        </h3>
                        <span className="text-2xl font-bold text-blue-400">{progress}%</span>
                      </div>
                      
                      <div className="mb-4">
                        <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500 ease-out"
                            style={{ width: `${progress}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="text-sm text-gray-300 mb-4 flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-ping"></div>
                        {statusMessage}
                      </div>

                      {scanId && (
                        <div className="text-xs text-gray-500 mb-4 font-mono bg-black/30 p-2 rounded">
                          ID: {scanId}
                        </div>
                      )}

                      <button
                        onClick={stopScan}
                        className="w-full px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition"
                      >
                        <StopCircle className="w-5 h-5" />
                        스캔 중지
                      </button>
                    </div>
                  )}

                  {/* Error Card */}
                  {error && (
                    <div className="bg-red-500/20 backdrop-blur-lg border border-red-500 rounded-xl p-6">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0" />
                        <div>
                          <div className="text-red-300 font-semibold mb-1">오류 발생</div>
                          <div className="text-red-200 text-sm">{error}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Features Info */}
                  {!scanning && !error && (
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                      <h4 className="text-sm font-bold text-white mb-3">주요 기능</h4>
                      <div className="space-y-2 text-xs text-gray-400">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span>Shadow API 자동 탐지</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span>취약점 자동 스캔</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span>AI 기반 PoC 생성</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span>상세 리포트 제공</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            
            {/* Logs Panel */}
            {showLogs && logs.length > 0 && (
              <div className="bg-black/40 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-green-400" />
                    실시간 로그
                  </h3>
                  <button
                    onClick={() => setShowLogs(false)}
                    className="text-gray-400 hover:text-white transition"
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
                        {scanId && (
                          <button
                            onClick={() => router.push(`/scan/${scanId}`)}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg flex items-center gap-2"
                          >
                            <ChevronRight className="w-4 h-4" />
                            상세 보기
                          </button>
                        )}
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
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                            {result.discovered_paths.map((pathData: any, index: number) => (
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
          </div>
        )}

        {/* 대시보드 탭 */}
        {activeTab === 'dashboard' && selectedProject && (
          <div className="max-w-7xl mx-auto">
            {loadingStats ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-12 h-12 animate-spin text-blue-400" />
              </div>
            ) : !dashStats ? (
              <div className="text-center py-20">
                <BarChart3 className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">통계 데이터를 불러올 수 없습니다</p>
              </div>
            ) : (
              <>
                {(() => {
                  const { overview, vulnerabilities, endpoints, timeline, recent_activity } = dashStats;
                  return (
                <div className="space-y-6">
                  {/* 프로젝트 헤더 */}
                  <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-3xl font-bold text-white mb-2">
                          {projects.find(p => p.project_id === selectedProject)?.name}
                        </h2>
                        <p className="text-gray-300">
                          {projects.find(p => p.project_id === selectedProject)?.description || '프로젝트 통합 대시보드'}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">마지막 스캔</div>
                        <div className="text-white font-semibold">
                          {recent_activity.last_scan 
                            ? new Date(recent_activity.last_scan).toLocaleString()
                            : '없음'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 주요 통계 카드 */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                      <div className="flex items-center justify-between mb-2">
                        <Activity className="w-8 h-8 text-blue-400" />
                        <div className="text-3xl font-bold text-white">{overview.total_scans}</div>
                      </div>
                      <div className="text-gray-300 text-sm">총 스캔 수</div>
                      <div className="mt-2 flex items-center gap-2 text-xs">
                        <span className="text-green-400">✓ {overview.completed_scans}</span>
                        <span className="text-red-400">✗ {overview.failed_scans}</span>
                      </div>
                    </div>

                    <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                      <div className="flex items-center justify-between mb-2">
                        <Target className="w-8 h-8 text-green-400" />
                        <div className="text-3xl font-bold text-white">{overview.total_endpoints}</div>
                      </div>
                      <div className="text-gray-300 text-sm">총 엔드포인트</div>
                      <div className="mt-2 text-xs">
                        <span className="text-red-400">Shadow: {overview.shadow_apis}</span>
                        <span className="text-gray-400 mx-1">|</span>
                        <span className="text-green-400">Public: {overview.public_apis}</span>
                      </div>
                    </div>

                    <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                      <div className="flex items-center justify-between mb-2">
                        <AlertTriangle className="w-8 h-8 text-orange-400" />
                        <div className="text-3xl font-bold text-white">{overview.total_vulnerabilities}</div>
                      </div>
                      <div className="text-gray-300 text-sm">총 취약점</div>
                      <div className="mt-2 flex items-center gap-1 text-xs">
                        {vulnerabilities.by_severity.critical > 0 && (
                          <span className="px-2 py-0.5 bg-red-500/20 text-red-300 rounded">
                            C: {vulnerabilities.by_severity.critical}
                          </span>
                        )}
                        {vulnerabilities.by_severity.high > 0 && (
                          <span className="px-2 py-0.5 bg-orange-500/20 text-orange-300 rounded">
                            H: {vulnerabilities.by_severity.high}
                          </span>
                        )}
                        {vulnerabilities.by_severity.medium > 0 && (
                          <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded">
                            M: {vulnerabilities.by_severity.medium}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                      <div className="flex items-center justify-between mb-2">
                        <TrendingUp className="w-8 h-8 text-purple-400" />
                        <div className="text-3xl font-bold text-white">{overview.success_rate}%</div>
                      </div>
                      <div className="text-gray-300 text-sm">성공률</div>
                      <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${overview.success_rate}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* 차트 그리드 */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* 취약점 심각도 분포 */}
                    <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <PieChart className="w-5 h-5 text-orange-400" />
                        취약점 심각도 분포
                      </h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Critical', value: vulnerabilities.by_severity.critical, color: '#ef4444' },
                              { name: 'High', value: vulnerabilities.by_severity.high, color: '#f97316' },
                              { name: 'Medium', value: vulnerabilities.by_severity.medium, color: '#eab308' },
                              { name: 'Low', value: vulnerabilities.by_severity.low, color: '#3b82f6' },
                              { name: 'Info', value: vulnerabilities.by_severity.info, color: '#6b7280' }
                            ].filter(d => d.value > 0)}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={(entry: any) => `${entry.name}: ${entry.value}`}
                            outerRadius={100}
                            dataKey="value"
                          >
                            {[
                              { name: 'Critical', value: vulnerabilities.by_severity.critical, color: '#ef4444' },
                              { name: 'High', value: vulnerabilities.by_severity.high, color: '#f97316' },
                              { name: 'Medium', value: vulnerabilities.by_severity.medium, color: '#eab308' },
                              { name: 'Low', value: vulnerabilities.by_severity.low, color: '#3b82f6' },
                              { name: 'Info', value: vulnerabilities.by_severity.info, color: '#6b7280' }
                            ].filter(d => d.value > 0).map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>

                    {/* HTTP 메서드 분포 */}
                    <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-blue-400" />
                        HTTP 메서드 분포
                      </h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={Object.entries(endpoints.by_method).map(([name, count]) => ({ name, count }))}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis dataKey="name" stroke="#9ca3af" />
                          <YAxis stroke="#9ca3af" />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                            cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
                          />
                          <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* 취약점 타입 분포 */}
                    {Object.keys(vulnerabilities.by_type).length > 0 && (
                      <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                          <Shield className="w-5 h-5 text-red-400" />
                          취약점 타입별 분포
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart 
                            data={Object.entries(vulnerabilities.by_type)
                              .map(([name, count]) => ({ name, count }))
                              .sort((a, b) => (b.count as number) - (a.count as number))
                              .slice(0, 8)
                            }
                            layout="vertical"
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis type="number" stroke="#9ca3af" />
                            <YAxis dataKey="name" type="category" stroke="#9ca3af" width={150} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                            />
                            <Bar dataKey="count" fill="#f97316" radius={[0, 8, 8, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {/* 스캔 타임라인 */}
                    {timeline.length > 0 && (
                      <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                          <Clock className="w-5 h-5 text-green-400" />
                          스캔 활동 타임라인 (30일)
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={timeline}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis 
                              dataKey="date" 
                              stroke="#9ca3af"
                              tickFormatter={(value) => {
                                const date = new Date(value);
                                return `${date.getMonth() + 1}/${date.getDate()}`;
                              }}
                            />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip 
                              contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                              labelFormatter={(value) => new Date(value).toLocaleDateString()}
                            />
                            <Legend />
                            <Bar dataKey="scans" name="스캔" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                            <Bar dataKey="endpoints" name="엔드포인트" fill="#10b981" radius={[8, 8, 0, 0]} />
                            <Bar dataKey="vulnerabilities" name="취약점" fill="#f97316" radius={[8, 8, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>

                  {/* 상위 취약 엔드포인트 */}
                  {vulnerabilities.top_vulnerable_endpoints.length > 0 && (
                    <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/10">
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        상위 취약 엔드포인트 (Top 10)
                      </h3>
                      <p className="text-gray-400 text-sm mb-4">클릭하여 해당 엔드포인트의 취약점 상세 정보를 확인하세요</p>
                      <div className="space-y-2">
                        {vulnerabilities.top_vulnerable_endpoints.map((item: any, index: number) => (
                          <div 
                            key={index}
                            onClick={() => loadEndpointVulnerabilities(item.endpoint)}
                            className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition cursor-pointer group"
                          >
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <div className="flex-shrink-0 w-6 h-6 bg-red-500/20 text-red-300 rounded-full flex items-center justify-center text-xs font-bold">
                                {index + 1}
                              </div>
                              <code className="text-gray-300 text-sm truncate group-hover:text-white">{item.endpoint}</code>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex-shrink-0 px-3 py-1 bg-red-500/20 text-red-300 rounded-full text-sm font-semibold">
                                {item.count} 취약점
                              </div>
                              <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-white" />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* API 타입 분포 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-red-500/20 to-red-600/20 backdrop-blur-lg rounded-lg p-6 border border-red-500/30">
                      <div className="flex items-center justify-between mb-3">
                        <Eye className="w-8 h-8 text-red-400" />
                        <div className="text-3xl font-bold text-white">{overview.shadow_apis}</div>
                      </div>
                      <div className="text-gray-200 font-semibold mb-1">Shadow APIs</div>
                      <div className="text-red-200 text-sm">
                        문서화되지 않은 숨겨진 API
                      </div>
                      <div className="mt-3 text-xs text-red-300">
                        전체의 {endpoints.shadow_ratio}%
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-green-500/20 to-green-600/20 backdrop-blur-lg rounded-lg p-6 border border-green-500/30">
                      <div className="flex items-center justify-between mb-3">
                        <FileText className="w-8 h-8 text-green-400" />
                        <div className="text-3xl font-bold text-white">{overview.public_apis}</div>
                      </div>
                      <div className="text-gray-200 font-semibold mb-1">Public APIs</div>
                      <div className="text-green-200 text-sm">
                        공개 문서화된 API
                      </div>
                      <div className="mt-3 text-xs text-green-300">
                        전체의 {100 - endpoints.shadow_ratio}%
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-lg rounded-lg p-6 border border-purple-500/30">
                      <div className="flex items-center justify-between mb-3">
                        <Calendar className="w-8 h-8 text-purple-400" />
                        <div className="text-3xl font-bold text-white">{recent_activity.scans_last_30_days}</div>
                      </div>
                      <div className="text-gray-200 font-semibold mb-1">최근 활동</div>
                      <div className="text-purple-200 text-sm">
                        지난 30일간 스캔 수
                      </div>
                      <div className="mt-3 text-xs text-purple-300">
                        {recent_activity.scans_last_30_days > 0 
                          ? `평균 ${(recent_activity.scans_last_30_days / 30).toFixed(1)}회/일`
                          : '활동 없음'}
                      </div>
                    </div>
                  </div>
                </div>
                  );
                })()}
              </>
            )}
          </div>
        )}

        {/* 대시보드 - 프로젝트 미선택 */}
        {activeTab === 'dashboard' && !selectedProject && (
          <div className="max-w-6xl mx-auto">
            <div className="text-center py-20">
              <BarChart3 className="w-20 h-20 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400 text-xl mb-2">프로젝트를 선택해주세요</p>
              <p className="text-gray-500 mb-6">
                프로젝트 관리 탭에서 프로젝트를 선택하면 종합 대시보드를 볼 수 있습니다
              </p>
              <button
                onClick={() => setActiveTab('projects')}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
              >
                프로젝트 선택하기
              </button>
            </div>
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
                  {scanHistory.map((item: any, index: number) => {
                    const isCompleted = item.status === 'completed';
                    return (
                      <div 
                        key={index} 
                        className={`bg-white/10 rounded-lg p-6 transition relative group ${
                          isCompleted ? 'hover:bg-white/20' : 'opacity-60'
                        }`}
                      >
                        {/* 삭제 버튼 */}
                        <button
                          onClick={(e) => deleteScan(item.id, e)}
                          className="absolute top-4 right-4 p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity z-10"
                          title="스캔 삭제"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>

                        {/* 클릭 가능한 영역 */}
                        <div 
                          className={isCompleted ? 'cursor-pointer' : 'cursor-not-allowed'}
                          onClick={() => isCompleted && loadScanDetails(item.id, item.target)}
                        >
                        <div className="flex items-center justify-between mb-3 pr-12">
                          <div className="flex items-center gap-3">
                            <Clock className="w-5 h-5 text-blue-400" />
                            <span className="text-white font-semibold">{item.target}</span>
                            {item.status === 'completed' && (
                              <span className="px-2 py-1 bg-green-500/20 text-green-300 text-xs rounded-full">완료</span>
                            )}
                            {item.status === 'running' && (
                              <span className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-full">진행중</span>
                            )}
                            {item.status === 'failed' && (
                              <span className="px-2 py-1 bg-red-500/20 text-red-300 text-xs rounded-full">실패</span>
                            )}
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
                        {isCompleted ? (
                          <div className="mt-3 text-blue-400 text-sm flex items-center gap-1">
                            <span>클릭하여 상세 보기</span>
                            <ChevronRight className="w-4 h-4" />
                          </div>
                        ) : (
                          <div className="mt-3 text-gray-500 text-sm">
                            {item.status === 'running' ? '스캔이 진행중입니다...' : '스캔이 완료되지 않았습니다'}
                          </div>
                        )}
                      </div>
                    </div>
                    );
                  })}
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

        {/* 엔드포인트 취약점 모달 */}
        {showEndpointVulnModal && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                      <AlertTriangle className="w-6 h-6 text-yellow-400" />
                      엔드포인트 취약점 상세
                    </h3>
                    <code className="text-gray-400 text-sm mt-2 block">{selectedEndpoint}</code>
                  </div>
                  <button
                    onClick={() => {
                      setShowEndpointVulnModal(false);
                      setSelectedEndpoint(null);
                      setEndpointVulnerabilities([]);
                    }}
                    className="text-gray-400 hover:text-white"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                {endpointVulnerabilities.length === 0 ? (
                  <div className="text-center py-12">
                    <AlertTriangle className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400">이 엔드포인트에 대한 취약점이 없습니다</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <p className="text-gray-300">
                        총 <span className="text-white font-bold">{endpointVulnerabilities.length}개</span>의 취약점이 발견되었습니다
                      </p>
                    </div>

                    {endpointVulnerabilities.map((vuln: any, index: number) => (
                      <div
                        key={index}
                        className={`rounded-lg border-l-4 p-5 ${
                          vuln.level === 'critical' ? 'bg-red-500/20 border-red-500' :
                          vuln.level === 'high' ? 'bg-orange-500/20 border-orange-500' :
                          vuln.level === 'medium' ? 'bg-yellow-500/20 border-yellow-500' :
                          'bg-blue-500/20 border-blue-500'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h4 className="font-bold text-white text-lg">{vuln.type}</h4>
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
                            <div className="flex items-center gap-4 text-xs text-gray-400">
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(vuln.scan_date).toLocaleString()}
                              </span>
                              <code className="px-2 py-1 bg-black/30 rounded">{vuln.method}</code>
                            </div>
                          </div>
                        </div>

                        {vuln.recommendation && (
                          <div className="mt-3 p-3 bg-black/30 rounded">
                            <p className="text-white font-semibold text-sm mb-1">💡 권장사항:</p>
                            <p className="text-gray-300 text-sm">{vuln.recommendation}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
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
    </div>
  );
}
