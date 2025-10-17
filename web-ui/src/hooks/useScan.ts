import { useState, useCallback, useRef } from 'react';
import { toast } from '@/lib/toast';
import { parseErrorMessage } from '@/lib/utils';
import apiService from '@/services/api';
import type { ScanRequest, ScanResult } from '@/types';

export const useScan = () => {
  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [logs, setLogs] = useState<string[]>([]);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const shouldStopRef = useRef(false);

  // 로그 추가
  const addLog = useCallback((message: string) => {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  }, []);

  // 스캔 상태 폴링
  const pollScanStatus = useCallback(async (id: string) => {
    let attempts = 0;
    const maxAttempts = 300; // 10분 (2초 * 300)

    const checkStatus = async () => {
      if (shouldStopRef.current) {
        clearInterval(pollingRef.current!);
        return;
      }

      attempts++;

      if (attempts >= maxAttempts) {
        clearInterval(pollingRef.current!);
        setScanning(false);
        toast.error('스캔 타임아웃');
        addLog('스캔 타임아웃');
        return;
      }

      try {
        const status = await apiService.getScanStatus(id);

        setStatusMessage(status.message || '');
        setProgress(Math.min((attempts / maxAttempts) * 100, 95));

        if (status.status === 'completed') {
          clearInterval(pollingRef.current!);

          // 결과 가져오기
          const scanResult = await apiService.getScanResult(id);
          setResult(scanResult);
          setProgress(100);
          setScanning(false);
          addLog(`스캔 완료 - ${scanResult.total_endpoints}개 엔드포인트 발견`);
          toast.success('스캔이 완료되었습니다!');
        } else if (status.status === 'failed') {
          clearInterval(pollingRef.current!);
          setScanning(false);
          toast.error(status.message || '스캔 실패');
          addLog(`스캔 실패: ${status.message}`);
        } else {
          addLog(status.message || '스캔 진행 중...');
        }
      } catch (err) {
        clearInterval(pollingRef.current!);
        setScanning(false);
        const message = parseErrorMessage(err);
        toast.error(`스캔 상태 확인 실패: ${message}`);
        addLog(`에러: ${message}`);
      }
    };

    pollingRef.current = setInterval(checkStatus, 2000);
  }, [addLog]);

  // 스캔 시작
  const startScan = useCallback(async (data: ScanRequest): Promise<boolean> => {
    if (!data.project_id) {
      toast.warning('프로젝트를 선택해주세요');
      return false;
    }

    if (!data.target_url) {
      toast.warning('대상 URL을 입력해주세요');
      return false;
    }

    try {
      setScanning(true);
      setResult(null);
      setProgress(0);
      setLogs([]);
      shouldStopRef.current = false;

      addLog('스캔 시작...');
      addLog(`대상 URL: ${data.target_url}`);
      addLog(`분석 타입: ${data.analysis_type === 'js_only' ? 'JS만' : '전체 스캔'}`);
      if (data.ai_enabled) addLog('AI 분석 활성화');
      if (data.bruteforce_enabled) addLog('디렉토리 브루트포스 활성화');

      const response = await apiService.startScan(data);

      setScanId(response.scan_id);
      addLog(`스캔 ID: ${response.scan_id}`);

      // 폴링 시작
      pollScanStatus(response.scan_id);

      return true;
    } catch (err) {
      setScanning(false);
      const message = parseErrorMessage(err);
      toast.error(`스캔 시작 실패: ${message}`);
      addLog(`에러: ${message}`);
      return false;
    }
  }, [addLog, pollScanStatus]);

  // 스캔 중지
  const stopScan = useCallback(async (): Promise<boolean> => {
    if (!scanId) return false;

    try {
      shouldStopRef.current = true;
      await apiService.stopScan(scanId);

      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }

      setScanning(false);
      toast.info('스캔이 중단되었습니다');
      addLog('스캔이 중단되었습니다');
      return true;
    } catch (err) {
      const message = parseErrorMessage(err);
      toast.error(`스캔 중단 실패: ${message}`);
      addLog(`스캔 중단 실패: ${message}`);
      return false;
    }
  }, [scanId, addLog]);

  // 결과 초기화
  const clearResult = useCallback(() => {
    setResult(null);
    setProgress(0);
    setStatusMessage('');
    setLogs([]);
    setScanId(null);
  }, []);

  return {
    scanning,
    scanId,
    result,
    progress,
    statusMessage,
    logs,
    startScan,
    stopScan,
    clearResult,
    addLog
  };
};
