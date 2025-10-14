import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:5001';

export async function POST(
  request: NextRequest,
  { params }: { params: { scan_id: string } }
) {
  try {
    const { scan_id } = params;

    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/scan/${scan_id}/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Stop scan error:', error);
    return NextResponse.json(
      { error: 'Failed to stop scan', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
