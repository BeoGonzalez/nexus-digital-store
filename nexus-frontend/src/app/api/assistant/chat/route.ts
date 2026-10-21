import { NextResponse } from 'next/server';

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || 'http://localhost:8000/api/v1';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // We don't use fastApiClient here because we want to proxy the stream directly
    const response = await fetch(`${FASTAPI_BASE_URL}/assistant/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    if (!response.body) {
      return NextResponse.json(
        { error: 'No stream received from backend' },
        { status: 500 }
      );
    }

    // Proxy the ReadableStream directly to the client without buffering
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
      },
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Internal server error while streaming' },
      { status: 500 }
    );
  }
}
