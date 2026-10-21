"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // Patrón Singleton in-component:
  // Inicializamos QueryClient de forma perezosa para evitar que se comparta
  // la misma instancia entre diferentes usuarios o peticiones (SSR)
  // y a la vez evitamos que se recree en cada render del Client Component.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000, // 5 Minutos: Evita requests innecesarias si la data no es vieja
            gcTime: 10 * 60 * 1000,   // 10 Minutos: Garbage Collector remueve la data de memoria si no se usa
            retry: 1,                 // Si falla, reintenta 1 vez antes de arrojar el error
            refetchOnWindowFocus: false, // Previene refresco agresivo al cambiar de pestaña
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
