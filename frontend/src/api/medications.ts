import apiClient from './client';
import type { Medication } from '../types';

export const getMedications = async (profileId: number): Promise<Medication[]> => {
  const { data } = await apiClient.get(`/api/medications/${profileId}`);
  return data;
};

export const addMedication = async (profileId: number, medication: Partial<Medication>): Promise<Medication> => {
  const { data } = await apiClient.post(`/api/medications/${profileId}`, medication);
  return data;
};

export const updateMedication = async (medicationId: number, updates: Partial<Medication>): Promise<Medication> => {
  const { data } = await apiClient.put(`/api/medications/${medicationId}`, updates);
  return data;
};

export const deleteMedication = async (medicationId: number): Promise<void> => {
  await apiClient.delete(`/api/medications/${medicationId}`);
};

export const getTodaySchedule = async (profileId: number) => {
  const { data } = await apiClient.get(`/api/medications/${profileId}/schedule/today`);
  return data;
};
