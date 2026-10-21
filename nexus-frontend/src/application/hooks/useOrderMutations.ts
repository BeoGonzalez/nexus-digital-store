import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchClient } from '@/infrastructure/api/fetchClient';
import { PaymentMethod, CreatePaymentMethodPayload, OrderPayload } from '@/domain/models';

export const orderKeys = {
  paymentMethods: (userId: string) => ['paymentMethods', userId] as const,
  orders: (userId: string) => ['orders', userId] as const,
};

export const usePaymentMethodsQuery = (token: string | null) => {
  return useQuery({
    // Utilizamos el token como parte del contexto, si no hay token no cargamos
    queryKey: orderKeys.paymentMethods('me'),
    queryFn: async () => {
      if (!token) return [];
      return await fetchClient<PaymentMethod[]>('/api/v1/orders/payment-methods');
    },
    enabled: !!token,
  });
};

export const useAddPaymentMethodMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreatePaymentMethodPayload) => {
      return await fetchClient<PaymentMethod>('/api/v1/orders/payment-methods', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: orderKeys.paymentMethods('me') });
    }
  });
};

export const useCreateOrderMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: OrderPayload) => {
      const idempotencyKey = crypto.randomUUID();
      return await fetchClient('/api/v1/orders', {
        method: 'POST',
        headers: {
          'Idempotency-Key': idempotencyKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      // Si hubiera un hook para el historial de órdenes, lo invalidaríamos aquí
      queryClient.invalidateQueries({ queryKey: orderKeys.orders('me') });
    }
  });
};
