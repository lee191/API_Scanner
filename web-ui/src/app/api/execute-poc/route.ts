import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFile, unlink } from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { poc_code, timeout = 30000 } = body;

    if (!poc_code) {
      return NextResponse.json(
        { error: 'poc_code is required' },
        { status: 400 }
      );
    }

    // Generate temporary Python file
    const tempId = uuidv4();
    const tempFile = path.join(process.cwd(), '..', 'temp', `poc_${tempId}.py`);

    try {
      // Write PoC code to temporary file
      await writeFile(tempFile, poc_code, 'utf-8');

      // Execute Python script with timeout
      const { stdout, stderr } = await execAsync(`python "${tempFile}"`, {
        timeout,
        maxBuffer: 1024 * 1024 * 5, // 5MB buffer
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
          PYTHONUTF8: '1'
        }
      });

      // Clean up temp file
      try {
        await unlink(tempFile);
      } catch (e) {
        // Ignore cleanup errors
      }

      return NextResponse.json({
        success: true,
        stdout: stdout || '',
        stderr: stderr || '',
        exit_code: 0
      });

    } catch (error: any) {
      // Clean up temp file on error
      try {
        await unlink(tempFile);
      } catch (e) {
        // Ignore cleanup errors
      }

      // Check if it's a timeout error
      if (error.killed && error.signal === 'SIGTERM') {
        return NextResponse.json({
          success: false,
          error: 'Execution timeout',
          stdout: error.stdout || '',
          stderr: error.stderr || '',
          exit_code: -1
        }, { status: 408 });
      }

      // Other execution errors
      return NextResponse.json({
        success: false,
        error: error.message || 'Execution failed',
        stdout: error.stdout || '',
        stderr: error.stderr || '',
        exit_code: error.code || 1
      }, { status: 200 }); // Return 200 but with success: false
    }

  } catch (error: any) {
    console.error('Execute PoC error:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to execute PoC',
        details: error.message
      },
      { status: 500 }
    );
  }
}
