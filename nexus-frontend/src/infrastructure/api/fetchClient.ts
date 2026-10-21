import { ApiErrorDetail } from "@/domain/models";

export class ApiError extends Error {
  public status: number;
  public statusText: string;
  public data: any;

  constructor(status: number, statusText: string, data: any) {
    // Normalizar mensaje de error de FastAPI
    const message = typeof data?.detail === 'string' 
      ? data.detail 
      : Array.isArray(data?.detail)
        ? data.detail.map((err: ApiErrorDetail) => err.msg).join(', ')
        : statusText || "Unknown API Error";

    super(message);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

export const fetchClient = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const url = `${baseURL}${endpoint}`;
  
  // Recuperar el token desde localStorage (idealmente desde cookies para SSR, pero por ahora en client)
  const token = typeof window !== 'undefined' ? localStorage.getItem('nexus_token') : null;

  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Si la respuesta no es OK (2xx), lanzamos la clase personalizada de Error
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    throw new ApiError(response.status, response.statusText, errorData);
  }

  // Parseo de JSON exitoso
  return response.json() as Promise<T>;
};
