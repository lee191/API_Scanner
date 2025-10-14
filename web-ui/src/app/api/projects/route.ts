import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:5001';

export async function GET(request: NextRequest) {
  try {
    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/projects`);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Get projects error:', error);
    return NextResponse.json(
      { error: 'Failed to get projects', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/projects`, {
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
    console.error('Create project error:', error);
    return NextResponse.json(
      { error: 'Failed to create project', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
