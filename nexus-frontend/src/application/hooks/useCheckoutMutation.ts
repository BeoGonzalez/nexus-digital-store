import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchClient } from '@/infrastructure/api/fetchClient';
import { CreateOrderDTO, OrderResponse } from '@/domain/models/order';

export const useCheckoutMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<OrderResponse, Error, CreateOrderDTO>({
    mutationFn: async (data: CreateOrderDTO) => {
      // Generación automática de Idempotency-Key para cada intento de checkout
      const idempotencyKey = crypto.randomUUID();
      
      return await fetchClient<OrderResponse>('/api/v1/orders', {
        method: 'POST',
        headers: {
          'Idempotency-Key': idempotencyKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      // Invalidar carrito si existiera la query (ej: ['cart'])
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      // Invalidar historial de órdenes
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};
