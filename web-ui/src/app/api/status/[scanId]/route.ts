import { NextRequest, NextResponse } from 'next/server';
import { scanResults } from '@/lib/scanStore';

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ scanId: string }> }
) {
  try {
    const params = await context.params;
    const { scanId } = params;

    if (!scanId) {
      return NextResponse.json(
        { error: 'scan_id is required' },
        { status: 400 }
      );
    }

    console.log(`Checking status for scan ID: ${scanId}`);
    console.log(`Available scan IDs: ${Array.from(scanResults.keys()).join(', ')}`);

    const scanStatus = scanResults.get(scanId);

    if (!scanStatus) {
      return NextResponse.json(
        { error: 'Scan not found', scan_id: scanId },
        { status: 404 }
      );
    }

    return NextResponse.json(scanStatus);
  } catch (error) {
    console.error('Status check error:', error);
    return NextResponse.json(
      { error: 'Failed to get scan status', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
