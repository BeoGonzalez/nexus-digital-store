import { NextResponse } from 'next/server';
import { fastApiClient } from '@/infrastructure/bff/fastApiClient';
import { VideoGame } from '@/domain/models';

export const revalidate = 60; // Cache these requests for 60 seconds by default

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const queryString = searchParams.toString();
    const endpoint = `/video-games${queryString ? `?${queryString}` : ''}`;

    const games = await fastApiClient.get<VideoGame[]>(endpoint, {
      next: { tags: ['catalog'] } // Next.js fetch options for revalidation
    });

    return NextResponse.json(games);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch games' },
      { status: error.status || 500 }
    );
  }
}
