import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchClient, ApiError } from '@/infrastructure/api/fetchClient';
import { orderKeys } from './useOrderMutations';

export const useLoginMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: Record<string, string>) => {
      // Neon Auth Login
      return await fetchClient<{ token: string }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: (data) => {
      localStorage.setItem('nexus_token', data.token);
      // Forzar recarga de queries dependientes de auth
      queryClient.invalidateQueries({ queryKey: orderKeys.paymentMethods('me') });
    }
  });
};

export const useRegisterMutation = () => {
  return useMutation({
    mutationFn: async (data: Record<string, string>) => {
      // Neon Auth Register
      return await fetchClient('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    }
  });
};
