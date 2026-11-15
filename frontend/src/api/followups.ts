import apiClient from './client';
import type { CaregiverFollowup, FollowupAction } from '../types';

export const getFollowups = async (profileId: number): Promise<CaregiverFollowup[]> => {
  const { data } = await apiClient.get(`/api/followups/${profileId}`);
  return data;
};

export const claimFollowup = async (
  doseId: number,
  caregiverId: number,
  action: FollowupAction
): Promise<CaregiverFollowup> => {
  const { data } = await apiClient.post(`/api/followups/claim`, {
    dose_schedule_id: doseId,
    caregiver_id: caregiverId,
    action,
  });
  return data;
};

export const updateFollowup = async (
  followupId: number,
  updates: { status?: string; notes?: string; action?: FollowupAction }
): Promise<CaregiverFollowup> => {
  const { data } = await apiClient.put(`/api/followups/${followupId}`, updates);
  return data;
};
