export const queryKeys = {
  games: {
    all: ['games'] as const,
    lists: () => [...queryKeys.games.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.games.lists(), { filters }] as const,
    details: () => [...queryKeys.games.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.games.details(), id] as const,
  },
  orders: {
    all: ['orders'] as const,
    lists: () => [...queryKeys.orders.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.orders.lists(), { filters }] as const,
    details: () => [...queryKeys.orders.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.orders.details(), id] as const,
  },
  paymentMethods: {
    all: ['paymentMethods'] as const,
    lists: () => [...queryKeys.paymentMethods.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.paymentMethods.lists(), { filters }] as const,
  },
  auth: {
    all: ['auth'] as const,
    me: () => [...queryKeys.auth.all, 'me'] as const,
    info: () => [...queryKeys.auth.all, 'info'] as const,
  },
  health: {
    all: ['health'] as const,
    status: () => [...queryKeys.health.all, 'status'] as const,
  },
} as const;
