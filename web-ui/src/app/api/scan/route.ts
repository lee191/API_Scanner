import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:5001';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Scan error:', error);
    return NextResponse.json(
      { error: 'Failed to start scan', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    // Forward request to Python Flask server for scan history
    const response = await fetch(`${PYTHON_API_URL}/api/history`);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Get scans error:', error);
    return NextResponse.json(
      { error: 'Failed to get scans' },
      { status: 500 }
    );
  }
}
