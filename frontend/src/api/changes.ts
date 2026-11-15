import apiClient from './client';
import type { MedicationChangeRequest } from '../types';

export const getChangeRequests = async (profileId: number): Promise<MedicationChangeRequest[]> => {
  const { data } = await apiClient.get(`/api/changes/${profileId}`);
  return data;
};

export const createChangeRequest = async (
  profileId: number,
  request: {
    requested_by_user_id: number;
    medication_id?: number;
    change_type: string;
    proposed_details: Record<string, unknown>;
    reason: string;
  }
): Promise<MedicationChangeRequest> => {
  const { data } = await apiClient.post(`/api/changes/${profileId}`, request);
  return data;
};

export const reviewChangeRequest = async (
  requestId: number,
  status: 'approved' | 'rejected',
  reviewedBy: number
): Promise<MedicationChangeRequest> => {
  const { data } = await apiClient.put(`/api/changes/${requestId}/review`, {
    status,
    reviewed_by_user_id: reviewedBy,
  });
  return data;
};
