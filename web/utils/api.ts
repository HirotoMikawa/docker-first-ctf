/**
 * API Client Utility (Ver 10.2)
 * 
 * Centralized API client configuration for dynamic endpoint management.
 * Uses NEXT_PUBLIC_API_URL environment variable for server IP-based deployment.
 */

/**
 * Get the base API URL from environment variable
 * @throws {Error} If NEXT_PUBLIC_API_URL is not set
 */
export function getApiUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  
  if (!apiUrl) {
    throw new Error('NEXT_PUBLIC_API_URL environment variable is not set. Please configure it in your environment variables or .env.local file.');
  }
  
  // Remove trailing slash if present
  return apiUrl.replace(/\/$/, '');
}

/**
 * Build a full API endpoint URL
 * @param endpoint - API endpoint path (e.g., '/api/challenges')
 * @returns Full URL string
 */
export function buildApiUrl(endpoint: string): string {
  const baseUrl = getApiUrl();
  // Ensure endpoint starts with /
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${normalizedEndpoint}`;
}

/**
 * Create fetch options with authentication header
 * @param sessionToken - Supabase session access token
 * @param options - Additional fetch options
 * @returns Fetch options object
 */
export function createAuthenticatedFetchOptions(
  sessionToken: string,
  options: RequestInit = {}
): RequestInit {
  return {
    ...options,
    headers: {
      'Authorization': `Bearer ${sessionToken}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };
}

/**
 * Fetch API wrapper with error handling
 * @param endpoint - API endpoint path
 * @param sessionToken - Supabase session access token
 * @param options - Additional fetch options
 * @returns Promise<Response>
 */
export async function apiFetch(
  endpoint: string,
  sessionToken: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = buildApiUrl(endpoint);
  const fetchOptions = createAuthenticatedFetchOptions(sessionToken, {
    ...options,
    method: options.method || 'GET',
  });
  
  return fetch(url, fetchOptions);
}

