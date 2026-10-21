'use server';

import { fastApiClient } from '@/infrastructure/bff/fastApiClient';
import { VideoGame } from '@/domain/models';
import { updateTag } from 'next/cache';

export async function createGameAction(gameData: Partial<VideoGame>) {
  try {
    const newGame = await fastApiClient.post<VideoGame>('/video-games', gameData, { requireAuth: true });
    updateTag('catalog');
    return { success: true, data: newGame };
  } catch (error: any) {
    console.error('Failed to create game:', error);
    return { success: false, error: error.message || 'Failed to create game' };
  }
}

export async function updateGameAction(id: string, gameData: Partial<VideoGame>) {
  try {
    const updatedGame = await fastApiClient.put<VideoGame>(`/video-games/${id}`, gameData, { requireAuth: true });
    updateTag('catalog');
    return { success: true, data: updatedGame };
  } catch (error: any) {
    console.error('Failed to update game:', error);
    return { success: false, error: error.message || 'Failed to update game' };
  }
}

export async function deleteGameAction(id: string) {
  try {
    await fastApiClient.delete(`/video-games/${id}`, { requireAuth: true });
    updateTag('catalog');
    return { success: true };
  } catch (error: any) {
    console.error('Failed to delete game:', error);
    return { success: false, error: error.message || 'Failed to delete game' };
  }
}

