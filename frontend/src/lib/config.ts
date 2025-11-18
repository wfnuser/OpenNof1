// Frontend configuration with environment variable support

export interface ApiConfig {
  useProxy: boolean;
  backendUrl: string;
  apiBaseUrl: string;
}

// Environment-driven configuration
export const apiConfig: ApiConfig = {
  // Use proxy by default, can be disabled for direct backend access
  useProxy: process.env.USE_API_PROXY !== 'false',
  
  // Backend URL (server-side only, not exposed to client)
  backendUrl: process.env.API_BASE_URL || 'http://localhost:8000/api/v1',
  
  // API base URL - switches between proxy and direct based on useProxy
  apiBaseUrl: process.env.USE_API_PROXY !== 'false' 
    ? '/api'  // Use Next.js API routes (proxy)
    : (process.env.NEXT_PUBLIC_DIRECT_API_URL || 'http://localhost:8000/api/v1') // Direct backend
};

// Runtime configuration check
export function getApiBaseUrl(): string {
  // In production (Vercel), always use proxy for security
  if (process.env.NODE_ENV === 'production') {
    return '/api';
  }
  
  // In development, respect the configuration
  return apiConfig.apiBaseUrl;
}

export function shouldUseProxy(): boolean {
  // Always use proxy in production
  if (process.env.NODE_ENV === 'production') {
    return true;
  }
  
  return apiConfig.useProxy;
}

// Check if control operations (bot start/stop, strategy modification) are allowed
export function isControlOperationsAllowed(): boolean {
  return process.env.ALLOW_CONTROL_OPERATIONS === 'true';
}
