import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createOrderAction } from '../actions/orders';
import { Order } from '@/domain/models';
import { queryKeys } from '../keys/queryKeys';

export function useCheckout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (orderData: Partial<Order>) => {
      // Using the Server Action
      const result = await createOrderAction(orderData);
      
      if (!result.success) {
        throw new Error(result.error);
      }
      return result.data;
    },
    onSuccess: () => {
      // Invalidate relevant queries after successful checkout
      queryClient.invalidateQueries({ queryKey: queryKeys.orders.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.games.all });
    },
  });
}
