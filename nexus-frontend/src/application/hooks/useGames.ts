import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../keys/queryKeys';
import { VideoGame } from '@/domain/models';

export function useGames(filters: string = '') {
  return useQuery<VideoGame[]>({
    queryKey: queryKeys.games.list(filters),
    queryFn: async () => {
      const response = await fetch(`/api/games${filters ? `?${filters}` : ''}`);
      if (!response.ok) {
        throw new Error('Failed to fetch games');
      }
      return response.json();
    },
  });
}

export function useGameDetails(id: string) {
  return useQuery<VideoGame>({
    queryKey: queryKeys.games.detail(id),
    queryFn: async () => {
      // In this architecture, assuming we can get the specific game via proxy as well,
      // or we can just fetch from `/api/games` and filter if there's no specific route.
      // But standard REST dictates an ID route. Let's assume we have it or will add it to proxy.
      // If we don't have a specific proxy route for details, we fetch from BFF.
      const response = await fetch(`/api/games/${id}`); // Assuming this exists or can be added
      if (!response.ok) {
        throw new Error('Failed to fetch game details');
      }
      return response.json();
    },
    enabled: !!id,
  });
}
