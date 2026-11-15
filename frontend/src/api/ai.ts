import apiClient from './client';

export const scanPrescription = async (file: File) => {
  const formData = new FormData();
  formData.append('image_file', file);
  formData.append('file', file);
  const { data } = await apiClient.post('/api/ai/scan-prescription', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getWeeklySummary = async (profileId: number) => {
  const { data } = await apiClient.post(`/api/ai/weekly-summary/${profileId}`);
  return data;
};

export const comparePrescription = async (profileId: number, extractedItems: unknown[]) => {
  const { data } = await apiClient.post('/api/ai/compare-prescription', {
    profile_id: profileId,
    extracted_items: extractedItems,
  });
  return data;
};

