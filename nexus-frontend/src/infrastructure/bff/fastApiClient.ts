import 'server-only';
import { cookies } from 'next/headers';

export class ApiError extends Error {
  public status: number;
  public data?: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

interface FetchOptions extends RequestInit {
  requireAuth?: boolean;
}

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || 'http://localhost:8000/api/v1';

export const fastApiClient = {
  async fetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { requireAuth = false, headers: customHeaders, ...restOptions } = options;
    
    const headers = new Headers(customHeaders);
    headers.set('Content-Type', 'application/json');

    if (requireAuth) {
      const cookieStore = await cookies();
      const token = cookieStore.get('token')?.value;
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      } else {
        throw new ApiError(401, 'Unauthorized: No token provided');
      }
    }

    const url = `${FASTAPI_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      ...restOptions,
      headers,
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (err) {
        errorData = { message: response.statusText };
      }
      throw new ApiError(response.status, errorData?.detail || 'API request failed', errorData);
    }

    // In case of 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  },

  async get<T>(endpoint: string, options?: FetchOptions) {
    return this.fetch<T>(endpoint, { ...options, method: 'GET' });
  },

  async post<T>(endpoint: string, data?: any, options?: FetchOptions) {
    return this.fetch<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async put<T>(endpoint: string, data?: any, options?: FetchOptions) {
    return this.fetch<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async delete<T>(endpoint: string, options?: FetchOptions) {
    return this.fetch<T>(endpoint, { ...options, method: 'DELETE' });
  }
};
