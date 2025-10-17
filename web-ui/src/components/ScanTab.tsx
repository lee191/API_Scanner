import React from 'react';
import {
  Settings, Activity, Info, Globe, FileCode, Search, Play, Loader2, StopCircle,
  AlertTriangle, CheckCircle, Folder, Zap, Brain, Rocket, HelpCircle, Terminal, ChevronUp, ChevronDown
} from 'lucide-react';

interface ScanTabProps {
  selectedProject: string | null;
  projects: any[];
  setActiveTab: (tab: 'scan' | 'dashboard' | 'history' | 'projects') => void;
  targetUrl: string;
  setTargetUrl: (url: string) => void;
  jsPath: string;
  setJsPath: (path: string) => void;
  analysisType: 'js_only' | 'full_scan';
  setAnalysisType: (type: 'js_only' | 'full_scan') => void;
  analysisMode: 'static' | 'ai' | 'both';
  setAnalysisMode: (mode: 'static' | 'ai' | 'both') => void;
  bruteforceEnabled: boolean;
  setBruteforceEnabled: (enabled: boolean) => void;
  crawlDepth: number;
  setCrawlDepth: (depth: number) => void;
  maxPages: number;
  setMaxPages: (pages: number) => void;
  scanning: boolean;
  startScan: () => void;
  stopScan: () => void;
  progress: number;
  statusMessage: string;
  scanId: string | null;
  error: string | null;
  scanSubTab: 'settings' | 'progress' | 'help' | 'summary';
  setScanSubTab: (tab: 'settings' | 'progress' | 'help' | 'summary') => void;
  result: any;
  logs: string[];
  showLogs: boolean;
  setShowLogs: (show: boolean) => void;
}

export default function ScanTab({
  selectedProject,
  projects,
  setActiveTab,
  targetUrl,
  setTargetUrl,
  jsPath,
  setJsPath,
  analysisType,
  setAnalysisType,
  analysisMode,
  setAnalysisMode,
  bruteforceEnabled,
  setBruteforceEnabled,
  crawlDepth,
  setCrawlDepth,
  maxPages,
  setMaxPages,
  scanning,
  startScan,
  stopScan,
  progress,
  statusMessage,
  scanId,
  error,
  scanSubTab,
  setScanSubTab,
  result,
  logs,
  showLogs,
  setShowLogs
}: ScanTabProps) {
  const [urlValidation, setUrlValidation] = React.useState<{ valid: boolean; message: string } | null>(null);

  // URL validation
  React.useEffect(() => {
    if (!targetUrl) {
      setUrlValidation(null);
      return;
    }

    try {
      const url = new URL(targetUrl);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        setUrlValidation({ valid: false, message: 'HTTP 또는 HTTPS 프로토콜을 사용해야 합니다' });
      } else {
        setUrlValidation({ valid: true, message: '✓ 유효한 URL' });
      }
    } catch {
      setUrlValidation({ valid: false, message: '올바른 URL 형식이 아닙니다' });
    }
  }, [targetUrl]);

  if (!selectedProject) {
    return (
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
    );
  }

  const currentConfig = {
    type: analysisType === 'js_only' ? 'JS 분석만' : '전체 스캔',
    mode: analysisType === 'full_scan' ? (
      analysisMode === 'static' ? '정적 분석' :
      analysisMode === 'ai' ? 'AI 분석' : '정적 + AI'
    ) : '-',
    bruteforce: analysisType === 'full_scan' && bruteforceEnabled ? '활성화' : '비활성화'
  };

  // 현재 프로젝트 정보 가져오기
  const currentProject = projects.find(p => p.project_id === selectedProject);
  const projectName = currentProject?.name || selectedProject;

  return (
    <div className="space-y-6">
      {/* Header with Project Info */}
      <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/50 rounded-xl p-5 backdrop-blur-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/30 rounded-lg">
              <Folder className="w-6 h-6 text-blue-300" />
            </div>
            <div>
              <p className="text-sm text-blue-200">현재 프로젝트</p>
              <p className="text-xl font-bold text-white">{projectName}</p>
            </div>
          </div>
          <button
            onClick={() => setActiveTab('projects')}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition"
          >
            프로젝트 변경
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
        <div className="flex border-b border-white/10">
          <button
            onClick={() => setScanSubTab('settings')}
            className={`flex-1 px-6 py-4 font-semibold transition flex items-center justify-center gap-2 ${
              scanSubTab === 'settings'
                ? 'bg-blue-500/30 text-white border-b-2 border-blue-500'
                : 'text-gray-300 hover:bg-white/10'
            }`}
          >
            <Settings className="w-5 h-5" />
            스캔 설정
          </button>
          <button
            onClick={() => setScanSubTab('progress')}
            className={`flex-1 px-6 py-4 font-semibold transition flex items-center justify-center gap-2 ${
              scanSubTab === 'progress'
                ? 'bg-blue-500/30 text-white border-b-2 border-blue-500'
                : 'text-gray-300 hover:bg-white/10'
            }`}
          >
            <Activity className="w-5 h-5" />
            진행 상황
          </button>
          <button
            onClick={() => setScanSubTab('summary')}
            className={`flex-1 px-6 py-4 font-semibold transition flex items-center justify-center gap-2 ${
              scanSubTab === 'summary'
                ? 'bg-blue-500/30 text-white border-b-2 border-blue-500'
                : 'text-gray-300 hover:bg-white/10'
            }`}
            disabled={!result}
          >
            <CheckCircle className="w-5 h-5" />
            결과 요약
          </button>
          <button
            onClick={() => setScanSubTab('help')}
            className={`flex-1 px-6 py-4 font-semibold transition flex items-center justify-center gap-2 ${
              scanSubTab === 'help'
                ? 'bg-blue-500/30 text-white border-b-2 border-blue-500'
                : 'text-gray-300 hover:bg-white/10'
            }`}
          >
            <HelpCircle className="w-5 h-5" />
            도움말
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Configuration Tab */}
          {scanSubTab === 'settings' && (
            <div className="space-y-6">
              {/* Scan Button - Top */}
              <div className="pb-2 border-b border-white/10">
                {!scanning ? (
                  <button
                    onClick={startScan}
                    disabled={!targetUrl || (urlValidation ? !urlValidation.valid : false)}
                    className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
                  >
                    <Play className="w-6 h-6" />
                    스캔 시작
                  </button>
                ) : (
                  <button
                    onClick={stopScan}
                    className="w-full py-4 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition flex items-center justify-center gap-3"
                  >
                    <StopCircle className="w-6 h-6" />
                    스캔 중지
                  </button>
                )}
              </div>

              {/* Target URL */}
              <div>
                <label className="block text-white font-semibold mb-3 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-400" />
                  대상 URL
                </label>
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="w-full bg-white/10 text-white px-4 py-3 rounded-lg border border-white/20 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50"
                  disabled={scanning}
                />
                {urlValidation && (
                  <p className={`mt-2 text-sm flex items-center gap-2 ${
                    urlValidation.valid ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {urlValidation.valid ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                    {urlValidation.message}
                  </p>
                )}
              </div>

              {/* JS Path */}
              <div>
                <label className="block text-white font-semibold mb-3 flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-purple-400" />
                  JS 경로 (선택사항)
                </label>
                <input
                  type="text"
                  value={jsPath}
                  onChange={(e) => setJsPath(e.target.value)}
                  placeholder="/static/js, /assets"
                  className="w-full bg-white/10 text-white px-4 py-3 rounded-lg border border-white/20 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50"
                  disabled={scanning}
                />
                <p className="mt-2 text-sm text-gray-400">
                  쉼표로 구분하여 여러 경로 입력 가능
                </p>
              </div>

              {/* Analysis Type */}
              <div>
                <label className="block text-white font-semibold mb-3">분석 타입</label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setAnalysisType('js_only')}
                    disabled={scanning}
                    className={`p-5 rounded-xl font-semibold transition border-2 ${
                      analysisType === 'js_only'
                        ? 'bg-purple-500/30 border-purple-500 text-white shadow-lg shadow-purple-500/20'
                        : 'bg-white/5 border-white/20 text-gray-300 hover:bg-white/10 hover:border-white/40'
                    } ${scanning ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <FileCode className="w-8 h-8 mx-auto mb-3" />
                    <div className="text-base mb-1">JS 분석만</div>
                    <div className="text-xs opacity-75">빠른 분석</div>
                  </button>
                  <button
                    onClick={() => setAnalysisType('full_scan')}
                    disabled={scanning}
                    className={`p-5 rounded-xl font-semibold transition border-2 ${
                      analysisType === 'full_scan'
                        ? 'bg-blue-500/30 border-blue-500 text-white shadow-lg shadow-blue-500/20'
                        : 'bg-white/5 border-white/20 text-gray-300 hover:bg-white/10 hover:border-white/40'
                    } ${scanning ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <Search className="w-8 h-8 mx-auto mb-3" />
                    <div className="text-base mb-1">전체 스캔</div>
                    <div className="text-xs opacity-75">상세 분석</div>
                  </button>
                </div>
              </div>

              {/* Analysis Mode */}
              {analysisType === 'full_scan' && (
                <div>
                  <label className="block text-white font-semibold mb-3 flex items-center gap-2">
                    <Brain className="w-5 h-5 text-pink-400" />
                    분석 모드
                  </label>
                  <div className="space-y-3">
                    {[
                      { value: 'static', icon: Zap, label: '⚡ 정적 분석만', desc: 'JavaScript 파일 정적 분석 (빠름)', color: 'blue' },
                      { value: 'ai', icon: Brain, label: '🤖 AI 분석만', desc: 'GPT-4o로 숨겨진 엔드포인트 추론', color: 'purple' },
                      { value: 'both', icon: Rocket, label: '🚀 정적 + AI 분석', desc: '정적 분석과 AI 추론 결합 (권장)', color: 'green' }
                    ].map((mode) => (
                      <label
                        key={mode.value}
                        className={`flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition ${
                          analysisMode === mode.value
                            ? `bg-${mode.color}-500/20 border-${mode.color}-500`
                            : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                        } ${scanning ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        <input
                          type="radio"
                          name="analysisMode"
                          value={mode.value}
                          checked={analysisMode === mode.value}
                          onChange={() => setAnalysisMode(mode.value as any)}
                          disabled={scanning}
                          className="w-5 h-5 accent-blue-500"
                        />
                        <div className="flex-1">
                          <div className="text-white font-semibold mb-1">{mode.label}</div>
                          <div className="text-xs text-gray-400">{mode.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>

                  {/* Crawl Depth Settings */}
                  <div className="mt-5 pt-5 border-t border-white/10">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      {/* Crawl Depth */}
                      <div>
                        <label className="block text-white font-semibold mb-3 text-sm">
                          🕸️ 크롤링 깊이
                        </label>
                        <select
                          value={crawlDepth}
                          onChange={(e) => setCrawlDepth(Number(e.target.value))}
                          disabled={scanning}
                          className="w-full bg-white/10 text-white px-4 py-3 rounded-lg border border-white/20 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50"
                        >
                          <option value="1" className="bg-gray-800">1단계 (현재 페이지만)</option>
                          <option value="2" className="bg-gray-800">2단계 (링크 1단계)</option>
                          <option value="3" className="bg-gray-800">3단계 (링크 2단계)</option>
                          <option value="4" className="bg-gray-800">4단계 (깊이 탐색)</option>
                          <option value="5" className="bg-gray-800">5단계 (매우 깊음)</option>
                        </select>
                        <p className="mt-2 text-xs text-gray-400">
                          깊이가 높을수록 더 많은 페이지를 크롤링합니다
                        </p>
                      </div>

                      {/* Max Pages */}
                      <div>
                        <label className="block text-white font-semibold mb-3 text-sm">
                          📄 최대 페이지 수
                        </label>
                        <select
                          value={maxPages}
                          onChange={(e) => setMaxPages(Number(e.target.value))}
                          disabled={scanning}
                          className="w-full bg-white/10 text-white px-4 py-3 rounded-lg border border-white/20 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50"
                        >
                          <option value="10" className="bg-gray-800">10 페이지</option>
                          <option value="25" className="bg-gray-800">25 페이지</option>
                          <option value="50" className="bg-gray-800">50 페이지 (권장)</option>
                          <option value="100" className="bg-gray-800">100 페이지</option>
                          <option value="200" className="bg-gray-800">200 페이지</option>
                        </select>
                        <p className="mt-2 text-xs text-gray-400">
                          크롤링할 최대 페이지 수 (무한 크롤링 방지)
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Bruteforce Option */}
                  <div className="mt-5 pt-5 border-t border-white/10">
                    <label className={`flex items-center gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition cursor-pointer ${
                      scanning ? 'opacity-50 cursor-not-allowed' : ''
                    }`}>
                      <input
                        type="checkbox"
                        checked={bruteforceEnabled}
                        onChange={(e) => setBruteforceEnabled(e.target.checked)}
                        disabled={scanning}
                        className="w-5 h-5 rounded accent-green-500"
                      />
                      <div className="flex-1">
                        <div className="text-white font-semibold mb-1">🔍 디렉토리 브루트포싱</div>
                        <div className="text-xs text-gray-400">숨겨진 경로와 JS 파일을 탐색합니다</div>
                      </div>
                    </label>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Status Tab */}
          {scanSubTab === 'progress' && (
            <div className="space-y-6">
              {/* Current Status */}
              <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-white/10">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  현재 상태
                </h3>
                
                {scanning ? (
                  <div className="space-y-4">
                    {/* Progress Steps */}
                    <div className="space-y-3">
                      {/* Step 1: JavaScript 수집 */}
                      <div className={`flex items-center gap-3 p-4 rounded-lg transition-all ${
                        statusMessage.includes('JavaScript') || statusMessage.includes('수집') || progress >= 10
                          ? 'bg-blue-500/20 border-2 border-blue-500'
                          : 'bg-white/5 border-2 border-white/10'
                      }`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          statusMessage.includes('JavaScript') || statusMessage.includes('수집') || progress >= 10
                            ? 'bg-blue-500 text-white'
                            : 'bg-white/10 text-gray-400'
                        }`}>
                          {progress >= 30 ? '✓' : '1'}
                        </div>
                        <div className="flex-1">
                          <p className="text-white font-semibold">JavaScript 파일 수집</p>
                          <p className="text-sm text-gray-400">웹페이지 크롤링 및 JS 파일 추출</p>
                        </div>
                        {(statusMessage.includes('JavaScript') || statusMessage.includes('수집')) && progress < 30 && (
                          <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                        )}
                      </div>

                      {/* Step 2: 엔드포인트 분석 */}
                      <div className={`flex items-center gap-3 p-4 rounded-lg transition-all ${
                        (statusMessage.includes('분석') || statusMessage.includes('엔드포인트')) && progress >= 30
                          ? 'bg-green-500/20 border-2 border-green-500'
                          : progress >= 30
                          ? 'bg-white/5 border-2 border-white/10'
                          : 'bg-white/5 border-2 border-transparent'
                      }`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          (statusMessage.includes('분석') || statusMessage.includes('엔드포인트')) && progress >= 30
                            ? 'bg-green-500 text-white'
                            : progress >= 30
                            ? 'bg-white/10 text-gray-400'
                            : 'bg-white/5 text-gray-600'
                        }`}>
                          {progress >= 60 ? '✓' : '2'}
                        </div>
                        <div className="flex-1">
                          <p className={`font-semibold ${progress >= 30 ? 'text-white' : 'text-gray-500'}`}>
                            엔드포인트 분석
                          </p>
                          <p className="text-sm text-gray-400">정적 분석 및 AI 기반 추론</p>
                        </div>
                        {(statusMessage.includes('분석') || statusMessage.includes('엔드포인트')) && progress >= 30 && progress < 60 && (
                          <Loader2 className="w-5 h-5 text-green-400 animate-spin" />
                        )}
                      </div>

                      {/* Step 3: 엔드포인트 검증 */}
                      <div className={`flex items-center gap-3 p-4 rounded-lg transition-all ${
                        statusMessage.includes('검증') && progress >= 60
                          ? 'bg-purple-500/20 border-2 border-purple-500'
                          : progress >= 60
                          ? 'bg-white/5 border-2 border-white/10'
                          : 'bg-white/5 border-2 border-transparent'
                      }`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          statusMessage.includes('검증') && progress >= 60
                            ? 'bg-purple-500 text-white'
                            : progress >= 60
                            ? 'bg-white/10 text-gray-400'
                            : 'bg-white/5 text-gray-600'
                        }`}>
                          {progress >= 80 ? '✓' : '3'}
                        </div>
                        <div className="flex-1">
                          <p className={`font-semibold ${progress >= 60 ? 'text-white' : 'text-gray-500'}`}>
                            엔드포인트 검증
                          </p>
                          <p className="text-sm text-gray-400">HTTP 요청으로 유효성 확인</p>
                        </div>
                        {statusMessage.includes('검증') && progress >= 60 && progress < 80 && (
                          <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
                        )}
                      </div>

                      {/* Step 4: 리포트 생성 */}
                      <div className={`flex items-center gap-3 p-4 rounded-lg transition-all ${
                        statusMessage.includes('리포트') && progress >= 80
                          ? 'bg-orange-500/20 border-2 border-orange-500'
                          : progress >= 80
                          ? 'bg-white/5 border-2 border-white/10'
                          : 'bg-white/5 border-2 border-transparent'
                      }`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          statusMessage.includes('리포트') && progress >= 80
                            ? 'bg-orange-500 text-white'
                            : progress >= 80
                            ? 'bg-white/10 text-gray-400'
                            : 'bg-white/5 text-gray-600'
                        }`}>
                          {progress >= 100 ? '✓' : '4'}
                        </div>
                        <div className="flex-1">
                          <p className={`font-semibold ${progress >= 80 ? 'text-white' : 'text-gray-500'}`}>
                            리포트 생성
                          </p>
                          <p className="text-sm text-gray-400">결과 저장 및 리포트 작성</p>
                        </div>
                        {statusMessage.includes('리포트') && progress >= 80 && progress < 100 && (
                          <Loader2 className="w-5 h-5 text-orange-400 animate-spin" />
                        )}
                      </div>
                    </div>

                    {/* Current Status Message */}
                    <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg p-4 border border-white/10">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                        <p className="text-white font-medium">{statusMessage}</p>
                        <span className="ml-auto text-blue-400 font-semibold">{progress}%</span>
                      </div>
                    </div>

                    {/* Scan ID */}
                    {scanId && (
                      <div className="bg-white/5 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">스캔 ID</p>
                        <p className="text-white font-mono text-sm">{scanId}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Activity className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg">스캔이 실행되지 않았습니다</p>
                    <p className="text-gray-500 text-sm mt-2">
                      스캔 설정 탭에서 스캔을 시작하세요
                    </p>
                  </div>
                )}
              </div>

              {/* Current Configuration */}
              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Settings className="w-5 h-5 text-purple-400" />
                  현재 구성
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-sm text-gray-400 mb-1">분석 타입</p>
                    <p className="text-white font-semibold">{currentConfig.type}</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-sm text-gray-400 mb-1">분석 모드</p>
                    <p className="text-white font-semibold">{currentConfig.mode}</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-sm text-gray-400 mb-1">브루트포싱</p>
                    <p className="text-white font-semibold">{currentConfig.bruteforce}</p>
                  </div>
                </div>
              </div>

              {/* Real-time Logs */}
              {scanning && logs.length > 0 && (
                <div className="bg-black/40 rounded-xl p-6 border border-white/10">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Terminal className="w-5 h-5 text-green-400" />
                      실시간 로그
                    </h3>
                    <button
                      onClick={() => setShowLogs(!showLogs)}
                      className="text-gray-400 hover:text-white transition"
                    >
                      {showLogs ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>
                  
                  {showLogs && (
                    <div className="bg-black/60 rounded-lg p-4 max-h-64 overflow-y-auto font-mono text-sm">
                      {logs.map((log, index) => (
                        <div key={index} className="text-green-400 mb-1">
                          {log}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Error Display */}
              {error && (
                <div className="bg-red-500/20 border border-red-500 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-red-400 font-semibold mb-1">오류 발생</p>
                      <p className="text-red-300 text-sm">{error}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Summary Tab */}
          {scanSubTab === 'summary' && (
            <div className="space-y-6">
              {result ? (
                <>
                  {/* Summary Stats - By Status Code */}
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                    <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-xl p-4 border border-blue-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-300 text-xs">총 엔드포인트</span>
                        <Globe className="w-4 h-4 text-blue-400" />
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {result.statistics?.total_endpoints || 0}
                      </div>
                    </div>
                    
                    <div className="bg-gradient-to-br from-green-500/20 to-green-600/20 rounded-xl p-4 border border-green-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-300 text-xs">2xx Success</span>
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {(() => {
                          const allEndpoints = [...(result.shadow_apis || []), ...(result.public_apis || [])];
                          return allEndpoints.filter((e: any) => e.status_code >= 200 && e.status_code < 300).length;
                        })()}
                      </div>
                    </div>
                    
                    <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl p-4 border border-cyan-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-300 text-xs">3xx Redirect</span>
                        <Globe className="w-4 h-4 text-cyan-400" />
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {(() => {
                          const allEndpoints = [...(result.shadow_apis || []), ...(result.public_apis || [])];
                          return allEndpoints.filter((e: any) => e.status_code >= 300 && e.status_code < 400).length;
                        })()}
                      </div>
                    </div>
                    
                    <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/20 rounded-xl p-4 border border-orange-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-300 text-xs">4xx Client Error</span>
                        <AlertTriangle className="w-4 h-4 text-orange-400" />
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {(() => {
                          const allEndpoints = [...(result.shadow_apis || []), ...(result.public_apis || [])];
                          return allEndpoints.filter((e: any) => e.status_code >= 400 && e.status_code < 500).length;
                        })()}
                      </div>
                    </div>
                    
                    <div className="bg-gradient-to-br from-red-500/20 to-red-600/20 rounded-xl p-4 border border-red-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-300 text-xs">5xx Server Error</span>
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {(() => {
                          const allEndpoints = [...(result.shadow_apis || []), ...(result.public_apis || [])];
                          return allEndpoints.filter((e: any) => e.status_code >= 500 && e.status_code < 600).length;
                        })()}
                      </div>
                    </div>
                  </div>

                  {/* Scan Info */}
                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <h3 className="text-lg font-bold text-white mb-4">스캔 정보</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">대상 URL:</span>
                        <div className="text-white font-mono mt-1">{targetUrl}</div>
                      </div>
                      <div>
                        <span className="text-gray-400">분석 모드:</span>
                        <div className="text-white mt-1">
                          {analysisMode === 'static' && '정적 분석만'}
                          {analysisMode === 'ai' && 'AI 분석만'}
                          {analysisMode === 'both' && '정적 + AI 분석'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-400">분석 타입:</span>
                        <div className="text-white mt-1">
                          {analysisType === 'js_only' ? 'JS 분석만' : '전체 스캔'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-400">스캔 ID:</span>
                        <div className="text-white font-mono mt-1 text-xs">{scanId}</div>
                      </div>
                    </div>
                  </div>

                  {/* Detection Methods */}
                  {result.statistics?.detection_methods && (
                    <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                      <h3 className="text-lg font-bold text-white mb-4">탐지 방법별 통계</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(result.statistics.detection_methods).map(([method, count]: [string, any]) => (
                          <div key={method} className="bg-white/5 rounded-lg p-4 text-center">
                            <div className="text-2xl font-bold text-white mb-1">{count}</div>
                            <div className="text-xs text-gray-400">{method}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Endpoints List - Grouped by Status Code */}
                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <h3 className="text-lg font-bold text-white mb-4">발견된 엔드포인트 (상태 코드별)</h3>
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {(() => {
                        // Group endpoints by status code
                        const allEndpoints = [...(result.shadow_apis || []), ...(result.public_apis || [])];
                        const grouped: Record<string, any[]> = {
                          '2xx': [],
                          '3xx': [],
                          '4xx': [],
                          '5xx': [],
                          'unknown': []
                        };

                        allEndpoints.forEach((api: any) => {
                          const status = api.status_code;
                          if (!status) {
                            grouped['unknown'].push(api);
                          } else if (status >= 200 && status < 300) {
                            grouped['2xx'].push(api);
                          } else if (status >= 300 && status < 400) {
                            grouped['3xx'].push(api);
                          } else if (status >= 400 && status < 500) {
                            grouped['4xx'].push(api);
                          } else if (status >= 500 && status < 600) {
                            grouped['5xx'].push(api);
                          } else {
                            grouped['unknown'].push(api);
                          }
                        });

                        const statusConfig = {
                          '2xx': { 
                            label: '2xx Success', 
                            color: 'green', 
                            bgClass: 'bg-green-500/10', 
                            borderClass: 'border-green-500/30',
                            badgeClass: 'bg-green-500',
                            icon: CheckCircle
                          },
                          '3xx': { 
                            label: '3xx Redirect', 
                            color: 'blue', 
                            bgClass: 'bg-blue-500/10', 
                            borderClass: 'border-blue-500/30',
                            badgeClass: 'bg-blue-500',
                            icon: Globe
                          },
                          '4xx': { 
                            label: '4xx Client Error', 
                            color: 'orange', 
                            bgClass: 'bg-orange-500/10', 
                            borderClass: 'border-orange-500/30',
                            badgeClass: 'bg-orange-500',
                            icon: AlertTriangle
                          },
                          '5xx': { 
                            label: '5xx Server Error', 
                            color: 'red', 
                            bgClass: 'bg-red-500/10', 
                            borderClass: 'border-red-500/30',
                            badgeClass: 'bg-red-500',
                            icon: AlertTriangle
                          },
                          'unknown': { 
                            label: 'Unknown Status', 
                            color: 'gray', 
                            bgClass: 'bg-gray-500/10', 
                            borderClass: 'border-gray-500/30',
                            badgeClass: 'bg-gray-500',
                            icon: HelpCircle
                          }
                        };

                        return Object.entries(grouped).map(([statusGroup, apis]) => {
                          if (apis.length === 0) return null;
                          
                          const config = statusConfig[statusGroup as keyof typeof statusConfig];
                          const Icon = config.icon;

                          return (
                            <div key={statusGroup} className="mb-4">
                              <h4 className={`text-${config.color}-400 font-semibold mb-2 flex items-center gap-2`}>
                                <Icon className="w-4 h-4" />
                                {config.label} ({apis.length})
                              </h4>
                              {apis.map((api: any, idx: number) => (
                                <div key={idx} className={`${config.bgClass} border ${config.borderClass} rounded-lg p-3 mb-2`}>
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`px-2 py-0.5 ${config.badgeClass} text-white text-xs font-semibold rounded`}>
                                      {api.method}
                                    </span>
                                    {api.status_code && (
                                      <span className="px-2 py-0.5 bg-gray-700 text-gray-300 text-xs font-mono rounded">
                                        {api.status_code}
                                      </span>
                                    )}
                                    <code className="text-white text-sm flex-1 truncate">{api.url}</code>
                                    {api.detection_method === 'ai' && (
                                      <span className="px-2 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold rounded-full flex items-center gap-1 flex-shrink-0">
                                        <Brain className="w-3 h-3" />
                                        AI
                                      </span>
                                    )}
                                  </div>
                                  {api.detection_method && (
                                    <span className="text-xs text-gray-400">
                                      탐지: {api.detection_method}
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          );
                        });
                      })()}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="flex gap-4">
                    <button
                      onClick={() => setScanSubTab('settings')}
                      className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
                    >
                      새 스캔 시작
                    </button>
                    <button
                      onClick={() => {
                        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `scan_result_${scanId}_${Date.now()}.json`;
                        a.click();
                      }}
                      className="flex-1 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition"
                    >
                      결과 다운로드 (JSON)
                    </button>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <AlertTriangle className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">스캔 결과가 없습니다</p>
                  <p className="text-gray-500 text-sm mt-2">먼저 스캔을 실행해주세요</p>
                </div>
              )}
            </div>
          )}

          {/* Help Tab */}
          {scanSubTab === 'help' && (
            <div className="space-y-6">
              {/* Analysis Types Guide */}
              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Info className="w-5 h-5 text-blue-400" />
                  분석 타입 가이드
                </h3>
                <div className="space-y-4">
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <FileCode className="w-5 h-5 text-purple-400 flex-shrink-0 mt-1" />
                      <div>
                        <h4 className="text-white font-semibold mb-2">JS 분석만</h4>
                        <p className="text-gray-300 text-sm leading-relaxed">
                          JavaScript 파일만 수집하고 분석합니다. 빠른 스캔이 필요할 때 사용하세요.
                          크롤링이나 브루트포싱 없이 지정된 경로의 JS 파일만 분석합니다.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Search className="w-5 h-5 text-blue-400 flex-shrink-0 mt-1" />
                      <div>
                        <h4 className="text-white font-semibold mb-2">전체 스캔</h4>
                        <p className="text-gray-300 text-sm leading-relaxed">
                          웹사이트 전체를 크롤링하고 JavaScript 파일을 수집한 후 상세 분석합니다.
                          정적 분석, AI 분석, 브루트포싱 옵션을 모두 사용할 수 있습니다.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Analysis Modes Guide */}
              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-pink-400" />
                  분석 모드 가이드
                </h3>
                <div className="space-y-4">
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Zap className="w-5 h-5 text-blue-400 flex-shrink-0 mt-1" />
                      <div>
                        <h4 className="text-white font-semibold mb-2">⚡ 정적 분석만</h4>
                        <p className="text-gray-300 text-sm leading-relaxed">
                          정규표현식과 패턴 매칭으로 엔드포인트를 추출합니다. 빠르지만 복잡한 패턴은 놓칠 수 있습니다.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Brain className="w-5 h-5 text-purple-400 flex-shrink-0 mt-1" />
                      <div>
                        <h4 className="text-white font-semibold mb-2">🤖 AI 분석만</h4>
                        <p className="text-gray-300 text-sm leading-relaxed">
                          GPT-4o를 사용하여 JavaScript 코드를 이해하고 숨겨진 엔드포인트를 추론합니다.
                          더 정확하지만 시간이 더 걸립니다.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Rocket className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                      <div>
                        <h4 className="text-white font-semibold mb-2">🚀 정적 + AI 분석 (권장)</h4>
                        <p className="text-gray-300 text-sm leading-relaxed">
                          정적 분석과 AI 분석을 모두 실행하여 최대한 많은 엔드포인트를 발견합니다.
                          가장 정확하지만 시간이 가장 오래 걸립니다.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Tips */}
              <div className="bg-gradient-to-br from-green-500/10 to-blue-500/10 rounded-xl p-6 border border-green-500/30">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  빠른 팁
                </h3>
                <ul className="space-y-3">
                  {[
                    '처음 스캔할 때는 "정적 + AI 분석"을 권장합니다',
                    'JS 경로를 알고 있다면 입력하여 스캔 시간을 단축하세요',
                    '브루트포싱은 숨겨진 경로를 찾을 때 유용하지만 시간이 오래 걸립니다',
                    '스캔이 완료되면 대시보드에서 결과를 확인할 수 있습니다'
                  ].map((tip, index) => (
                    <li key={index} className="flex items-start gap-3 text-gray-300 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
