import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:5001';

export async function GET(
  request: NextRequest,
  { params }: { params: { project_id: string } }
) {
  try {
    const { project_id } = params;

    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/projects/${project_id}`);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Get project error:', error);
    return NextResponse.json(
      { error: 'Failed to get project', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { project_id: string } }
) {
  try {
    const { project_id } = params;

    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/projects/${project_id}`, {
      method: 'DELETE'
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Delete project error:', error);
    return NextResponse.json(
      { error: 'Failed to delete project', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { project_id: string } }
) {
  try {
    const { project_id } = params;
    const body = await request.json();

    // Forward request to Python Flask server
    const response = await fetch(`${PYTHON_API_URL}/api/projects/${project_id}`, {
      method: 'PUT',
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
    console.error('Update project error:', error);
    return NextResponse.json(
      { error: 'Failed to update project', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
