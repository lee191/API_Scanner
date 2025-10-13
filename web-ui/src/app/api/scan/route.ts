import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { mkdir } from 'fs/promises';
import * as fs from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { scanResults } from '@/lib/scanStore';

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { target_url, js_path, scan_vulns = true, analysis_type = 'full_scan' } = body;

    if (!target_url) {
      return NextResponse.json(
        { error: 'target_url is required' },
        { status: 400 }
      );
    }

    // Generate scan ID
    const scanId = uuidv4();

    // Initialize scan status
    scanResults.set(scanId, {
      scan_id: scanId,
      status: 'pending',
      progress: 0,
      message: 'Scan queued'
    });

    // Execute scan asynchronously
    executeScan(scanId, target_url, js_path, scan_vulns, analysis_type);

    return NextResponse.json({
      scan_id: scanId,
      status: 'pending',
      message: 'Scan started successfully'
    });

  } catch (error) {
    console.error('Scan error:', error);
    return NextResponse.json(
      { error: 'Failed to start scan', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

async function executeScan(
  scanId: string,
  targetUrl: string,
  jsPath: string | undefined,
  scanVulns: boolean,
  analysisType: string
) {
  try {
    // Update status to running
    scanResults.set(scanId, {
      scan_id: scanId,
      status: 'running',
      progress: 10,
      message: 'Starting scan...'
    });

    // Get project root directory (go up from web-ui/src/app/api/scan)
    const projectRoot = path.resolve(process.cwd(), '..');
    const outputDir = path.join(projectRoot, 'output', 'web-scans');

    // Create output directory if it doesn't exist
    await mkdir(outputDir, { recursive: true });

    // Build command
    let command: string;
    const outputPath = path.join(outputDir, scanId);

    // Create output directory
    await mkdir(outputPath, { recursive: true });

    if (analysisType === 'js_only' && jsPath) {
      command = `cd /d "${projectRoot}" && python main.py analyze "${jsPath}" --base-url "${targetUrl}"`;
    } else if (analysisType === 'full_scan') {
      const jsPathArg = jsPath ? `--js-path "${jsPath}"` : '';
      const scanVulnsArg = scanVulns ? '--scan-vulns' : '--no-scan-vulns';
      command = `cd /d "${projectRoot}" && python main.py full-scan "${targetUrl}" ${jsPathArg} ${scanVulnsArg} --output "${outputPath}"`;
    } else {
      throw new Error('Invalid analysis type');
    }

    // Update progress
    scanResults.set(scanId, {
      scan_id: scanId,
      status: 'running',
      progress: 30,
      message: 'Executing scanner...'
    });

    // Execute Python scanner with UTF-8 encoding
    console.log(`Executing command: ${command}`);
    const { stdout, stderr } = await execAsync(command, {
      maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      timeout: 300000, // 5 minutes timeout
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8',
        PYTHONUTF8: '1'
      }
    });

    console.log(`Command stdout: ${stdout}`);
    if (stderr) console.log(`Command stderr: ${stderr}`);

    // Update progress
    scanResults.set(scanId, {
      scan_id: scanId,
      status: 'running',
      progress: 80,
      message: 'Processing results...'
    });

    // Read the generated JSON report
    console.log(`Reading output directory: ${outputPath}`);
    const files = await fs.readdir(outputPath);
    console.log(`Files in output directory: ${files.join(', ')}`);
    const jsonFile = files.find((f: string) => f.endsWith('.json'));

    if (!jsonFile) {
      console.error(`No JSON file found. Available files: ${files.join(', ')}`);
      throw new Error('No JSON report generated');
    }

    const jsonPath = path.join(outputPath, jsonFile);
    console.log(`Reading JSON file: ${jsonPath}`);
    const resultData = await fs.readFile(jsonPath, 'utf-8');
    const scanResult = JSON.parse(resultData);
    console.log(`Scan result parsed successfully. Endpoints: ${scanResult.endpoints?.length || 0}, Vulnerabilities: ${scanResult.vulnerabilities?.length || 0}`);

    // Update final status
    scanResults.set(scanId, {
      scan_id: scanId,
      status: 'completed',
      progress: 100,
      message: 'Scan completed successfully',
      result: scanResult,
      output_path: outputPath
    });

  } catch (error) {
    console.error(`Scan ${scanId} failed:`, error);
    const errorMessage = error instanceof Error ? error.message : 'Scan failed';
    const errorDetails = error instanceof Error ? error.stack : 'Unknown error';

    console.error(`Error message: ${errorMessage}`);
    console.error(`Error details: ${errorDetails}`);

    scanResults.set(scanId, {
      scan_id: scanId,
      status: 'failed',
      progress: 0,
      message: errorMessage,
      error: errorDetails
    });
  }
}

export async function GET(request: NextRequest) {
  try {
    // List all scans
    const scans = Array.from(scanResults.values()).map(scan => ({
      scan_id: scan.scan_id,
      status: scan.status,
      progress: scan.progress,
      message: scan.message,
      has_result: !!scan.result
    }));

    return NextResponse.json({ scans });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to list scans' },
      { status: 500 }
    );
  }
}
