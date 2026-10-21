import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchClient } from '@/infrastructure/api/fetchClient';
import { gameKeys } from '@/application/keys/gameKeys';
import { VideoGame } from '@/domain/models';

/**
 * Hook para obtener la lista del catálogo (Queries)
 */
export const useVideoGamesQuery = () => {
  return useQuery({
    queryKey: gameKeys.lists(),
    queryFn: async () => {
      return await fetchClient<VideoGame[]>('/api/v1/video-games');
    },
  });
};

/**
 * Ejemplo de Hook para Mutaciones optimistas (Mutations)
 * Esto puede utilizarse en el admin para borrar un juego sin esperar a la BD
 */
export const useDeleteGameMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (gameId: string) => {
      // Importante: No retornamos el json de DELETE ya que devuelve 204 No Content usualmente, 
      // si tu backend devuelve JSON quita el ignore de TS
      const token = localStorage.getItem('nexus_token');
      await fetchClient(`/api/v1/video-games/${gameId}`, { 
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    },
    // Optimistic Update
    onMutate: async (deletedGameId) => {
      // Cancelamos queries activas para no sobrescribir nuestro update optimista
      await queryClient.cancelQueries({ queryKey: gameKeys.lists() });

      // Guardamos la lista vieja para rollback
      const previousGames = queryClient.getQueryData<VideoGame[]>(gameKeys.lists());

      // Mutamos la caché quitando el juego instantáneamente (UX súper rápida)
      if (previousGames) {
        queryClient.setQueryData<VideoGame[]>(
          gameKeys.lists(),
          previousGames.filter((game) => game.id !== deletedGameId)
        );
      }

      return { previousGames };
    },
    // En caso de error de red o backend, hacemos rollback a la caché guardada
    onError: (err, deletedGameId, context) => {
      if (context?.previousGames) {
        queryClient.setQueryData(gameKeys.lists(), context.previousGames);
      }
    },
    // Independientemente del resultado, invalidamos la caché para que re-descargue datos limpios (Eventual Consistency)
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: gameKeys.lists() });
    },
  });
};
