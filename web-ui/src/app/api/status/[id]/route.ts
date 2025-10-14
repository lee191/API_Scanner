import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:5001';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id;

    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/status/${id}`);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Get status error:', error);
    return NextResponse.json(
      { error: 'Failed to get scan status', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
