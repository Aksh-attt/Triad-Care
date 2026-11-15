import apiClient, { setAccessToken, setCsrfToken } from './client';
import type { User, ProfileMembership } from '../types';

export interface LoginResponse {
  user: User;
  memberships: ProfileMembership[];
  profile_id?: number;
  access_token?: string;
  csrf_token?: string;
}

export const getDemoUsers = async (): Promise<User[]> => {
  const { data } = await apiClient.get('/api/auth/demo-users');
  return data;
};

export const login = async (passcode: string): Promise<LoginResponse> => {
  const { data } = await apiClient.post('/api/auth/login', { passcode });
  if (data.access_token) setAccessToken(data.access_token);
  if (data.csrf_token) setCsrfToken(data.csrf_token);
  return data;
};

export const demoLogin = async (role: string): Promise<LoginResponse> => {
  const { data } = await apiClient.post('/api/auth/demo-login', { role });
  if (data.access_token) setAccessToken(data.access_token);
  if (data.csrf_token) setCsrfToken(data.csrf_token);
  return data;
};

export const refreshSession = async (): Promise<LoginResponse> => {
  const { data } = await apiClient.post('/api/auth/refresh');
  if (data.access_token) setAccessToken(data.access_token);
  if (data.csrf_token) setCsrfToken(data.csrf_token);
  return data;
};

export const bootstrapCsrf = async (): Promise<string> => {
  const { data } = await apiClient.get('/api/auth/csrf-bootstrap');
  if (data.csrf_token) setCsrfToken(data.csrf_token);
  return data.csrf_token;
};

export const logoutApi = async (): Promise<void> => {
  try {
    await apiClient.post('/api/auth/logout');
  } finally {
    setAccessToken(null);
    setCsrfToken(null);
  }
};

export const getMe = async (): Promise<LoginResponse> => {
  const { data } = await apiClient.get('/api/auth/me');
  return data;
};
