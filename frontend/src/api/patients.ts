import apiClient from './client';
import type { PatientProfile } from '../types';

export const getPatient = async (profileId: number): Promise<PatientProfile> => {
  const { data } = await apiClient.get(`/api/patients/${profileId}`);
  return data;
};

export const updatePatient = async (profileId: number, updates: Partial<PatientProfile>): Promise<PatientProfile> => {
  const { data } = await apiClient.put(`/api/patients/${profileId}`, updates);
  return data;
};
