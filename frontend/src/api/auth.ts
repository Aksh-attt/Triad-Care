import apiClient from './client';
import type { User, ProfileMembership } from '../types';

export interface LoginResponse {
  user: User;
  memberships: ProfileMembership[];
  profile_id?: number;
}

export const getDemoUsers = async (): Promise<User[]> => {
  const { data } = await apiClient.get('/api/auth/demo-users');
  return data;
};

export const login = async (passcode: string): Promise<LoginResponse> => {
  const { data } = await apiClient.post('/api/auth/login', { passcode });
  return data;
};

