// utils/tokenRefresh.ts
import api from './api';

/**
 * Attempts to refresh the authentication token.
 * @returns Promise<boolean> - true if refresh is successful, otherwise false
 */
export const refreshToken = async (): Promise<boolean> => {
  try {
    await api.post('/api/users/token/refresh-cookie/');
    return true;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return false;
  }
};

/**
 * Checks if a JWT token is expired.
 * @param token string | null | undefined - the JWT token
 * @returns boolean - true if expired or invalid, false if still valid
 */
export const isTokenExpired = (token: string | null | undefined): boolean => {
  if (!token) return true;

  try {
    // Extract payload from token
    const base64Payload = token.split('.')[1];
    const payload = JSON.parse(atob(base64Payload)) as { exp: number };

    const exp = payload.exp * 1000; // Convert to milliseconds
    return Date.now() >= exp;
  } catch (error) {
    console.error('Error checking token expiration:', error);
    return true;
  }
};
