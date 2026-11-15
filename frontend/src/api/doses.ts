import apiClient from './client';
import type { DoseSchedule } from '../types';

export const getTodayDoses = async (profileId: number): Promise<DoseSchedule[]> => {
  const { data } = await apiClient.get(`/api/doses/${profileId}/today`);
  return data;
};

export const confirmDose = async (doseId: number, confirmedByUserId: number): Promise<DoseSchedule> => {
  const { data } = await apiClient.post(`/api/doses/${doseId}/confirm`, {
    confirmed_by_user_id: confirmedByUserId,
  });
  return data;
};

export const recordDoseReason = async (
  doseId: number,
  reason: string,
  notes: string,
  confirmedByUserId: number
): Promise<DoseSchedule> => {
  const { data } = await apiClient.post(`/api/doses/${doseId}/reason`, {
    reason,
    notes,
    confirmed_by_user_id: confirmedByUserId,
  });
  return data;
};

export const getDoseHistory = async (profileId: number): Promise<DoseSchedule[]> => {
  const { data } = await apiClient.get(`/api/doses/${profileId}/history`);
  return data;
};
