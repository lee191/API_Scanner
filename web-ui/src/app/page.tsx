'use client';

import { useState } from 'react';
import { Shield, Search, FileCode, AlertTriangle, CheckCircle } from 'lucide-react';
import axios from 'axios';

export default function Home() {
  const [targetUrl, setTargetUrl] = useState('');
  const [jsPath, setJsPath] = useState('');
  const [scanVulns, setScanVulns] = useState(true);
  const [analysisType, setAnalysisType] = useState<'js_only' | 'full_scan'>('full_scan');
  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const startScan = async () => {
    if (!targetUrl) {
      setError('Please enter a target URL');
      return;
    }

    setScanning(true);
    setError(null);
    setResult(null);

    try {
      // Start scan
      const response = await axios.post('/api/scan', {
        target_url: targetUrl,
        js_path: jsPath || undefined,
        scan_vulns: scanVulns,
        analysis_type: analysisType
      });

      const { scan_id } = response.data;
      setScanId(scan_id);

      // Poll for results
      pollScanStatus(scan_id);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to start scan');
      setScanning(false);
    }
  };

  const pollScanStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/status/${id}`);
        const status = response.data;

        if (status.status === 'completed') {
          clearInterval(interval);
          setResult(status.result);
          setScanning(false);
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setError(status.message || 'Scan failed');
          setScanning(false);
        }
      } catch (err) {
        clearInterval(interval);
        setError('Failed to check scan status');
        setScanning(false);
      }
    }, 2000); // Poll every 2 seconds
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Shield className="w-12 h-12 text-blue-400" />
            <h1 className="text-4xl font-bold text-white">Shadow API Scanner</h1>
          </div>
          <p className="text-gray-300 text-lg">
            숨겨진 API와 보안 취약점을 발견합니다
          </p>
        </div>

        {/* Scan Form */}
        <div className="max-w-3xl mx-auto bg-white/10 backdrop-blur-lg rounded-lg p-8 mb-8">
          <div className="space-y-6">
            {/* Target URL */}
            <div>
              <label className="block text-white mb-2 font-semibold">
                대상 URL *
              </label>
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
              <label className="block text-white mb-2 font-semibold">
                JavaScript 경로 (선택사항)
              </label>
              <input
                type="text"
                value={jsPath}
                onChange={(e) => setJsPath(e.target.value)}
                placeholder="비워두면 자동으로 웹사이트에서 수집합니다"
                className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-400 border border-white/30 focus:outline-none focus:border-blue-400"
              />
              <p className="text-gray-400 text-sm mt-2">
                💡 JS 파일 경로를 비워두면 대상 웹사이트를 자동으로 크롤링하여 JavaScript 파일을 수집합니다.
              </p>
            </div>

            {/* Analysis Type */}
            <div>
              <label className="block text-white mb-2 font-semibold">
                분석 타입
              </label>
              <div className="flex gap-4">
                <button
                  onClick={() => setAnalysisType('js_only')}
                  className={`flex-1 py-3 px-4 rounded-lg font-semibold transition ${
                    analysisType === 'js_only'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white/20 text-gray-300 hover:bg-white/30'
                  }`}
                >
                  <FileCode className="w-5 h-5 inline mr-2" />
                  JS 분석만
                </button>
                <button
                  onClick={() => setAnalysisType('full_scan')}
                  className={`flex-1 py-3 px-4 rounded-lg font-semibold transition ${
                    analysisType === 'full_scan'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white/20 text-gray-300 hover:bg-white/30'
                  }`}
                >
                  <Search className="w-5 h-5 inline mr-2" />
                  전체 스캔
                </button>
              </div>
            </div>

            {/* Scan Vulnerabilities */}
            {analysisType === 'full_scan' && (
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="scanVulns"
                  checked={scanVulns}
                  onChange={(e) => setScanVulns(e.target.checked)}
                  className="w-5 h-5 rounded"
                />
                <label htmlFor="scanVulns" className="text-white font-semibold">
                  취약점 스캔
                </label>
              </div>
            )}

            {/* Start Button */}
            <button
              onClick={startScan}
              disabled={scanning}
              className="w-full py-4 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold rounded-lg transition text-lg"
            >
              {scanning ? (
                <>
                  <div className="inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
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

          {/* Error */}
          {error && (
            <div className="mt-6 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-200">
              <AlertTriangle className="w-5 h-5 inline mr-2" />
              {error}
            </div>
          )}
        </div>

        {/* Results */}
        {result && (
          <div className="max-w-6xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-lg p-8">
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <CheckCircle className="w-7 h-7 text-green-400" />
                스캔 결과
              </h2>

              {/* Statistics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white/10 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-white">
                    {result.statistics?.total_endpoints || 0}
                  </div>
                  <div className="text-gray-300 text-sm">엔드포인트</div>
                </div>
                <div className="bg-white/10 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-white">
                    {result.statistics?.total_vulnerabilities || 0}
                  </div>
                  <div className="text-gray-300 text-sm">취약점</div>
                </div>
                <div className="bg-red-500/20 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-red-400">
                    {result.statistics?.critical || 0}
                  </div>
                  <div className="text-red-200 text-sm">치명적</div>
                </div>
                <div className="bg-orange-500/20 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-orange-400">
                    {result.statistics?.high || 0}
                  </div>
                  <div className="text-orange-200 text-sm">높음</div>
                </div>
              </div>

              {/* Endpoints */}
              <div className="mb-8">
                <h3 className="text-xl font-bold text-white mb-4">
                  발견된 엔드포인트 ({result.endpoints?.length || 0})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {result.endpoints?.slice(0, 10).map((endpoint: any, index: number) => (
                    <div
                      key={index}
                      className="bg-white/10 rounded-lg p-4 flex items-center gap-4"
                    >
                      <span className={`px-3 py-1 rounded font-semibold text-sm ${
                        endpoint.method === 'GET' ? 'bg-blue-500' :
                        endpoint.method === 'POST' ? 'bg-green-500' :
                        endpoint.method === 'DELETE' ? 'bg-red-500' :
                        'bg-gray-500'
                      } text-white`}>
                        {endpoint.method}
                      </span>
                      <code className="flex-1 text-gray-200">{endpoint.url}</code>
                      <span className="text-gray-400 text-sm">{endpoint.source}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Vulnerabilities */}
              <div>
                <h3 className="text-xl font-bold text-white mb-4">
                  취약점 ({result.vulnerabilities?.length || 0})
                </h3>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {result.vulnerabilities?.slice(0, 10).map((vuln: any, index: number) => (
                    <div
                      key={index}
                      className={`rounded-lg p-4 border-l-4 ${
                        vuln.level === 'critical' ? 'bg-red-500/20 border-red-500' :
                        vuln.level === 'high' ? 'bg-orange-500/20 border-orange-500' :
                        vuln.level === 'medium' ? 'bg-yellow-500/20 border-yellow-500' :
                        'bg-blue-500/20 border-blue-500'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-bold text-white">{vuln.type}</h4>
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
                      <code className="text-gray-300 text-xs block mb-2">
                        {vuln.method} {vuln.endpoint}
                      </code>
                      <p className="text-gray-400 text-sm">
                        <strong>권장사항:</strong> {vuln.recommendation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
