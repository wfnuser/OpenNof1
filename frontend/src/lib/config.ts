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
// This now checks the backend configuration instead of environment variable
let cachedControlAllowed: boolean | null = null;

export async function isControlOperationsAllowed(): Promise<boolean> {
  // If already cached, return cached value
  if (cachedControlAllowed !== null) {
    return cachedControlAllowed;
  }

  try {
    // Try to fetch from backend config API
    const response = await fetch(`${getApiBaseUrl()}/config`);
    if (response.ok) {
      const config = await response.json();
      cachedControlAllowed = config.system?.allow_control_operations === true;
      return cachedControlAllowed;
    }
  } catch (error) {
    console.warn('Failed to fetch control operations config from backend, falling back to environment variable');
  }

  // Fallback to environment variable for backward compatibility
  // Default to false if not explicitly set
  cachedControlAllowed = process.env.ALLOW_CONTROL_OPERATIONS !== 'false';
  return cachedControlAllowed;
}

// Synchronous version for middleware (uses environment variable as fallback)
// Only blocks if explicitly set to 'false', otherwise allows backend to decide
export function isControlOperationsAllowedSync(): boolean {
  // Only block if explicitly disabled
  return process.env.ALLOW_CONTROL_OPERATIONS !== 'false';
}
